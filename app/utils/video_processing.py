import os
import yt_dlp
import multiprocessing
from moviepy.editor import VideoFileClip


def process_chunk(chunk_info):
    input_file, start_time, end_time, output_path = chunk_info
    subclip = VideoFileClip(input_file).subclip(start_time, end_time)
    subclip.write_videofile(output_path, codec="libx264", audio_codec="aac")
    subclip.close()

def process_video_file(input_file, output_folder, clip_duration=10):
    """
    Process a video file by splitting it into smaller clips.

    Args:
    input_file (str): Path to the input video file.
    output_folder (str): Path to the folder where output clips will be saved.
    clip_duration (int, optional): Duration of each clip in seconds. Defaults to 10.

    Returns:
    list: A list of dictionaries containing information about each clip.

    Raises:
    IOError: If there's an error opening the video file.
    RuntimeError: If there's an unexpected error during processing.
    """
    clip = VideoFileClip(input_file)
    total_duration = clip.duration
    clip.close()

    chunks = []
    for i in range(0, int(total_duration), clip_duration):
        start_time = i
        end_time = min(i + clip_duration, total_duration)
        output_path = os.path.join(output_folder, f"clip_{i//clip_duration + 1}.mp4")
        chunks.append((input_file, start_time, end_time, output_path))

    with multiprocessing.Pool() as pool:
        pool.map(process_chunk, chunks)

    # Return clip info as before
    return [{"filename": f"clip_{i+1}.mp4", "start_time": chunk[1], "end_time": chunk[2], "duration": chunk[2] - chunk[1]} for i, chunk in enumerate(chunks)]

def download_streaming_video(url, output_path):
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_path,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.DownloadError as e:
        raise RuntimeError(f"Error downloading video: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error during video download: {e}")

def download_video(url, output_path):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'verbose': True,  # Enable verbose output
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
        except yt_dlp.utils.DownloadError as e:
            print(f"An error occurred: {str(e)}")
            print("Attempting to troubleshoot...")
            
            # Try listing available formats
            print("Available formats:")
            ydl.params['listformats'] = True
            ydl.download([url])
            
            # Try downloading with a lower quality
            print("Attempting download with lower quality...")
            ydl.params['format'] = 'worstvideo+worstaudio/worst'
            ydl.params['listformats'] = False
            try:
                ydl.download([url])
                print("Download successful with lower quality.")
            except yt_dlp.utils.DownloadError:
                print("Download failed even with lower quality.")
            
            # Print yt-dlp version
            print(f"yt-dlp version: {yt_dlp.version.__version__}")
            
            raise e
        
def download_from_archive(identifier, output_path):
    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': output_path,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://archive.org/details/{identifier}"])
