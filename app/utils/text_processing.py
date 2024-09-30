import logging
import re
from threading import Lock
import cv2
import pytesseract
from googletrans import Translator
from langdetect import detect
import spacy
from spacy.cli import download
from summa import keywords, summarizer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# List of all available spaCy models
SPACY_MODELS = [
    "en_core_web_sm", "fr_core_news_sm", "es_core_news_sm", "de_core_news_sm",
    "zh_core_web_sm", "nl_core_news_sm", "el_core_news_sm", "it_core_news_sm",
    "ja_core_news_sm", "lt_core_news_sm", "nb_core_news_sm", "pl_core_news_sm",
    "pt_core_news_sm", "ro_core_news_sm", "ru_core_news_sm"
]

# Load spaCy models for different languages
nlp_en = spacy.load("en_core_web_sm")
nlp_fr = spacy.load("fr_core_news_sm")
nlp_es = spacy.load("es_core_news_sm")
nlp_de = spacy.load("de_core_news_sm")

# Dictionary to store loaded models
nlp_models = {}
model_locks = {model: Lock() for model in SPACY_MODELS}

def ocr_from_video(video_path):
    video = cv2.VideoCapture(video_path)
    fps = video.get(cv2.CAP_PROP_FPS)
    ocr_text = ""
    frame_count = 0

    while video.isOpened():
        ret, frame = video.read()
        if not ret:
            break

        if frame_count % (5 * int(fps)) == 0:  # Process every 5 seconds
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            ocr_text += pytesseract.image_to_string(gray) + " "

        frame_count += 1

    video.release()
    return ocr_text.strip()

def translate_text(text, target_language='en'):
    translator = Translator()
    return translator.translate(text, dest=target_language).text

def load_spacy_model(model_name):
    with model_locks[model_name]:
        if model_name not in nlp_models:
            try:
                nlp_models[model_name] = spacy.load(model_name)
                print(f"Loaded model: {model_name}")
            except OSError:
                print(f"Downloading model: {model_name}")
                download(model_name)
                nlp_models[model_name] = spacy.load(model_name)
    return nlp_models[model_name]


def get_nlp_model(lang):
    # Map detected language to spaCy model
    lang_to_model = {
        'en': 'en_core_web_sm',
        'fr': 'fr_core_news_sm',
        'es': 'es_core_news_sm',
        'de': 'de_core_news_sm',
        'zh': 'zh_core_web_sm',
        'nl': 'nl_core_news_sm',
        'el': 'el_core_news_sm',
        'it': 'it_core_news_sm',
        'ja': 'ja_core_news_sm',
        'lt': 'lt_core_news_sm',
        'nb': 'nb_core_news_sm',
        'pl': 'pl_core_news_sm',
        'pt': 'pt_core_news_sm',
        'ro': 'ro_core_news_sm',
        'ru': 'ru_core_news_sm'
    }
    
    model_name = lang_to_model.get(lang, 'en_core_web_sm')  # Default to English if language not found
    return load_spacy_model(model_name)

def is_sentence_meaningful(sentence):
    try:
        # Check if the sentence has a minimum length
        if len(sentence.split()) < 5:
            return False

        # Get the appropriate NLP model
        detected_lang = detect(sentence)
        nlp = get_nlp_model(detected_lang)

        # Check if the sentence contains at least one verb and one noun
        doc = nlp(sentence)
        has_verb = any(token.pos_ == "VERB" for token in doc)
        has_noun = any(token.pos_ == "NOUN" for token in doc)

        if not (has_verb and has_noun):
            return False

        # Check if the sentence contains too many special characters or numbers
        special_char_ratio = len(re.findall(r"[^a-zA-Z\s]", sentence)) / len(sentence)
        if special_char_ratio > 0.3:  # If more than 30% of characters are special
            return False

        return True
    except Exception as e:
        print(f"Warning: Error in is_sentence_meaningful. Error: {str(e)}")
        return False  # If there's an error, we'll consider the sentence not meaningful


def filter_important_sentences(sentences):
    filtered = []
    for sentence in sentences:
        try:
            if is_sentence_meaningful(sentence):
                filtered.append(sentence)
        except Exception as e:
            print(f"Warning: Error while filtering sentence. Error: {str(e)}")
    return filtered

def extract_meaningful_content(original_text, translated_text, target_language):
    try:
        # Combine original and translated text
        combined_text = f"{original_text}\n{translated_text}"

        # Detect language of the combined text
        detected_lang = detect(combined_text)
        nlp = get_nlp_model(detected_lang)

        # Process the text with spaCy
        doc = nlp(combined_text)

        # Extract named entities with error handling
        try:
            entities = [ent.text for ent in doc.ents]
        except AttributeError:
            print("Warning: Unable to extract entities. The spaCy model might not support entity recognition.")
            entities = []

        # Extract key phrases
        try:
            key_phrases = keywords.keywords(combined_text).split("\n")[:5]  # Top 5 key phrases
        except Exception as e:
            print(f"Warning: Unable to extract key phrases. Error: {str(e)}")
            key_phrases = []

        # Extract important sentences
        try:
            important_sentences = summarizer.summarize(
                combined_text, ratio=0.3
            )  # Extract 30% of the text as important sentences
            important_sentences = [
                sent.strip() for sent in important_sentences.split("\n") if sent.strip()
            ]
        except Exception as e:
            print(f"Warning: Unable to extract important sentences. Error: {str(e)}")
            important_sentences = []

        # Filter out nonsensical sentences
        filtered_sentences = filter_important_sentences(important_sentences)

        summary = {
            "entities": entities,
            "key_phrases": key_phrases,
            "important_sentences": filtered_sentences,
        }
        return summary
    except Exception as e:
        print(f"Error in extract_meaningful_content: {str(e)}")
        return {"error": f"Unable to extract meaningful content: {str(e)}"}
