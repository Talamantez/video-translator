import uuid
from flask import Blueprint, render_template, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from app.utils.file_handling import allowed_file, get_video_duration
import os

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    current_app.logger.debug(f"Current working directory: {os.getcwd()}")
    current_app.logger.debug(
        f"Does index.html exist: {os.path.exists('app/templates/index.html')}"
    )
    return render_template("index.html")

@main_bp.route("/upload", methods=["POST"])
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

@main_bp.route("/upload_folder", methods=["POST"])
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

@main_bp.route("/output/<path:filename>")
def send_file(filename):
    return send_from_directory(current_app.config["OUTPUT_FOLDER"], filename)