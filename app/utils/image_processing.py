import cv2
import numpy as np
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input, decode_predictions

def recognize_images_in_video(video_path, num_frames=10):
    model = ResNet50(weights='imagenet')
    
    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frames_to_sample = np.linspace(0, frame_count - 1, num_frames, dtype=int)
    
    results = []
    for frame_idx in frames_to_sample:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if ret:
            img = cv2.resize(frame, (224, 224))
            img = preprocess_input(img)
            img = np.expand_dims(img, axis=0)
            
            preds = model.predict(img)
            decoded_preds = decode_predictions(preds, top=1)[0]
            
            for _, label, confidence in decoded_preds:
                results.append({"label": label, "confidence": float(confidence)})
    
    cap.release()
    
    # Aggregate results and return top 5
    aggregated_results = {}
    for result in results:
        if result["label"] in aggregated_results:
            aggregated_results[result["label"]] += result["confidence"]
        else:
            aggregated_results[result["label"]] = result["confidence"]
    
    sorted_results = sorted(aggregated_results.items(), key=lambda x: x[1], reverse=True)
    return [{"label": label, "confidence": confidence / num_frames} for label, confidence in sorted_results[:5]]