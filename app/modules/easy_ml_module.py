import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer as WordWeigher
from sklearn.naive_bayes import MultinomialNB as PatternSpotter
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

class EasyTextSorter:
    def __init__(self):
        self.sorter = Pipeline([
            ('weigh_words', WordWeigher()),
            ('spot_patterns', PatternSpotter())
        ])
        self.memory_file = 'text_sorter_memory.joblib'

    def learn_patterns(self, texts, categories):
        """Teach the sorter to recognize text patterns."""
        practice_texts, test_texts, practice_categories, test_categories = train_test_split(
            texts, categories, test_size=0.2, random_state=42
        )
        
        self.sorter.fit(practice_texts, practice_categories)
        
        test_guesses = self.sorter.predict(test_texts)
        print("How well our sorter learned:")
        print(classification_report(test_categories, test_guesses))

        joblib.dump(self.sorter, self.memory_file)
        print(f"Sorter's memory saved to {self.memory_file}")

    def sort_text(self, new_texts):
        """Sort new texts into categories."""
        if not hasattr(self, 'sorter'):
            self.sorter = joblib.load(self.memory_file)
        
        guessed_categories = self.sorter.predict(new_texts)
        confidence_levels = self.sorter.predict_proba(new_texts)
        
        results = []
        for category, confidence in zip(guessed_categories, confidence_levels):
            how_sure = np.max(confidence)
            results.append({'category': category, 'confidence': how_sure})
        
        return results

# Example usage
if __name__ == "__main__":
    # Sample data
    texts = [
        "I love this video", "This content is terrible",
        "Neutral opinion about this", "Amazing editing skills",
        "Boring and uninteresting"
    ]
    categories = ["positive", "negative", "neutral", "positive", "negative"]

    sorter = EasyTextSorter()
    
    # Teach the sorter
    sorter.learn_patterns(texts, categories)
    
    # Try sorting new texts
    new_texts = ["This video is awesome", "I didn't like the content"]
    results = sorter.sort_text(new_texts)
    
    for text, result in zip(new_texts, results):
        print(f"Text: '{text}'")
        print(f"Guessed category: {result['category']}")
        print(f"How sure: {result['confidence']:.2f}")
        print()