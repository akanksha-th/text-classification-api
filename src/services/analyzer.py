from src.models.sentiment import SentimentAnalyzer
from src.models.preprocessing import TextProcessor
from typing import List, Dict
import asyncio
import time

class AnalyzerService:
    """Orchestrates the comment analysis pipeline"""
    def __init__(self):
        self.preprocessor = TextProcessor()
        self.analyzer = SentimentAnalyzer()

    async def analyze_comments(self, video_id: str, comments: List[Dict]) -> Dict:
        """clean → analyze → aggregate"""
        start_time = time.time()
        
        if not comments:
            return self._empty_response(video_id)
        
        texts = [comment.get("text", "") for comment in comments]
        cleaned_texts = [self.preprocessor.clean(text) for text in texts]

        valid_texts = []
        valid_indices = []
        
        for i, cleaned in enumerate(cleaned_texts):
            if self.preprocessor.is_valid(cleaned):
                valid_texts.append(cleaned)
                valid_indices.append(i)
                
        if valid_texts:
            sentiments = await asyncio.to_thread(
                self.analyzer.analyze_batch, valid_texts
            )
        else:
            sentiments = []

        enriched_comments = []
        sentiment_idx = 0

        for i, comment in enumerate(comments):
            enriched = comment.copy()
            enriched["cleaned_text"] = cleaned_texts[i]

            if i in valid_indices and sentiment_idx < len(sentiments):
                enriched["sentiment"] = sentiments[sentiment_idx]["label"]
                enriched["confidence"] = sentiments[sentiment_idx]["confidence"]
                sentiment_idx += 1
            else:
                enriched["sentiment"] = "neutral"
                enriched["confidence"] = 0.0

            enriched_comments.append(enriched)

        distribution = self._calculate_distribution(enriched_comments)
        overall = self._get_overall_sentiment(distribution)
        avg_confidence = self._calculate_avg_confidence(enriched_comments)
        valid_count = len(valid_texts)
        
        processing_time_ms = int((time.time() - start_time) * 1000)

        return {
            "video_id": video_id,
            "total_comments": len(comments),
            "valid_comments": valid_count,
            "sentiment_distribution": distribution,
            "overall_sentiment": overall,
            "average_confidence": avg_confidence,
            "comments": enriched_comments,
            "processing_time_ms": processing_time_ms
        }
    
    def _calculate_distribution(self, comments: List[Dict]) -> Dict:
        total = len(comments)
        if total == 0:
            return {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
        
        pos_count = len([c for c in comments if c.get("sentiment") == "positive"])
        neg_count = len([c for c in comments if c.get("sentiment") == "negative"])
        neut_count = len([c for c in comments if c.get("sentiment") == "neutral"])

        pos_pct, neg_pct, neut_pct = pos_count/total *100, neg_count/total *100, neut_count/total *100
        
        return {
            "positive": round(pos_pct, 2),
            "negative": round(neg_pct, 2),
            "neutral": round(neut_pct, 2),
        }

    def _get_overall_sentiment(self, distribution: Dict) -> str:
        max_val = max(distribution.values())
        winners = [k for k, v in distribution.items() if v == max_val]
        if len(winners) > 1 or "neutral" in winners:
            return "neutral"
        return winners[0]


    def _calculate_avg_confidence(self, comments: List[Dict]) -> float:
        analyzed = [c for c in comments if c.get("confidence", 0.0) > 0.0]
        if not analyzed:
            return 0.0
        
        total_confidence = sum(c.get("confidence", 0.0) for c in analyzed)
        return round(total_confidence / len(analyzed), 4)
    
    def _empty_response(self, video_id: str) -> Dict:
        """Return empty response when no comments provided"""
        return {
            "video_id": video_id,
            "total_comments": 0,
            "valid_comments": 0,
            "sentiment_distribution": {
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 0.0
            },
            "overall_sentiment": "neutral",
            "average_confidence": 0.0,
            "comments": [],
            "processing_time_ms": 0
        }