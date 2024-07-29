from flask import Blueprint, render_template, request, jsonify, send_from_directory, current_app
from app.utils.video_processing import download_video, process_video_file
from app.utils.audio_processing import extract_audio, speech_to_text
from app.utils.text_processing import ocr_from_video, translate_text
from app.utils.file_handling import allowed_file, get_video_duration
import os
import uuid
import json
from werkzeug.utils import secure_filename

main = Blueprint("main", __name__)

@main.route("/")
def index():
    current_app.logger.debug(f"Current working directory: {os.getcwd()}")
    current_app.logger.debug(f"Does index.html exist: {os.path.exists('app/templates/index.html')}")
    return render_template("index.html")

@main.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        duration = get_video_duration(filepath)
        return jsonify({"filename": filename, "duration": duration})
    return jsonify({"error": "File type not allowed"}), 400

@main.route("/upload_folder", methods=["POST"])
def upload_folder():
    if "files[]" not in request.files:
        return jsonify({"error": "No file part"}), 400

    files = request.files.getlist("files[]")
    if not files or files[0].filename == "":
        return jsonify({"error": "No selected files"}), 400

    folder_id = str(uuid.uuid4())
    folder_path = os.path.join(current_app.config["UPLOAD_FOLDER"], folder_id)
    os.makedirs(folder_path, exist_ok=True)

    uploaded_files = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(folder_path, filename)
            file.save(filepath)
            uploaded_files.append(filename)

    if not uploaded_files:
        return jsonify({"error": "No valid files uploaded"}), 400

    return jsonify({"folder_id": folder_id, "files": uploaded_files})


@main.route("/process_url", methods=["POST"])
def process_url():
    try:
        data = request.json
        url = data["url"]
        clip_duration = data["clipDuration"]
        target_language = data.get("targetLanguage", "en")

        current_app.logger.info(f"Processing URL: {url}")

        output_folder = os.path.join(
            current_app.config["OUTPUT_FOLDER"], str(uuid.uuid4())
        )
        os.makedirs(output_folder, exist_ok=True)

        temp_file = os.path.join(output_folder, "temp_video.mp4")
        download_video(url, temp_file)

        if not os.path.exists(temp_file):
            raise FileNotFoundError(f"Failed to download video: {temp_file}")
        clips = process_video_file(temp_file, output_folder, clip_duration)

        results = []
        for clip in clips:
            clip_path = os.path.join(output_folder, clip["filename"])
            audio_path = os.path.join(output_folder, f"{clip['filename']}.wav")

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
                    **clip,
                    "speech_text": speech_text,
                    "ocr_text": ocr_text,
                    "translated_text": translated_text,
                }
            )

            if os.path.exists(audio_path):
                os.remove(audio_path)  # Clean up temporary audio file

        if os.path.exists(temp_file):
            os.remove(temp_file)  # Clean up the temporary video file

        current_app.logger.info(f"Processed {len(clips)} clips")
        return jsonify(
            {"clips": results, "output_folder": os.path.basename(output_folder)}
        )
    except Exception as e:
        current_app.logger.error(f"Error processing URL: {str(e)}")
        return jsonify({"error": f"Error processing URL: {str(e)}"}), 500


@main.route('/process', methods=['POST'])
def process_video():
    try:
        data = request.json
        filename = data['filename']
        clip_duration = data['clipDuration']
        target_language = data.get('targetLanguage', 'en')
        
        current_app.logger.info(f"Processing video: {filename}")
        
        input_file = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        output_folder = os.path.join(current_app.config['OUTPUT_FOLDER'], os.path.splitext(filename)[0])
        os.makedirs(output_folder, exist_ok=True)
        
        clips = process_video_file(input_file, output_folder, clip_duration)
        
        results = []
        for clip in clips:
            clip_path = os.path.join(output_folder, clip["filename"])
            audio_path = os.path.join(output_folder, f"{clip['filename']}.wav")

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
                    **clip,
                    "speech_text": speech_text,
                    "ocr_text": ocr_text,
                    "translated_text": translated_text,
                }
            )

            if os.path.exists(audio_path):
                os.remove(audio_path)  # Clean up temporary audio file

        current_app.logger.info(f"Processed {len(clips)} clips for {filename}")
        return jsonify(
            {"clips": results, "output_folder": os.path.splitext(filename)[0]}
        )

    except FileNotFoundError as e:
        current_app.logger.error(f"File not found error: {str(e)}")
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error processing video: {str(e)}")
        return jsonify({'error': f"Error processing video: {str(e)}"}), 500


@main.route("/process_folder", methods=["POST"])

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


@main.route("/output/<path:filename>")
def send_file(filename):
    return send_from_directory(current_app.config["OUTPUT_FOLDER"], filename)

# save_result, load_result/result_name, list_saved_results

@main.route('/save_result', methods=['POST'])
def save_result():
    data = request.json
    result_name = secure_filename(data['name'])
    result_data = data['data']
    
    file_path = os.path.join(current_app.config['SAVED_RESULTS_FOLDER'], f"{result_name}.json")
    
    with open(file_path, 'w') as f:
        json.dump(result_data, f)
    
    return jsonify({"message": f"Result saved as {result_name}"})

@main.route('/load_result/<result_name>', methods=['GET'])
def load_result(result_name):
    file_path = os.path.join(current_app.config['SAVED_RESULTS_FOLDER'], f"{result_name}.json")
    
    if not os.path.exists(file_path):
        return jsonify({"error": "Result not found"}), 404
    
    with open(file_path, 'r') as f:
        result_data = json.load(f)
    
    return jsonify(result_data)

@main.route('/list_saved_results', methods=['GET'])
def list_saved_results():
    saved_results = [f.replace('.json', '') for f in os.listdir(current_app.config['SAVED_RESULTS_FOLDER']) if f.endswith('.json')]
    return jsonify(saved_results)