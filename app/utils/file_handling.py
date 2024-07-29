import os
import json
import subprocess
from flask import current_app
import yt_dlp

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def get_video_duration(filename):
    try:
        result = subprocess.run(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', filename], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        data = json.loads(result.stdout)
        
        # Try to get duration from format
        if 'format' in data and 'duration' in data['format']:
            return float(data['format']['duration'])
        
        # If not in format, try to get from streams
        if 'streams' in data:
            for stream in data['streams']:
                if 'duration' in stream:
                    return float(stream['duration'])
        
        # If we still can't find duration, try to calculate from frames
        if 'streams' in data:
            for stream in data['streams']:
                if stream.get('codec_type') == 'video':
                    if 'nb_frames' in stream and 'avg_frame_rate' in stream:
                        nb_frames = int(stream['nb_frames'])
                        fps = eval(stream['avg_frame_rate'])
                        if fps != 0:
                            return nb_frames / fps
        
        # If all else fails, return 0
        return 0
    except Exception as e:
        current_app.logger.error(f"Error getting video duration: {str(e)}")
        return 0

def check_folder_permissions():
    folders_to_check = [current_app.config['UPLOAD_FOLDER'], current_app.config['OUTPUT_FOLDER']]
    for folder in folders_to_check:
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
            except PermissionError:
                current_app.logger.error(f"Permission denied when creating folder: {folder}")
                raise
        elif not os.access(folder, os.W_OK):
            current_app.logger.error(f"No write permission for folder: {folder}")
            raise PermissionError(f"No write permission for folder: {folder}")

def search_internet_archive(query):
    base_url = "https://archive.org/advancedsearch.php"
    params = {
        "q": query,
        "fl[]": "identifier,title",
        "sort[]": "downloads desc",
        "output": "json",
        "rows": 10,
        "page": 1,
        "mediatype": "movies"
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get("response", {}).get("docs", [])
    else:
        return []

def download_from_archive(identifier, output_path):
    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': output_path,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://archive.org/details/{identifier}"])
