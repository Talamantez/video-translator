import os
import subprocess
import logging
import re
from fractions import Fraction
from .utils_routes import get_video_duration
from ultralytics import YOLO
import cv2

# Initialize YOLO model globally - will load only once
model = YOLO('yolov8n.pt')  # using the smallest model to start

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

def detect_objects_in_clip(clip_path):
    """
    Perform object detection on key frames of a video clip
    Returns a dict of detected objects with timestamps
    """
    try:
        cap = cv2.VideoCapture(clip_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Process one frame per second
        detections = []
        for frame_idx in range(0, frame_count, int(fps)):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                continue
                
            # Run YOLO detection
            results = model(frame)
            
            # Get timestamp for this frame
            timestamp = frame_idx / fps
            
            # Process results
            frame_detections = []
            for r in results[0]:
                for box in r.boxes:
                    obj = {
                        'class': model.names[int(box.cls[0])],
                        'confidence': float(box.conf[0]),
                        'bbox': box.xyxy[0].tolist(),
                        'timestamp': timestamp
                    }
                    frame_detections.append(obj)
            
            if frame_detections:
                detections.append({
                    'timestamp': timestamp,
                    'objects': frame_detections
                })
        
        cap.release()
        return detections
        
    except Exception as e:
        logging.error(f"Error in object detection for {clip_path}: {str(e)}")
        return []

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
                '-c', 'copy',
                '-y',
                clip_path
            ]
            logging.info(f"Running ffmpeg command: {' '.join(ffmpeg_cmd)}")
            subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if os.path.exists(clip_path):
                logging.info(f"Successfully created clip: {clip_path}")
                
                # Perform object detection on the clip
                detections = detect_objects_in_clip(clip_path)
                
                yield {
                    "filename": clip_filename,
                    "start": start_time,
                    "end": end_time,
                    "objects": detections  # Add object detections to the output
                }
            else:
                logging.error(f"Failed to create clip: {clip_path}")
    
    except Exception as e:
        logging.error(f"Error in process_video_file_generator: {str(e)}", exc_info=True)
        raise