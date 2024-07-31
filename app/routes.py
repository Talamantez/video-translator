import os
import logging
import json
import uuid
from flask import (
    Blueprint,
    Response,
    stream_with_context,
    render_template,
    request,
    jsonify,
    send_from_directory,
    current_app,
)
from app.utils.video_processing import download_video
from app.utils.audio_processing import extract_audio, speech_to_text
from app.utils.text_processing import ocr_from_video, translate_text
from app.utils.file_handling import allowed_file, get_video_duration
from app.utils.image_processing import recognize_images_in_video
from app.utils.fake_video_detection import detect_fake_video
from werkzeug.utils import secure_filename
from datetime import datetime
import spacy
from spacy.cli import download
from threading import Lock
from langdetect import detect
from summa import keywords, summarizer
import re
import subprocess


from fractions import Fraction

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')



# Load spaCy models for different languages
nlp_en = spacy.load("en_core_web_sm")
nlp_fr = spacy.load("fr_core_news_sm")
nlp_es = spacy.load("es_core_news_sm")
nlp_de = spacy.load("de_core_news_sm")

main = Blueprint("main", __name__)

# List of all available spaCy models
SPACY_MODELS = [
    "en_core_web_sm", "fr_core_news_sm", "es_core_news_sm", "de_core_news_sm",
    "zh_core_web_sm", "nl_core_news_sm", "el_core_news_sm", "it_core_news_sm",
    "ja_core_news_sm", "lt_core_news_sm", "nb_core_news_sm", "pl_core_news_sm",
    "pt_core_news_sm", "ro_core_news_sm", "ru_core_news_sm"
]

# Dictionary to store loaded models
nlp_models = {}
model_locks = {model: Lock() for model in SPACY_MODELS}

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

def perform_fake_video_detection(temp_file, output_folder):
    fake_detection_result = detect_fake_video(temp_file)
    with open(os.path.join(output_folder, "fake_detection_result.json"), "w") as f:
        json.dump(fake_detection_result, f)


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

def filter_important_sentences(sentences):
    filtered = []
    for sentence in sentences:
        try:
            if is_sentence_meaningful(sentence):
                filtered.append(sentence)
        except Exception as e:
            print(f"Warning: Error while filtering sentence. Error: {str(e)}")
    return filtered

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

def get_nlp_model(lang):
    if lang == "en":
        return nlp_en
    elif lang == "fr":
        return nlp_fr
    elif lang == "es":
        return nlp_es
    elif lang == "de":
        return nlp_de
    else:
        return nlp_en  # Default to English



@main.route("/")
def index():
    current_app.logger.debug(f"Current working directory: {os.getcwd()}")
    current_app.logger.debug(
        f"Does index.html exist: {os.path.exists('app/templates/index.html')}"
    )
    return render_template("index.html")


@main.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        duration = get_video_duration(filepath)
        return jsonify({"filename": filename, "duration": duration})
    return jsonify({"error": "File type not allowed"}), 400


@main.route("/upload_folder", methods=["POST"])
def upload_folder():
    if "files[]" not in request.files:
        return jsonify({"error": "No file part"}), 400

    files = request.files.getlist("files[]")
    if not files or files[0].filename == "":
        return jsonify({"error": "No selected files"}), 400

    folder_id = str(uuid.uuid4())
    folder_path = os.path.join(current_app.config["UPLOAD_FOLDER"], folder_id)
    os.makedirs(folder_path, exist_ok=True)

    uploaded_files = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(folder_path, filename)
            file.save(filepath)
            uploaded_files.append(filename)

    if not uploaded_files:
        return jsonify({"error": "No valid files uploaded"}), 400

    return jsonify({"folder_id": folder_id, "files": uploaded_files})


def generate_clip_name(speech_text, ocr_text, image_recognition_results):
    # Combine all text
    all_text = f"{speech_text} {ocr_text}"

    # Extract key phrases
    key_phrases = keywords.keywords(all_text).split("\n")[:3]

    # Get top recognized object
    top_object = (
        image_recognition_results[0]["label"] if image_recognition_results else ""
    )

    # Combine information to create a name
    clip_name_parts = key_phrases + [top_object]
    clip_name = " ".join(clip_name_parts[:3])  # Limit to 3 parts

    return clip_name.capitalize() if clip_name else "Unnamed Clip"

def update_running_summary(current_summary, new_clip_data):
    if not current_summary:
        current_summary = {
            "key_topics": [],
            "main_entities": [],
            "recognized_objects": [],
            "important_sentences": [],
        }

    # Update key topics
    if "summary" in new_clip_data and "key_phrases" in new_clip_data["summary"]:
        current_summary["key_topics"].extend(new_clip_data["summary"]["key_phrases"])
        current_summary["key_topics"] = list(set(current_summary["key_topics"]))[:10]  # Keep top 10 unique topics

    # Update main entities
    if "summary" in new_clip_data and "entities" in new_clip_data["summary"]:
        current_summary["main_entities"].extend(new_clip_data["summary"]["entities"])
        current_summary["main_entities"] = list(set(current_summary["main_entities"]))[:10]  # Keep top 10 unique entities

    # Update recognized objects
    if "image_recognition" in new_clip_data:
        new_objects = [obj["label"] for obj in new_clip_data["image_recognition"][:3]]  # Top 3 objects from new clip
        current_summary["recognized_objects"].extend(new_objects)
        current_summary["recognized_objects"] = list(set(current_summary["recognized_objects"]))[:10]  # Keep top 10 unique objects

    # Update important sentences
    if "summary" in new_clip_data and "important_sentences" in new_clip_data["summary"]:
        new_sentences = new_clip_data["summary"].get("important_sentences", [])
        current_summary["important_sentences"].extend(new_sentences)
        current_summary["important_sentences"] = list(set(current_summary["important_sentences"]))[:20]  # Keep top 20 unique sentences

    return current_summary

def get_video_duration(filename):
    try:
        result = subprocess.run(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', filename],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        data = json.loads(result.stdout)
       
        # Try to get duration from format
        if 'format' in data and 'duration' in data['format']:
            return float(data['format']['duration'])
       
        # If not in format, try to get from streams
        if 'streams' in data:
            for stream in data['streams']:
                if 'duration' in stream:
                    return float(stream['duration'])
       
        # If we still can't find duration, try to calculate from frames
        if 'streams' in data:
            for stream in data['streams']:
                if stream.get('codec_type') == 'video':
                    if 'nb_frames' in stream and 'avg_frame_rate' in stream:
                        nb_frames = int(stream['nb_frames'])
                        fps = eval(stream['avg_frame_rate'])
                        if fps != 0:
                            return nb_frames / fps
       
        # If all else fails, return 0
        return 0
    except Exception as e:
        logging.error(f"Error getting video duration: {str(e)}")
        return 0

def split_video(input_file, output_folder, clip_duration=30):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    total_duration = get_video_duration(input_file)
    if total_duration == 0:
        logging.error(f"Could not determine duration of {input_file}")
        return []
    num_clips = int(total_duration // clip_duration) + 1
    clips = []
    for i in range(num_clips):
        start_time = i * clip_duration
        end_time = min((i + 1) * clip_duration, total_duration)
        output_file = os.path.join(output_folder, f"clip_{i+1:03d}.mp4")
       
        try:
            subprocess.run([
                'ffmpeg',
                '-i', input_file,
                '-ss', str(start_time),
                '-to', str(end_time),
                '-c', 'copy',
                '-y',
                output_file
            ], check=True, stderr=subprocess.PIPE)
            clips.append({
                'filename': f"clip_{i+1:03d}.mp4",
                'start': start_time,
                'end': end_time
            })
        except subprocess.CalledProcessError as e:
            logging.error(f"Error processing clip {i+1}: {e.stderr.decode()}")
    return clips

@main.route("/process_url", methods=["POST"])
def process_url():
    try:
        data = request.json
        url = data["url"]
        clip_duration = data.get("clipDuration", 30)  # Default to 30 seconds if not provided
        if clip_duration is not None:
            try:
                clip_duration = float(clip_duration)
                if clip_duration <= 0:
                    raise ValueError
            except ValueError:
                return jsonify({"error": "Invalid clip duration. Must be a positive number."}), 400
        target_language = data.get("targetLanguage", "en")
        
        def generate():
            yield json.dumps({"status": "started", "message": "Processing started"}) + "\n"

            output_folder = os.path.join(current_app.config["OUTPUT_FOLDER"], str(uuid.uuid4()))
            os.makedirs(output_folder, exist_ok=True)

            temp_file = os.path.join(output_folder, "temp_video.mp4")
            
            yield json.dumps({"status": "downloading", "message": "Downloading video"}) + "\n"
            download_video(url, temp_file)

            if not os.path.exists(temp_file):
                raise FileNotFoundError(f"Failed to download video: {temp_file}")

            yield json.dumps({"status": "splitting", "message": "Splitting video into clips"}) + "\n"
            
            try:
                clips = split_video(temp_file, output_folder, clip_duration)
                yield json.dumps({"status": "processing", "message": f"Video split into {len(clips)} clips. Starting processing."}) + "\n"

                running_summary = {}
                
                for i, clip in enumerate(clips):
                    logging.info(f"Processing clip {i+1}/{len(clips)}: {clip}")
                    yield json.dumps({"status": "processing", "message": f"Processing clip {i+1}/{len(clips)}"}) + "\n"
                    
                    try:
                        # Process the clip
                        clip_result = process_clip(clip, output_folder, target_language, url)
                        
                        # Update running summary
                        running_summary = update_running_summary(running_summary, clip_result)
                        
                        yield json.dumps({
                            "status": "clip_ready",
                            "data": {
                                "clip": clip_result,
                                "output_folder": os.path.basename(output_folder),
                                "running_summary": running_summary,
                            },
                        }) + "\n"
                    except Exception as clip_error:
                        logging.error(f"Error processing clip {i+1}: {str(clip_error)}", exc_info=True)
                        yield json.dumps({"status": "error", "message": f"Error processing clip {i+1}: {str(clip_error)}"}) + "\n"

                logging.info(f"Finished processing {len(clips)} clips")
                yield json.dumps({
                    "status": "complete",
                    "message": f"Processing complete. Processed {len(clips)} clips.",
                }) + "\n"
            except Exception as e:
                logging.error(f"Error in clip processing loop: {str(e)}", exc_info=True)
                yield json.dumps({"status": "error", "message": f"Error during clip processing: {str(e)}"}) + "\n"
            finally:
                # Clean up the temporary file after all processing is done
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logging.info(f"Removed temporary file: {temp_file}")

        return Response(stream_with_context(generate()), content_type="application/json")

    except Exception as e:
        logging.error(f"Error in process_url route: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error processing URL: {str(e)}"}), 500

def get_video_info(input_file):
    ffprobe_cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-count_packets',
        '-show_entries', 'stream=nb_read_packets,r_frame_rate,duration',
        '-of', 'csv=p=0',
        input_file
    ]
    try:
        ffprobe_output = subprocess.check_output(ffprobe_cmd, stderr=subprocess.STDOUT).decode('utf-8').strip().split(',')
        logging.info(f"ffprobe output: {ffprobe_output}")
        
        if len(ffprobe_output) < 3:
            raise ValueError(f"Unexpected ffprobe output format: {ffprobe_output}")
        
        # Handle frame rate
        fps = float(Fraction(ffprobe_output[0]))
        
        # Handle packet count or duration (depending on ffprobe version)
        try:
            nb_packets = int(float(ffprobe_output[1])) if ffprobe_output[1] != 'N/A' else None
        except ValueError:
            nb_packets = None
        
        # Handle duration
        try:
            duration = float(ffprobe_output[2]) if ffprobe_output[2] != 'N/A' else None
        except ValueError:
            duration = None
        
        # Estimate total frames
        if nb_packets is not None:
            total_frames = nb_packets
        elif duration is not None:
            total_frames = int(duration * fps)
        else:
            # If we don't have duration or packet count, we need an alternative method
            logging.warning("Unable to determine total frames from ffprobe output. Using ffmpeg to count frames.")
            total_frames = count_frames_ffmpeg(input_file)
        
        logging.info(f"Video info: Total frames: {total_frames}, FPS: {fps}, Duration: {duration}")
        
        return total_frames, fps, duration
    
    except subprocess.CalledProcessError as e:
        logging.error(f"ffprobe command failed: {e.output.decode('utf-8')}")
        raise
    except ValueError as e:
        logging.error(f"Error parsing ffprobe output: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error in get_video_info: {str(e)}")
        raise

def count_frames_ffmpeg(input_file):
    cmd = [
        'ffmpeg',
        '-i', input_file,
        '-map', '0:v:0',
        '-c', 'copy',
        '-f', 'null',
        '-'
    ]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()
        matches = re.search(r'frame=\s*(\d+)', output)
        if matches:
            return int(matches.group(1))
        else:
            raise ValueError("Could not find frame count in ffmpeg output")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running ffmpeg: {e.output.decode('utf-8')}")
        raise

def process_video_file_generator(input_file, output_folder, clip_duration):
    logging.info(f"Starting video file processing: input_file={input_file}, output_folder={output_folder}, clip_duration={clip_duration}")
    try:
        total_frames, fps, duration = get_video_info(input_file)
        logging.info(f"Video info: total_frames={total_frames}, fps={fps}, duration={duration}")
        
        for i in range(0, total_frames, int(fps * clip_duration)):
            start_time = i / fps
            end_time = min((i + int(fps * clip_duration)) / fps, duration) if duration else (i + int(fps * clip_duration)) / fps
            
            clip_filename = f"clip_{i//int(fps * clip_duration):04d}.mp4"
            clip_path = os.path.join(output_folder, clip_filename)
            
            # Use ffmpeg to cut the clip
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', input_file,
                '-ss', str(start_time),
                '-t', str(end_time - start_time),
                '-c', 'copy',  # This copies the codec without re-encoding, which is faster
                '-y',  # Overwrite output file if it exists
                clip_path
            ]
            logging.info(f"Running ffmpeg command: {' '.join(ffmpeg_cmd)}")
            subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if os.path.exists(clip_path):
                logging.info(f"Successfully created clip: {clip_path}")
                yield {
                    "filename": clip_filename,
                    "start": start_time,
                    "end": end_time
                }
            else:
                logging.error(f"Failed to create clip: {clip_path}")
    
    except Exception as e:
        logging.error(f"Error in process_video_file_generator: {str(e)}", exc_info=True)
        raise

def process_clip(clip, output_folder, target_language, url):
    logging.info(f"Processing clip: {clip}")
    clip_path = os.path.join(output_folder, clip["filename"])
    audio_path = os.path.join(output_folder, f"{clip['filename']}.wav")

    audio_extracted = extract_audio(clip_path, audio_path)
    logging.info(f"Audio extracted: {audio_extracted}")

    if audio_extracted:
        speech_text = speech_to_text(audio_path)
    else:
        speech_text = "Audio extraction failed. No speech recognition performed."
    logging.info(f"Speech text: {speech_text[:100]}...")

    ocr_text = ocr_from_video(clip_path)
    logging.info(f"OCR text: {ocr_text[:100]}...")

    image_recognition_results = recognize_images_in_video(clip_path)
    logging.info(f"Image recognition results: {image_recognition_results[:3]}...")

    combined_text = f"{speech_text} {ocr_text}".strip()
    if combined_text:
        translated_text = translate_text(combined_text, target_language)
        summary = extract_meaningful_content(combined_text, translated_text, target_language)
    else:
        translated_text = "No text to translate."
        summary = {"error": "No meaningful content found"}
    logging.info(f"Translation and summary complete")

    clip_name = generate_clip_name(speech_text, ocr_text, image_recognition_results)
    logging.info(f"Generated clip name: {clip_name}")

    if os.path.exists(audio_path):
        os.remove(audio_path)  # Clean up temporary audio file
        logging.info(f"Removed temporary audio file: {audio_path}")

    return {
        **clip,
        "clip_name": clip_name,
        "speech_text": speech_text,
        "ocr_text": ocr_text,
        "translated_text": translated_text,
        "summary": summary,
        "image_recognition": image_recognition_results,
        "source_url": url,
        "access_time": datetime.now().isoformat(),
    }

@main.route("/process", methods=["POST"])
def process_video():
    try:
        data = request.json
        filename = data.get("filename")
        url = data.get("url")
        clip_duration = data["clipDuration"]
        target_language = data.get("targetLanguage", "en")

        logging.info(f"Processing video: filename={filename}, url={url}, clip_duration={clip_duration}, target_language={target_language}")

        if filename:
            input_file = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        elif url:
            input_file = download_video(url)
        else:
            return jsonify({"error": "No filename or URL provided"}), 400

        if not os.path.exists(input_file):
            return jsonify({"error": "Input file not found"}), 404

        output_folder = os.path.join(current_app.config["OUTPUT_FOLDER"], os.path.splitext(os.path.basename(input_file))[0])
        os.makedirs(output_folder, exist_ok=True)

        def generate():
            try:
                yield json.dumps({"status": "started", "message": "Processing started"}) + "\n"

                clip_generator = process_video_file_generator(input_file, output_folder, clip_duration)
                running_summary = {}

                for i, clip in enumerate(clip_generator):
                    logging.info(f"Processing clip {i+1}: {clip}")
                    yield json.dumps({"status": "processing", "message": f"Processing clip {i+1}"}) + "\n"
                    
                    clip_result = process_clip(clip, output_folder, target_language, url or filename)
                    
                    running_summary = update_running_summary(running_summary, clip_result)
                    
                    yield json.dumps({
                        "status": "clip_ready",
                        "data": {
                            "clip": clip_result,
                            "output_folder": os.path.basename(output_folder),
                            "running_summary": running_summary,
                        },
                    }) + "\n"

                fake_detection_result = detect_fake_video(input_file)
                
                yield json.dumps({
                    "status": "complete",
                    "message": "Processing complete",
                    "fake_detection_result": fake_detection_result,
                }) + "\n"
            
            except Exception as e:
                logging.error(f"Error in generate function: {str(e)}", exc_info=True)
                yield json.dumps({"status": "error", "message": f"Error during processing: {str(e)}"}) + "\n"

        return Response(stream_with_context(generate()), content_type="application/json")

    except Exception as e:
        logging.error(f"Error in process_video route: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error processing video: {str(e)}"}), 500

@main.route("/process_folder", methods=["POST"])
def process_folder():
    data = request.json
    folder_id = data["folder_id"]
    target_language = data.get("targetLanguage", "en")

    folder_path = os.path.join(current_app.config["UPLOAD_FOLDER"], folder_id)
    if not os.path.exists(folder_path):
        return jsonify({"error": "Folder not found"}), 404

    output_folder = os.path.join(current_app.config["OUTPUT_FOLDER"], folder_id)
    os.makedirs(output_folder, exist_ok=True)

    results = []
    for filename in os.listdir(folder_path):
        if allowed_file(filename):
            clip_path = os.path.join(folder_path, filename)
            audio_path = os.path.join(output_folder, f"{filename}.wav")

            audio_extracted = extract_audio(clip_path, audio_path)

            if audio_extracted:
                speech_text = speech_to_text(audio_path)
            else:
                speech_text = (
                    "Audio extraction failed. No speech recognition performed."
                )

            ocr_text = ocr_from_video(clip_path)

            combined_text = f"{speech_text} {ocr_text}".strip()
            translated_text = (
                translate_text(combined_text, target_language)
                if combined_text
                else "No text to translate."
            )

            results.append(
                {
                    "filename": filename,
                    "speech_text": speech_text,
                    "ocr_text": ocr_text,
                    "translated_text": translated_text,
                }
            )

            if os.path.exists(audio_path):
                os.remove(audio_path)  # Clean up temporary audio file

    return jsonify({"clips": results, "output_folder": folder_id})


@main.route("/output/<path:filename>")
def send_file(filename):
    return send_from_directory(current_app.config["OUTPUT_FOLDER"], filename)


# save_result, load_result/result_name, list_saved_results


@main.route("/save_result", methods=["POST"])
def save_result():
    data = request.json
    result_name = secure_filename(data["name"])
    result_data = data["data"]

    # Add source URL and access time
    result_data["source_url"] = data.get("source_url", "")
    result_data["access_time"] = datetime.now().isoformat()

    file_path = os.path.join(
        current_app.config["SAVED_RESULTS_FOLDER"], f"{result_name}.json"
    )

    with open(file_path, "w") as f:
        json.dump(result_data, f)

    return jsonify({"message": f"Result saved as {result_name}"})


@main.route("/load_result/<result_name>", methods=["GET"])
def load_result(result_name):
    file_path = os.path.join(
        current_app.config["SAVED_RESULTS_FOLDER"], f"{result_name}.json"
    )

    if not os.path.exists(file_path):
        return jsonify({"error": "Result not found"}), 404

    with open(file_path, "r") as f:
        result_data = json.load(f)

    # Update access time
    result_data["access_time"] = datetime.now().isoformat()

    with open(file_path, "r") as f:
        result_data = json.load(f)

    return jsonify(result_data)


@main.route("/list_saved_results", methods=["GET"])
def list_saved_results():
    saved_results = [
        f.replace(".json", "")
        for f in os.listdir(current_app.config["SAVED_RESULTS_FOLDER"])
        if f.endswith(".json")
    ]
    return jsonify(saved_results)


@main.route("/delete_result/<result_name>", methods=["DELETE"])
def delete_result(result_name):
    file_path = os.path.join(
        current_app.config["SAVED_RESULTS_FOLDER"], f"{result_name}.json"
    )

    if not os.path.exists(file_path):
        return jsonify({"error": "Result not found"}), 404

    try:
        os.remove(file_path)
        return jsonify({"message": f"Result {result_name} deleted successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to delete result: {str(e)}"}), 500
