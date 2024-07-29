from flask import current_app
import os
import subprocess
import yt_dlp

from app.utils.video_splitter import get_video_duration

def process_video_file(input_file, output_folder, clip_duration=30):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    clips = []
    total_duration = get_video_duration(input_file)
    num_clips = int(total_duration // clip_duration) + 1

    for i in range(num_clips):
        start_time = i * clip_duration
        end_time = min((i + 1) * clip_duration, total_duration)

        output_file = os.path.join(output_folder, f"clip_{i+1:03d}.mp4")
        
        # Remove the file if it already exists
        if os.path.exists(output_file):
            os.remove(output_file)
        
        try:
            subprocess.run([
                'ffmpeg',
                '-i', input_file,
                '-ss', str(start_time),
                '-to', str(end_time),
                '-c', 'copy',
                '-y',  # This flag tells ffmpeg to overwrite without prompting
                output_file
            ], check=True, stderr=subprocess.PIPE)

            clips.append({
                'filename': f"clip_{i+1:03d}.mp4",
                'start': start_time,
                'end': end_time
            })
        except subprocess.CalledProcessError as e:
            current_app.logger.error(f"Error processing clip {i+1}: {e.stderr.decode()}")
            # You might want to handle this error, e.g., skip this clip or raise an exception

    return clips

def download_streaming_video(url, output_path):
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_path,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        
def download_video(url, output_path):
    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': output_path,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def download_from_archive(identifier, output_path):
    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': output_path,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://archive.org/details/{identifier}"])
