# app/routes/upload_routes.py

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
from http import HTTPStatus

upload_bp = Blueprint('upload', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@upload_bp.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload with improved validation and error handling."""
    try:
        if "file" not in request.files:
            return jsonify({
                "error": "No file part"
            }), HTTPStatus.BAD_REQUEST

        file = request.files["file"]
        if not file.filename:
            return jsonify({
                "error": "No selected file"
            }), HTTPStatus.BAD_REQUEST

        if not allowed_file(file.filename):
            return jsonify({
                "error": "File type not allowed",
                "allowed_types": list(current_app.config['ALLOWED_EXTENSIONS'])
            }), HTTPStatus.BAD_REQUEST

        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        
        # Check if file already exists
        if os.path.exists(filepath):
            filename = f"{os.path.splitext(filename)[0]}_{os.urandom(4).hex()}{os.path.splitext(filename)[1]}"
            filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

        file.save(filepath)
        
        # Get video duration using video service
        duration = current_app.video_service.get_video_info(filepath)[2]

        return jsonify({
            "filename": filename,
            "duration": duration,
            "size": os.path.getsize(filepath)
        })

    except Exception as e:
        current_app.logger.error(f"Upload error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Error uploading file",
            "details": str(e)
        }), HTTPStatus.INTERNAL_SERVER_ERROR