from transformers import pipeline
from src.core.config import get_settings
from typing import Dict

settings = get_settings()


class SentimentAnalyzer:
    """Sentiment analyzer for social media comments"""
    MAX_LENGTH = 512
    
    def __init__(self):
        self.model = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            device=-1,   # CPU
            batch_size=settings.BATCH_SIZE,
            truncation=True,  
            max_length=self.MAX_LENGTH
        )

    def analyze(self, text: str) -> Dict[str, any]:
        """Analyze sentiment of a single text"""
        if not text or not isinstance(text, str):
            return {
                "label": "neutral",
                "confidence": 0.0
            }
        
        text = self._truncate(text)
        result = self.model(text)[0]
        return {
            "label": result["label"],
            "confidence": round(result["score"], 4)
        }

    def analyze_batch(self, texts: list[str]) -> list[dict]:
        """Batch processing for sentiment analysis"""
        if not texts:
            return []
        
        valid_texts = []
        valid_indices = []

        for i, text in enumerate(texts):
            if text and isinstance(text, str) and text.strip():
                valid_texts.append(self._truncate(text))
                valid_indices.append(i)

        if not valid_texts:
            return [
                {"label": "neutral", "confidence": 0.0} 
                for _ in texts
            ]
        
        results = self.model(valid_texts)
        output = [{"label": "neutral", "confidence": 0.0} for _ in texts]

        for valid_idx, result in zip(valid_indices, results):
            output[valid_idx] = {
                "label": result["label"],
                "confidence": round(result["score"], 4)
            }

        return output
    
    def _truncate(self, text: str) -> str:
        """
        Truncate text to prevent exceeding model's max token length.
        RoBERTa ~= 1 token per word on average for social media text.
        We use 400 words as safe limit (well under 512 tokens).
        """
        words = text.split()
        if len(words) > 400:
            return ' '.join(words[:400])
        return text
    

if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    print("\nTesting batch analysis:")
    
    batch_texts = [
        "Great video!",
        "Terrible content",
        "kinda mid",
        "",
        "I have doubts over a few things",
        "that movie was wayyyyyy too mid",
        "😎😎😎",
        ":smiling_face_with_sunglasses:"
    ]
    
    import time
    start = time.time()
    results = analyzer.analyze_batch(batch_texts)
    duration = time.time() - start
    
    print(f"Processed {len(batch_texts)} texts in {duration:.2f} seconds")
    
    for text, result in zip(batch_texts, results):
        print(f"Text: '{text:30s}' → {result['label']:8s} ({result['confidence']:.2f})")
