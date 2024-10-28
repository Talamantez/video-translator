import cv2
import numpy as np
from ultralytics import YOLO
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input, decode_predictions
import logging

class VideoAnalyzer:
    def __init__(self):
        self.resnet_model = ResNet50(weights='imagenet')
        self.yolo_model = YOLO('yolov8n.pt')
        logging.info("Initialized VideoAnalyzer with ResNet50 and YOLOv8")

    def process_frame(self, frame):
        """Process a single frame with both ResNet50 and YOLOv8"""
        results = {
            'classifications': self._classify_frame(frame),
            'detections': self._detect_objects_frame(frame)
        }
        return results

    def _classify_frame(self, frame):
        """Classify frame using ResNet50"""
        try:
            img = cv2.resize(frame, (224, 224))
            img = preprocess_input(img)
            img = np.expand_dims(img, axis=0)
            
            preds = self.resnet_model.predict(img, verbose=0)
            decoded_preds = decode_predictions(preds, top=3)[0]
            
            return [
                {"label": label, "confidence": float(conf)} 
                for _, label, conf in decoded_preds
            ]
        except Exception as e:
            logging.error(f"Error in classification: {str(e)}")
            return []

    def _detect_objects_frame(self, frame):
        """Detect objects using YOLOv8"""
        try:
            results = self.yolo_model(frame, verbose=False)
            detections = []
            
            for r in results[0]:
                boxes = r.boxes
                for box in boxes:
                    detection = {
                        "class": self.yolo_model.names[int(box.cls[0])],
                        "confidence": float(box.conf[0]),
                        "bbox": box.xyxy[0].tolist()
                    }
                    detections.append(detection)
            
            return detections
        except Exception as e:
            logging.error(f"Error in object detection: {str(e)}")
            return []

def recognize_images_in_video(video_path, num_frames=10):
    """Enhanced version of recognize_images_in_video with both classification and detection"""
    try:
        analyzer = VideoAnalyzer()
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            logging.error(f"Could not open video file: {video_path}")
            return {'classifications': [], 'detections': [], 'error': 'Could not open video file'}
            
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        if frame_count == 0 or fps == 0:
            logging.error(f"Invalid video properties: frames={frame_count}, fps={fps}")
            return {'classifications': [], 'detections': [], 'error': 'Invalid video properties'}
            
        # Ensure we don't try to sample more frames than exist
        num_frames = min(num_frames, frame_count)
        frames_to_sample = np.linspace(0, frame_count - 1, num_frames, dtype=int)
        
        results = {
            'classifications': [],
            'detections': [],
            'frame_timestamps': []
        }
        
        for frame_idx in frames_to_sample:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                continue
                
            timestamp = frame_idx / fps if fps > 0 else 0
            frame_results = analyzer.process_frame(frame)
            
            results['classifications'].extend(frame_results['classifications'])
            results['detections'].extend([
                {**det, 'timestamp': timestamp}
                for det in frame_results['detections']
            ])
            results['frame_timestamps'].append(timestamp)
        
        cap.release()
        
        # Aggregate classifications
        class_counts = {}
        for cls in results['classifications']:
            label = cls['label']
            if label in class_counts:
                class_counts[label]['count'] += 1
                class_counts[label]['confidence'] += cls['confidence']
            else:
                class_counts[label] = {
                    'count': 1,
                    'confidence': cls['confidence']
                }
        
        # Average the confidences and sort
        aggregated_classifications = [
            {
                'label': label,
                'confidence': stats['confidence'] / stats['count'],
                'occurrences': stats['count']
            }
            for label, stats in class_counts.items()
        ]
        aggregated_classifications.sort(key=lambda x: x['confidence'], reverse=True)
        
        final_results = {
            'classifications': aggregated_classifications[:5],  # Top 5 classifications
            'detections': results['detections'],  # All detections with timestamps
            'analyzed_frames': len(results['frame_timestamps']),
            'video_duration': frame_count / fps if fps > 0 else 0
        }
        
        # Ensure results is serializable
        logging.info(f"Successfully processed video with {len(final_results['detections'])} detections")
        return final_results
        
    except Exception as e:
        logging.error(f"Error in recognize_images_in_video: {str(e)}")
        return {
            'classifications': [],
            'detections': [],
            'error': str(e)
        }