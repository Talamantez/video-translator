import cv2
import speech_recognition as sr
import pytesseract
from pydub import AudioSegment
from googletrans import Translator
from langdetect import detect
import numpy as np
import os

def extract_audio(video_path, audio_path):
    video = AudioSegment.from_file(video_path, format="mp4")
    audio = video.set_channels(1).set_frame_rate(16000)
    audio.export(audio_path, format="wav")

def speech_to_text(audio_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return "Speech recognition could not understand audio"

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

def detect_language(text):
    return detect(text)

def translate_text(text, target_language='en'):
    translator = Translator()
    return translator.translate(text, dest=target_language).text

def assess_quality(original, translated):
    # Implement BLEU score or other quality metrics here
    # For simplicity, we'll use a basic word match ratio
    original_words = set(original.lower().split())
    translated_words = set(translated.lower().split())
    return len(original_words.intersection(translated_words)) / len(original_words)

def process_video(video_path):
    audio_path = "temp_audio.wav"
    extract_audio(video_path, audio_path)

    speech_text = speech_to_text(audio_path)
    ocr_text = ocr_from_video(video_path)

    combined_text = speech_text + " " + ocr_text
    detected_language = detect_language(combined_text)

    translated_text = translate_text(combined_text, 'en')
    quality_score = assess_quality(combined_text, translated_text)

    # Clean up temporary audio file
    if os.path.exists(audio_path):
        os.remove(audio_path)

    return {
        "speech_text": speech_text,
        "ocr_text": ocr_text,
        "detected_language": detected_language,
        "translated_text": translated_text,
        "quality_score": quality_score
    }