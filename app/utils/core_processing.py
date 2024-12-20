# app/utils/core_processing.py

import os
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Union

from .audio_processing import extract_audio, speech_to_text
from .text_processing import ocr_from_video, translate_text, extract_meaningful_content
from .image_processing import recognize_images_in_video
from summa import keywords


class VideoProcessor:
    """Core processing functionality for video analysis."""

    @staticmethod
    def process_clip(clip, output_folder, target_language, url):
        """Process a single video clip with audio, OCR, and object detection."""
        logging.info(f"Processing clip: {clip}")
        clip_path = os.path.join(output_folder, clip["filename"])
        audio_path = os.path.join(output_folder, f"{clip['filename']}.wav")

        # Audio processing
        audio_extracted = extract_audio(clip_path, audio_path)
        logging.info(f"Audio extracted: {audio_extracted}")

        if audio_extracted:
            speech_text = speech_to_text(audio_path)
        else:
            speech_text = "Audio extraction failed. No speech recognition performed."
        logging.info(f"Speech text: {speech_text[:100]}...")

        # OCR processing - handle as string for now
        ocr_text = ocr_from_video(clip_path)
        logging.info(f"OCR text: {ocr_text[:100]}...")

        # Image recognition
        try:
            image_recognition_results = recognize_images_in_video(clip_path)
            detections = image_recognition_results.get('detections', [])
            classifications = image_recognition_results.get('classifications', [])
            
            if detections:
                logging.info(f"Detected objects (first 3): {detections[:3]}")
            if classifications:
                logging.info(f"Scene classifications (first 3): {classifications[:3]}")
        except Exception as e:
            logging.error(f"Error in image recognition: {str(e)}")
            image_recognition_results = {'detections': [], 'classifications': []}

        # Translation
        speech_translated = translate_text(speech_text, target_language) if speech_text else "No speech to translate."
        ocr_translated = translate_text(ocr_text, target_language) if ocr_text else "No OCR text to translate."

        # Content analysis
        combined_text = f"{speech_text} {ocr_text}".strip()
        if combined_text:
            summary = extract_meaningful_content(combined_text, f"{speech_translated} {ocr_translated}", target_language)
        else:
            summary = {"error": "No meaningful content found"}
        logging.info("Translation and summary complete")

        # Generate clip name
        clip_name = VideoProcessor.generate_clip_name(speech_text, ocr_text, image_recognition_results)
        logging.info(f"Generated clip name: {clip_name}")

        # Cleanup
        if os.path.exists(audio_path):
            os.remove(audio_path)
            logging.info(f"Removed temporary audio file: {audio_path}")

        return {
            **clip,
            "clip_name": clip_name,
            "speech_text": speech_text,
            "ocr_text": ocr_text,
            "speech_translated": speech_translated,
            "ocr_translated": ocr_translated,
            "summary": summary,
            "image_recognition": image_recognition_results,
            "source_url": url,
            "access_time": datetime.now().isoformat(),
        }
    
    @staticmethod
    def generate_clip_name(
        speech_text: str, ocr_text: str, image_recognition_results: Dict
    ) -> str:
        """Generate a meaningful name for the clip."""
        all_text = f"{speech_text} {ocr_text}"
        all_text = re.sub(r"[^\w\s]", "", all_text).strip()

        if len(all_text) < 10:
            return "short_clip"

        try:
            text_phrases = keywords.keywords(all_text).split("\n")[:3]

            detections = image_recognition_results.get("detections", [])
            classifications = image_recognition_results.get("classifications", [])

            visual_elements = [det["class"] for det in detections[:2]] + [
                cls["label"] for cls in classifications[:2]
            ]

            all_phrases = text_phrases + visual_elements
            if not all_phrases:
                return "unnamed_clip"

            clip_name = "_".join(filter(None, all_phrases))
            return clip_name[:50].lower().replace(" ", "_")

        except Exception as e:
            logging.warning(f"Keyword extraction failed: {str(e)}")
            words = all_text.split()[:3]
            return "_".join(words)[:50].lower() if words else "unnamed_clip"

    @staticmethod
    def update_running_summary(current_summary: Optional[Dict] = None, 
                             new_clip_data: Optional[Dict] = None) -> Dict:
        """
        Update the running summary with new clip data.
        Now the single source of truth for summary updates.
        """
        if not current_summary:
            current_summary = {
                "key_phrases": [],
                "entities": [],
                "recognized_objects": [],
                "important_sentences": [],
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "clip_count": 0
                }
            }

        try:
            # Update metadata
            current_summary["metadata"]["last_updated"] = datetime.now().isoformat()
            current_summary["metadata"]["clip_count"] += 1

            # Update key phrases from summary
            if "summary" in new_clip_data and "key_phrases" in new_clip_data["summary"]:
                current_summary["key_phrases"].extend(new_clip_data["summary"]["key_phrases"])
                current_summary["key_phrases"] = list(set(current_summary["key_phrases"]))[:10]

            # Update main entities
            if "summary" in new_clip_data and "entities" in new_clip_data["summary"]:
                current_summary["entities"].extend(new_clip_data["summary"]["entities"])
                current_summary["entities"] = list(set(current_summary["entities"]))[:10]

            # Update recognized objects from detections
            if "image_recognition" in new_clip_data:
                new_objects = []
                # Get objects from detections
                detections = new_clip_data["image_recognition"].get("detections", [])
                for det in detections:
                    if det.get("confidence", 0) > 0.5:  # High confidence threshold
                        new_objects.append(det.get("class", ""))
                
                # Get objects from classifications
                classifications = new_clip_data["image_recognition"].get("classifications", [])
                for cls in classifications:
                    if cls.get("confidence", 0) > 0.3:  # Lower threshold for classifications
                        new_objects.append(cls.get("label", ""))

                current_summary["recognized_objects"].extend(new_objects)
                current_summary["recognized_objects"] = list(set(current_summary["recognized_objects"]))[:10]

            # Update important sentences
            if "summary" in new_clip_data and "important_sentences" in new_clip_data["summary"]:
                new_sentences = new_clip_data["summary"].get("important_sentences", [])
                current_summary["important_sentences"].extend(new_sentences)
                current_summary["important_sentences"] = list(set(current_summary["important_sentences"]))[:20]

            logging.info(f"Updated summary - Objects: {len(current_summary['recognized_objects'])} total")

        except Exception as e:
            logging.error(f"Error updating summary: {str(e)}", exc_info=True)
            return current_summary

        return current_summary