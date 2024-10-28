# app/routes/summary_routes.py

from datetime import datetime
import os
import logging
from flask import Blueprint, jsonify, request
from typing import Dict, List, Union

summary_bp = Blueprint('summary', __name__)

class SummaryManager:
    """Manages video processing summaries and updates."""
    
    @staticmethod
    def update_running_summary(
        current_summary: Dict = None,
        new_clip_data: Dict = None
    ) -> Dict:
        """
        Update the running summary with new clip data.
        
        Args:
            current_summary: Current accumulated summary dict
            new_clip_data: New clip data to incorporate
        
        Returns:
            Updated summary dictionary
        """
        if current_summary is None:
            current_summary = {
                "key_topics": [],
                "main_entities": [],
                "recognized_objects": [],
                "important_sentences": [],
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "clip_count": 0,
                }
            }

        try:
            # Update metadata
            current_summary["metadata"]["last_updated"] = datetime.now().isoformat()
            current_summary["metadata"]["clip_count"] += 1

            # Update key topics
            if "summary" in new_clip_data and "key_phrases" in new_clip_data["summary"]:
                current_summary["key_topics"].extend(new_clip_data["summary"]["key_phrases"])
                current_summary["key_topics"] = list(set(current_summary["key_topics"]))[:10]
                logging.debug(f"Added key topics: {new_clip_data['summary']['key_phrases']}")

            # Update main entities
            if "summary" in new_clip_data and "entities" in new_clip_data["summary"]:
                current_summary["main_entities"].extend(new_clip_data["summary"]["entities"])
                current_summary["main_entities"] = list(set(current_summary["main_entities"]))[:10]
                logging.debug(f"Added entities: {new_clip_data['summary']['entities']}")

            # Update recognized objects from image recognition
            if "image_recognition" in new_clip_data:
                image_recog = new_clip_data["image_recognition"]
                
                # Handle detections
                if "detections" in image_recog:
                    new_detections = [
                        {
                            "label": det["class"],
                            "confidence": det["confidence"],
                            "timestamp": det.get("timestamp", 0)
                        }
                        for det in image_recog["detections"]
                        if det.get("confidence", 0) > 0.5
                    ]
                    if "detected_objects" not in current_summary:
                        current_summary["detected_objects"] = []
                    current_summary["detected_objects"].extend(new_detections)
                    logging.debug(f"Added {len(new_detections)} new detections")

                # Handle classifications
                if "classifications" in image_recog:
                    new_classifications = [
                        {
                            "label": cls["label"],
                            "confidence": cls["confidence"]
                        }
                        for cls in image_recog["classifications"]
                        if cls.get("confidence", 0) > 0.3
                    ]
                    if "scene_classifications" not in current_summary:
                        current_summary["scene_classifications"] = []
                    current_summary["scene_classifications"].extend(new_classifications)
                    logging.debug(f"Added {len(new_classifications)} new classifications")

                # Update simple recognized_objects list
                all_objects = [det["label"] for det in current_summary.get("detected_objects", [])]
                all_objects.extend(cls["label"] for cls in current_summary.get("scene_classifications", []))
                current_summary["recognized_objects"] = list(set(all_objects))[:10]

            # Update important sentences
            if "summary" in new_clip_data and "important_sentences" in new_clip_data["summary"]:
                new_sentences = new_clip_data["summary"].get("important_sentences", [])
                if not isinstance(current_summary.get("important_sentences"), list):
                    current_summary["important_sentences"] = []
                current_summary["important_sentences"].extend(new_sentences)
                current_summary["important_sentences"] = list(set(current_summary["important_sentences"]))[:20]
                logging.debug(f"Added {len(new_sentences)} new sentences")

            logging.info(f"Summary updated: {len(current_summary['recognized_objects'])} objects, "
                        f"{len(current_summary['key_topics'])} topics")

        except Exception as e:
            logging.error(f"Error updating summary: {str(e)}", exc_info=True)
            return current_summary

        return current_summary

    @staticmethod
    def get_summary_stats(summary: Dict) -> Dict:
        """Get statistics about the current summary."""
        return {
            "clip_count": summary.get("metadata", {}).get("clip_count", 0),
            "total_topics": len(summary.get("key_topics", [])),
            "total_entities": len(summary.get("main_entities", [])),
            "total_objects": len(summary.get("recognized_objects", [])),
            "total_sentences": len(summary.get("important_sentences", [])),
            "last_updated": summary.get("metadata", {}).get("last_updated", None),
        }

# API Routes
@summary_bp.route("/summary/stats", methods=["GET"])
def get_stats():
    """Get current summary statistics."""
    summary_id = request.args.get("summary_id")
    try:
        # Fetch summary from your storage
        summary = {}  # Replace with actual summary fetch
        stats = SummaryManager.get_summary_stats(summary)
        return jsonify(stats)
    except Exception as e:
        logging.error(f"Error getting summary stats: {str(e)}")
        return jsonify({"error": str(e)}), 500

@summary_bp.route("/summary", methods=["POST"])
def update_summary():
    """Update summary with new clip data."""
    try:
        data = request.json
        current_summary = data.get("current_summary", {})
        new_clip_data = data.get("new_clip_data", {})
        
        updated_summary = SummaryManager.update_running_summary(
            current_summary,
            new_clip_data
        )
        
        return jsonify(updated_summary)
    except Exception as e:
        logging.error(f"Error in summary update: {str(e)}")
        return jsonify({"error": str(e)}), 500