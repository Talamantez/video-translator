import subprocess
import speech_recognition as sr

from flask import current_app

def extract_audio(video_path, audio_path):
    try:
        result = subprocess.run([
            'ffmpeg',
            '-i', video_path,
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # Audio codec
            '-ar', '44100',  # Audio sample rate
            '-ac', '2',  # Audio channels
            '-f', 'wav',  # Force WAV format
            audio_path
        ], check=True, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        current_app.logger.error(f"Error extracting audio: {e.stderr.decode()}")
        return False

def speech_to_text(audio_path):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            return "Could not request results from speech recognition service"
    except Exception as e:
        current_app.logger.error(f"Error in speech_to_text: {str(e)}")
        return f"Error processing audio: {str(e)}"
