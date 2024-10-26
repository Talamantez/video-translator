from .audio_processing_routes import extract_audio, speech_to_text
from .text_processing_routes import ocr_from_video, translate_text, extract_meaningful_content
from .image_processing_routes import recognize_images_in_video
from datetime import datetime
import os
import logging


def update_running_summary(current_summary, new_clip_data):
    if not current_summary:
        current_summary = {
            "key_topics": [],
            "main_entities": [],
            "recognized_objects": [],
            "important_sentences": [],
        }

    # Update key topics
    if "summary" in new_clip_data and "key_phrases" in new_clip_data["summary"]:
        current_summary["key_topics"].extend(new_clip_data["summary"]["key_phrases"])
        current_summary["key_topics"] = list(set(current_summary["key_topics"]))[:10]  # Keep top 10 unique topics

    # Update main entities
    if "summary" in new_clip_data and "entities" in new_clip_data["summary"]:
        current_summary["main_entities"].extend(new_clip_data["summary"]["entities"])
        current_summary["main_entities"] = list(set(current_summary["main_entities"]))[:10]  # Keep top 10 unique entities

    # Update recognized objects
    if "image_recognition" in new_clip_data:
        new_objects = [obj["label"] for obj in new_clip_data["image_recognition"][:3]]  # Top 3 objects from new clip
        current_summary["recognized_objects"].extend(new_objects)
        current_summary["recognized_objects"] = list(set(current_summary["recognized_objects"]))[:10]  # Keep top 10 unique objects

    # Update important sentences
    if "summary" in new_clip_data and "important_sentences" in new_clip_data["summary"]:
        new_sentences = new_clip_data["summary"].get("important_sentences", [])
        current_summary["important_sentences"].extend(new_sentences)
        current_summary["important_sentences"] = list(set(current_summary["important_sentences"]))[:20]  # Keep top 20 unique sentences

    return current_summary
