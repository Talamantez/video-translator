import subprocess
import speech_recognition as sr

from flask import current_app

import logging

def extract_audio(video_path, audio_path):
    try:
        command = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # Disable video
            '-acodec', 'pcm_s16le',  # Audio codec
            '-ar', '44100',  # Audio sampling rate
            '-ac', '2',  # Number of audio channels
            '-y',  # Overwrite output file if it exists
            audio_path
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        if result.returncode == 0:
            logging.info(f"Audio extracted successfully: {audio_path}")
            return True
        else:
            logging.error(f"Error extracting audio: {result.stderr}")
            return False
    
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg error: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error in audio extraction: {str(e)}")
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
