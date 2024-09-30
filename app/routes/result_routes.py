from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json

result_bp = Blueprint('result', __name__)

@result_bp.route("/save_result", methods=["POST"])
def save_result():
    data = request.json
    result_name = secure_filename(data["name"])
    result_data = data["data"]

    # Add source URL and access time
    result_data["source_url"] = data.get("source_url", "")
    result_data["access_time"] = datetime.now().isoformat()

    file_path = os.path.join(
        current_app.config["SAVED_RESULTS_FOLDER"], f"{result_name}.json"
    )

    with open(file_path, "w") as f:
        json.dump(result_data, f)

    return jsonify({"message": f"Result saved as {result_name}"})


@result_bp.route("/load_result/<result_name>", methods=["GET"])
def load_result(result_name):
    file_path = os.path.join(
        current_app.config["SAVED_RESULTS_FOLDER"], f"{result_name}.json"
    )

    if not os.path.exists(file_path):
        return jsonify({"error": "Result not found"}), 404

    with open(file_path, "r") as f:
        result_data = json.load(f)

    # Update access time
    result_data["access_time"] = datetime.now().isoformat()

    with open(file_path, "r") as f:
        result_data = json.load(f)

    return jsonify(result_data)


@result_bp.route("/list_saved_results", methods=["GET"])
def list_saved_results():
    saved_results = [
        f.replace(".json", "")
        for f in os.listdir(current_app.config["SAVED_RESULTS_FOLDER"])
        if f.endswith(".json")
    ]
    return jsonify(saved_results)


@result_bp.route("/delete_result/<result_name>", methods=["DELETE"])
def delete_result(result_name):
    file_path = os.path.join(
        current_app.config["SAVED_RESULTS_FOLDER"], f"{result_name}.json"
    )

    if not os.path.exists(file_path):
        return jsonify({"error": "Result not found"}), 404

    try:
        os.remove(file_path)
        return jsonify({"message": f"Result {result_name} deleted successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to delete result: {str(e)}"}), 500
