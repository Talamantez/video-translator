import cv2
import pytesseract
from googletrans import Translator

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
