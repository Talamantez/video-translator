from fractions import Fraction
import re
import subprocess
from flask import Blueprint, request, jsonify, current_app, Response
from app.utils.core_processing import VideoProcessor
from app.utils.video_processing import download_video
from app.utils.file_handling import allowed_file, get_video_duration
from app.utils.audio_processing import extract_audio, speech_to_text
from app.utils.text_processing import ocr_from_video, translate_text, extract_meaningful_content
from app.utils.image_processing import recognize_images_in_video
from app.utils.fake_video_detection import detect_fake_video
from datetime import datetime
import os
import json
import logging
import uuid
from flask import stream_with_context
from summa import keywords

process_bp = Blueprint('process', __name__)


# Include all the processing functions here (generate_clip_name, update_running_summary, process_clip, etc.)

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
    
@process_bp.route("/process_url", methods=["POST"])
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
                        clip_result = VideoProcessor.process_clip(clip, output_folder, target_language, url)
                        
                        # Update running summary
                        running_summary = VideoProcessor.update_running_summary(running_summary, clip_result)
                        
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

@process_bp.route("/process", methods=["POST"])
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
                    
                    clip_result = VideoProcessor.process_clip(clip, output_folder, target_language, url or filename)
                    
                    running_summary = VideoProcessor.update_running_summary(running_summary, clip_result)
                    
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

@process_bp.route("/process_folder", methods=["POST"])
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

