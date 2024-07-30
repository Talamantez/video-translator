import cv2
import numpy as np
from scipy.stats import entropy

def detect_fake_video(video_path):
    cap = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()

    results = {
        "potential_manipulation": False,
        "reasons": []
    }

    # Check for unusual frame rate
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps < 24 or fps > 60:
        results["potential_manipulation"] = True
        results["reasons"].append(f"Unusual frame rate: {fps} FPS")

    # Check for consistent video quality
    if len(frames) > 1:
        qualities = [cv2.Laplacian(frame, cv2.CV_64F).var() for frame in frames]
        quality_std = np.std(qualities)
        if quality_std > 100:  # Threshold can be adjusted
            results["potential_manipulation"] = True
            results["reasons"].append("Inconsistent video quality across frames")

    # Check for abrupt changes in facial landmarks (simplified)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    face_areas = []
    for frame in frames[::10]:  # Check every 10th frame for efficiency
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        if len(faces) > 0:
            face_areas.append(faces[0][2] * faces[0][3])  # Width * Height of the first detected face
    if len(face_areas) > 1:
        face_area_changes = np.diff(face_areas) / np.array(face_areas[:-1])
        if np.any(np.abs(face_area_changes) > 0.5):  # Threshold for abrupt change
            results["potential_manipulation"] = True
            results["reasons"].append("Abrupt changes in facial proportions detected")

    # Check for unusual color distribution
    color_entropies = []
    for frame in frames[::10]:  # Check every 10th frame for efficiency
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])
        color_entropies.append(entropy(hist.flatten()))
    if np.std(color_entropies) > 0.5:  # Threshold can be adjusted
        results["potential_manipulation"] = True
        results["reasons"].append("Unusual color distribution changes")

    return results