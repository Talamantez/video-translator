import pytest
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class MLResult:
    output: Any
    confidence: float

class MLComponent(ABC):
    @abstractmethod
    def process(self, input_data) -> MLResult:
        pass

class OCR(MLComponent):
    def process(self, input_data):
        return MLResult(f"OCR processed: {input_data}", 0.85)

class AudioRecognition(MLComponent):
    def process(self, input_data):
        return MLResult(f"Audio recognized: {input_data}", 0.78)

class ObjectRecognition(MLComponent):
    def process(self, input_data):
        return MLResult(f"Objects recognized in: {input_data}", 0.92)

class ImportantSentenceRecognition(MLComponent):
    def process(self, input_data):
        return MLResult(f"Important sentences in: {input_data}", 0.73)

class Translation(MLComponent):
    def process(self, input_data):
        return MLResult(f"Translated: {input_data}", 0.89)

@pytest.fixture
def test_harness():
    components = {
        "OCR": OCR(),
        "AudioRecognition": AudioRecognition(),
        "ObjectRecognition": ObjectRecognition(),
        "ImportantSentenceRecognition": ImportantSentenceRecognition(),
        "Translation": Translation()
    }
    return components

def format_confidence(confidence: float) -> str:
    if confidence >= 0.9:
        return f"High ({confidence:.2f})"
    elif confidence >= 0.7:
        return f"Medium ({confidence:.2f})"
    else:
        return f"Low ({confidence:.2f})"

def display_results(results: Dict[str, MLResult]) -> str:
    output = "ML Pipeline Results:\n"
    output += "=" * 50 + "\n\n"
    
    for component, result in results.items():
        output += f"{component}:\n"
        output += f"  Result: {result.output}\n"
        output += f"  Confidence: {format_confidence(result.confidence)}\n\n"
    
    overall_confidence = sum(r.confidence for r in results.values()) / len(results)
    output += "=" * 50 + "\n"
    output += f"Overall Confidence: {format_confidence(overall_confidence)}\n"
    output += "=" * 50 + "\n"
    return output

def test_user_friendly_display(test_harness):
    results = {}
    for component_name, component in test_harness.items():
        results[component_name] = component.process(f"sample input for {component_name}")
    
    user_display = display_results(results)
    print("\nUser-Friendly Display of ML Results:")
    print(user_display)
    
    assert "ML Pipeline Results:" in user_display
    assert "Overall Confidence:" in user_display
    for component_name in test_harness.keys():
        assert component_name in user_display
        assert "Result:" in user_display
        assert "Confidence:" in user_display

def test_ocr(test_harness):
    result = test_harness["OCR"].process("sample image")
    assert result.output == "OCR processed: sample image"
    assert 0 <= result.confidence <= 1

def test_audio_recognition(test_harness):
    result = test_harness["AudioRecognition"].process("sample audio")
    assert result.output == "Audio recognized: sample audio"
    assert 0 <= result.confidence <= 1

def test_object_recognition(test_harness):
    result = test_harness["ObjectRecognition"].process("sample video frame")
    assert result.output == "Objects recognized in: sample video frame"
    assert 0 <= result.confidence <= 1

def test_important_sentence_recognition(test_harness):
    result = test_harness["ImportantSentenceRecognition"].process("sample text")
    assert result.output == "Important sentences in: sample text"
    assert 0 <= result.confidence <= 1

def test_translation(test_harness):
    result = test_harness["Translation"].process("sample text")
    assert result.output == "Translated: sample text"
    assert 0 <= result.confidence <= 1

def test_all_components_with_confidence(test_harness):
    for component_name, component in test_harness.items():
        result = component.process(f"sample input for {component_name}")
        print(f"{component_name}: {result.output} (Confidence: {result.confidence:.2f})")
        assert isinstance(result, MLResult)
        assert isinstance(result.output, str)
        assert isinstance(result.confidence, float)
        assert 0 <= result.confidence <= 1

if __name__ == "__main__":
    test_harness_instance = test_harness()
    results = {name: component.process(f"sample input for {name}") 
               for name, component in test_harness_instance.items()}
    print(display_results(results))