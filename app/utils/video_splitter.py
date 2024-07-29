import os
import subprocess
import json

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
        print(f"Error getting video duration: {str(e)}")
        return 0

def split_video(input_file, output_folder, clip_duration=30):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    total_duration = get_video_duration(input_file)
    if total_duration == 0:
        print(f"Could not determine duration of {input_file}")
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
            print(f"Error processing clip {i+1}: {e.stderr.decode()}")

    return clips