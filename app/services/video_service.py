# app/services/video_service.py

from typing import Generator, Dict, Any, Optional, List
import os
import logging
import uuid
import subprocess
from fractions import Fraction
import re
from datetime import datetime

from ..utils.video_processing import download_video
from ..utils.file_handling import get_video_duration
from ..utils.core_processing import VideoProcessor
from ..utils.fake_video_detection import detect_fake_video

class VideoService:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def process_url(self, url: str, clip_duration: float, target_language: str) -> Generator:
        """
        Process a video from URL with progress updates.
        
        Args:
            url: Video URL to process
            clip_duration: Duration of each clip in seconds
            target_language: Target language for translations
            
        Yields:
            Dict containing processing status and results
        """
        try:
            yield {"status": "started", "message": "Processing started"}

            # Create unique output folder
            output_folder = os.path.join(self.config["OUTPUT_FOLDER"], str(uuid.uuid4()))
            os.makedirs(output_folder, exist_ok=True)

            # Download video
            temp_file = os.path.join(output_folder, "temp_video.mp4")
            yield {"status": "downloading", "message": "Downloading video"}
            
            download_video(url, temp_file)
            if not os.path.exists(temp_file):
                raise FileNotFoundError(f"Failed to download video: {temp_file}")

            # Split and process video
            yield {"status": "splitting", "message": "Splitting video into clips"}
            
            try:
                clips = self._split_video(temp_file, output_folder, clip_duration)
                yield {
                    "status": "processing", 
                    "message": f"Video split into {len(clips)} clips. Starting processing."
                }

                running_summary = {}
                
                # Process each clip
                for i, clip in enumerate(clips):
                    self.logger.info(f"Processing clip {i+1}/{len(clips)}: {clip}")
                    yield {
                        "status": "processing", 
                        "message": f"Processing clip {i+1}/{len(clips)}"
                    }
                    
                    try:
                        clip_result = VideoProcessor.process_clip(
                            clip, output_folder, target_language, url
                        )
                        running_summary = VideoProcessor.update_running_summary(
                            running_summary, clip_result
                        )
                        
                        yield {
                            "status": "clip_ready",
                            "data": {
                                "clip": clip_result,
                                "output_folder": os.path.basename(output_folder),
                                "running_summary": running_summary,
                            },
                        }
                        
                    except Exception as e:
                        self.logger.error(f"Error processing clip {i+1}: {str(e)}", exc_info=True)
                        yield {
                            "status": "error", 
                            "message": f"Error processing clip {i+1}: {str(e)}"
                        }

                # Final fake video analysis
                fake_detection_result = detect_fake_video(temp_file)
                
                yield {
                    "status": "complete",
                    "message": f"Processing complete. Processed {len(clips)} clips.",
                    "fake_detection_result": fake_detection_result,
                }

            finally:
                # Cleanup
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    self.logger.info(f"Removed temporary file: {temp_file}")

        except Exception as e:
            self.logger.error(f"Error in process_url: {str(e)}", exc_info=True)
            yield {"status": "error", "message": f"Error processing URL: {str(e)}"}

    def _split_video(
        self, input_file: str, output_folder: str, clip_duration: float = 30
    ) -> List[Dict[str, Any]]:
        """
        Split a video file into clips of specified duration.
        """
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        total_duration = get_video_duration(input_file)
        if total_duration == 0:
            self.logger.error(f"Could not determine duration of {input_file}")
            return []

        clips = []
        num_clips = int(total_duration // clip_duration) + 1

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
                self.logger.error(f"Error processing clip {i+1}: {e.stderr.decode()}")

        return clips

    def get_video_info(self, input_file: str) -> tuple:
        """
        Get video information using ffprobe.
        """
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
            ffprobe_output = subprocess.check_output(
                ffprobe_cmd, stderr=subprocess.STDOUT
            ).decode('utf-8').strip().split(',')
            
            if len(ffprobe_output) < 3:
                raise ValueError(f"Unexpected ffprobe output format: {ffprobe_output}")
            
            fps = float(Fraction(ffprobe_output[0]))
            nb_packets = int(float(ffprobe_output[1])) if ffprobe_output[1] != 'N/A' else None
            duration = float(ffprobe_output[2]) if ffprobe_output[2] != 'N/A' else None
            
            total_frames = (
                nb_packets or 
                int(duration * fps) if duration 
                else self._count_frames_ffmpeg(input_file)
            )
            
            return total_frames, fps, duration
            
        except Exception as e:
            self.logger.error(f"Error in get_video_info: {str(e)}")
            raise

    def _count_frames_ffmpeg(self, input_file: str) -> int:
        """
        Count frames using ffmpeg when other methods fail.
        """
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
            raise ValueError("Could not find frame count in ffmpeg output")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error running ffmpeg: {e.output.decode('utf-8')}")
            raise