import pytest
import json
import os
from app import create_app
from unittest.mock import patch, MagicMock
import io

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.data  # Assuming it returns HTML

def test_upload_route(client):
    data = {
        'file': (io.BytesIO(b"abcdef"), 'test.mp4')
    }
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    assert 'filename' in json.loads(response.data)
    assert 'duration' in json.loads(response.data)
@patch('app.routes.download_video')
@patch('app.routes.process_video_file_generator')
@patch('app.routes.process_clip')
@patch('app.routes.detect_fake_video')

def test_process_url(mock_detect_fake_video, mock_process_clip, mock_process_video_file_generator, mock_download_video, client):
    mock_download_video.return_value = 'path/to/fake/video.mp4'
    mock_process_video_file_generator.return_value = [{'filename': 'clip_1.mp4', 'start': 0, 'end': 10}]
    mock_process_clip.return_value = {
        'clip_name': 'Test Clip',
        'speech_text': 'This is a test',
        'ocr_text': 'OCR Text',
        'translated_text': 'Translated text',
        'summary': {'key_phrases': ['test']},
        'image_recognition': [{'label': 'object'}]
    }
    mock_detect_fake_video.return_value = {'is_fake': False, 'confidence': 0.9}

    url = "/process_url"
    data = {
        "url": "https://example.com/sample_video.mp4",
        "clipDuration": 10,
        "targetLanguage": "en"
    }
    
    response = client.post(url, json=data)
    
    assert response.status_code == 200
    
    response_data = response.get_data(as_text=True)
    response_lines = response_data.strip().split('\n')
    
    assert json.loads(response_lines[0])['status'] == 'started'
    assert json.loads(response_lines[1])['status'] == 'downloading'
    assert json.loads(response_lines[2])['status'] == 'processing'
    assert json.loads(response_lines[3])['status'] == 'clip_ready'
    assert json.loads(response_lines[4])['status'] == 'complete'

    mock_download_video.assert_called_once()
    mock_process_video_file_generator.assert_called_once()
    mock_process_clip.assert_called_once()
    mock_detect_fake_video.assert_called_once()

def test_process_route(client):
    data = {
        "filename": "test_video.mp4",
        "clipDuration": 10,
        "targetLanguage": "en"
    }
    
    response = client.post('/process', json=data)
    
    assert response.status_code == 200
    
    response_data = response.get_data(as_text=True)
    for line in response_data.split('\n'):
        if line:
            json_response = json.loads(line)
            print(json_response)
            
            if json_response["status"] == "complete":
                assert "fake_detection_result" in json_response
                break
            elif json_response["status"] == "clip_ready":
                assert "clip" in json_response["data"]
                assert "running_summary" in json_response["data"]

def test_save_and_load_result(client):
    # Test saving a result
    save_data = {
        "name": "test_result",
        "data": {"key": "value"},
        "source_url": "https://example.com"
    }
    response = client.post('/save_result', json=save_data)
    assert response.status_code == 200
    assert b'Result saved as test_result' in response.data

    # Test loading the saved result
    response = client.get('/load_result/test_result')
    assert response.status_code == 200
    loaded_data = json.loads(response.data)
    assert loaded_data["key"] == "value"
    assert "access_time" in loaded_data

def test_list_and_delete_results(client):
    # Test listing saved results
    response = client.get('/list_saved_results')
    assert response.status_code == 200
    results = json.loads(response.data)
    assert "test_result" in results

    # Test deleting a result
    response = client.delete('/delete_result/test_result')
    assert response.status_code == 200
    assert b'Result test_result deleted successfully' in response.data

    # Verify the result is deleted
    response = client.get('/load_result/test_result')
    assert response.status_code == 404

if __name__ == '__main__':
    pytest.main()