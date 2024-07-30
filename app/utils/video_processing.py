import os
import yt_dlp
from moviepy.editor import VideoFileClip


def process_video_file(input_file, output_folder, clip_duration=10):
    clip = VideoFileClip(input_file)
    total_duration = clip.duration

    if clip_duration is None or clip_duration <= 0:
        clip_duration = 10  # Default to 10 seconds if clip_duration is invalid

    num_clips = int(total_duration // clip_duration) + 1
    clips = []

    for i in range(num_clips):
        start_time = i * clip_duration
        end_time = min((i + 1) * clip_duration, total_duration)
        
        subclip = clip.subclip(start_time, end_time)
        
        output_filename = f"clip_{i+1}.mp4"
        output_path = os.path.join(output_folder, output_filename)
        
        subclip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        
        clips.append({
            "filename": output_filename,
            "start_time": start_time,
            "end_time": end_time,
            "duration": end_time - start_time
        })

    clip.close()
    
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
