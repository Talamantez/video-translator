import re
from .audio_processing_routes import extract_audio, speech_to_text
from .text_processing_routes import ocr_from_video, translate_text, extract_meaningful_content
from .image_processing_routes import recognize_images_in_video
from datetime import datetime
import os
import logging

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

    # Translate speech and OCR text separately
    speech_translated = translate_text(speech_text, target_language) if speech_text else "No speech to translate."
    ocr_translated = translate_text(ocr_text, target_language) if ocr_text else "No OCR text to translate."

    combined_text = f"{speech_text} {ocr_text}".strip()
    if combined_text:
        summary = extract_meaningful_content(combined_text, f"{speech_translated} {ocr_translated}", target_language)
    else:
        summary = {"error": "No meaningful content found"}
    logging.info("Translation and summary complete")

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
        "speech_translated": speech_translated,
        "ocr_translated": ocr_translated,
        "summary": summary,
        "image_recognition": image_recognition_results,
        "source_url": url,
        "access_time": datetime.now().isoformat(),
    }


def generate_clip_name(speech_text, ocr_text, image_recognition_results):
    all_text = f"{speech_text} {ocr_text}"
    
    # Clean the text
    all_text = re.sub(r'[^\w\s]', '', all_text)
    all_text = all_text.strip()

    if len(all_text) < 10:  # Adjust this threshold as needed
        return "short_clip"  # Fallback for very short text

    try:
        key_phrases = keywords.keywords(all_text).split("\n")[:3]
    except Exception as e:
        logging.warning(f"Keyword extraction failed: {str(e)}")
        # Fallback: Use the first few words of the text
        key_phrases = all_text.split()[:3]

    # Use image recognition results if keyword extraction failed
    if not key_phrases and image_recognition_results:
        key_phrases = [result['label'] for result in image_recognition_results[:3]]

    # Generate clip name
    clip_name = "_".join(key_phrases) if key_phrases else "unnamed_clip"
    return clip_name[:50]  # Limit the length of the clip name
