import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from app.utils.video_processing import process_video_file, download_streaming_video, download_video, download_from_archive

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_video_file(tmp_path):
    video_file = tmp_path / "test_video.mp4"
    video_file.write_text("mock video content")
    return str(video_file)

@pytest.fixture
def mock_output_folder(tmp_path):
    output_folder = tmp_path / "output"
    output_folder.mkdir()
    return str(output_folder)

@patch('app.utils.video_processing.VideoFileClip')
@patch('app.utils.video_processing.multiprocessing.Pool')
def test_process_video_file(mock_pool, mock_video_clip, mock_video_file, mock_output_folder):
    mock_video_clip.return_value.duration = 30
    mock_subclip = MagicMock()
    mock_video_clip.return_value.subclip.return_value = mock_subclip
    
    mock_pool.return_value.__enter__.return_value.map.return_value = None

    clips = process_video_file(mock_video_file, mock_output_folder, clip_duration=10)

    assert len(clips) == 3
    assert all(clip['duration'] == 10 for clip in clips[:2])
    assert clips[2]['duration'] == 10
    assert clips[2]['start_time'] == 20
    assert clips[2]['end_time'] == 30

    mock_pool.assert_called_once()
    mock_pool.return_value.__enter__.return_value.map.assert_called_once()
    
@pytest.mark.parametrize("download_func", [
    download_streaming_video,
    download_video,
    download_from_archive
])

def test_download_functions(download_func, tmp_path):
    with patch('app.utils.video_processing.yt_dlp.YoutubeDL') as mock_yt_dlp:
        mock_yt_dlp.return_value.__enter__.return_value.download.return_value = None

        output_path = str(tmp_path / "output.mp4")
        if download_func == download_from_archive:
            download_func("test_identifier", output_path)
        else:
            download_func("https://example.com/video", output_path)

        mock_yt_dlp.assert_called_once()
        mock_yt_dlp.return_value.__enter__.return_value.download.assert_called_once()

@patch('app.utils.video_processing.VideoFileClip')
@patch('app.utils.video_processing.multiprocessing.Pool')
def test_process_video_file_short_duration(mock_pool, mock_video_clip, mock_video_file, mock_output_folder):
    mock_video_clip.return_value.duration = 5
    mock_subclip = MagicMock()
    mock_video_clip.return_value.subclip.return_value = mock_subclip
    
    mock_pool.return_value.__enter__.return_value.map.return_value = None

    clips = process_video_file(mock_video_file, mock_output_folder, clip_duration=10)

    assert len(clips) == 1
    assert clips[0]['duration'] == 5
    assert clips[0]['start_time'] == 0
    assert clips[0]['end_time'] == 5

    mock_pool.assert_called_once()
    mock_pool.return_value.__enter__.return_value.map.assert_called_once()

@patch('app.utils.video_processing.VideoFileClip')
@patch('app.utils.video_processing.multiprocessing.Pool')
def test_process_video_file_exact_duration(mock_pool, mock_video_clip, mock_video_file, mock_output_folder):
    mock_video_clip.return_value.duration = 20
    mock_subclip = MagicMock()
    mock_video_clip.return_value.subclip.return_value = mock_subclip
    
    mock_pool.return_value.__enter__.return_value.map.return_value = None

    clips = process_video_file(mock_video_file, mock_output_folder, clip_duration=10)

    assert len(clips) == 2
    assert all(clip['duration'] == 10 for clip in clips)
    assert clips[0]['start_time'] == 0
    assert clips[0]['end_time'] == 10
    assert clips[1]['start_time'] == 10
    assert clips[1]['end_time'] == 20

    mock_pool.assert_called_once()
    mock_pool.return_value.__enter__.return_value.map.assert_called_once()

if __name__ == "__main__":
    pytest.main()