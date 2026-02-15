from transformers import pipeline
import onnxruntime as ort

class SentimentAnalyzer:
    def __init__(self):
        self.model = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            device=-1,   # CPU
            batch_size=32
        )

    def analyze_batch(self, texts: list[str]) -> list[dict]:
        ...