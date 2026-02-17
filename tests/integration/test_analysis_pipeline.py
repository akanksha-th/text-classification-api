import pytest
import time
from src.models.preprocessing import TextProcessor
from src.models.sentiment import SentimentAnalyzer
from src.services.analyzer import AnalyzerService


class TestAnalysisPipeline:
    """Integration tests for the complete analysis pipeline"""
   
    def test_preprocess_and_sentiment_positive(self, services):
        text = "This is amazing! 😍"
        cleaned = services["preprocessor"].clean(text)
        result = services["sentiment"].analyze(cleaned)
        
        assert result["label"] == "positive"
        assert result["confidence"] > 0.7
    
    def test_preprocess_and_sentiment_negative(self, services):
        text = "This is terrible and awful"
        cleaned = services["preprocessor"].clean(text)
        result = services["sentiment"].analyze(cleaned)
        
        assert result["label"] == "negative"
        assert result["confidence"] > 0.7
    
    def test_preprocess_removes_url_before_sentiment(self, services):
        text = "Great video https://spam.com"
        cleaned = services["preprocessor"].clean(text)
        result = services["sentiment"].analyze(cleaned)
        
        assert "https://spam.com" not in cleaned
        assert "great video" in cleaned
        assert result["label"] == "positive"
    
    # ===== AnalyzerService Integration =====
    
    def test_analyzer_service_enriches_comments(self, services):
        comments = [
            {
                "author": "User1",
                "text": "Great!",
                "like_count": 10,
                "published_at": "2024-01-01",
                "updated_at": "2024-01-01"
            }
        ]
        
        result = services["analyzer"].analyze_comments("test_video_id", comments)
        
        assert result["total_comments"] == 1
        assert result["valid_comments"] == 1
        assert len(result["comments"]) == 1
        
        comment = result["comments"][0]
        assert "sentiment" in comment
        assert "confidence" in comment
        assert "cleaned_text" in comment
        assert comment["sentiment"] == "positive"
    
    def test_analyzer_service_handles_mixed_sentiments(self, services):
        comments = [
            {"author": "User1", "text": "Amazing!", "like_count": 10, "published_at": "2024-01-01", "updated_at": "2024-01-01"},
            {"author": "User2", "text": "Terrible", "like_count": 2, "published_at": "2024-01-02", "updated_at": "2024-01-02"},
            {"author": "User3", "text": "It is okay", "like_count": 5, "published_at": "2024-01-03", "updated_at": "2024-01-03"},
        ]
        
        result = services["analyzer"].analyze_comments("test_video_id", comments)
        
        assert result["total_comments"] == 3
        assert len(result["comments"]) == 3
        assert result["comments"][0]["sentiment"] == "positive"
        assert result["comments"][1]["sentiment"] == "negative"
        assert result["comments"][2]["sentiment"] in ["neutral", "positive", "negative"]
    
    def test_analyzer_service_filters_invalid_comments(self, services):
        comments = [
            {"author": "User1", "text": "https://only-url.com", "like_count": 0, "published_at": "2024-01-01", "updated_at": "2024-01-01"},
            {"author": "User2", "text": "   ", "like_count": 0, "published_at": "2024-01-02", "updated_at": "2024-01-02"},
        ]
        
        result = services["analyzer"].analyze_comments("test_video_id", comments)
        
        assert result["total_comments"] == 2
        assert result["valid_comments"] == 0
        assert len(result["comments"]) == 2
        assert result["comments"][0]["sentiment"] == "neutral"
        assert result["comments"][0]["confidence"] == 0.0
        assert result["comments"][1]["sentiment"] == "neutral"
        assert result["comments"][1]["confidence"] == 0.0
    
    def test_analyzer_service_preserves_original_data(self, services):
        comments = [
            {
                "author": "TestUser",
                "text": "Great!",
                "like_count": 42,
                "published_at": "2024-01-01",
                "updated_at": "2024-01-02"
            }
        ]
        
        result = services["analyzer"].analyze_comments("test_video_id", comments)
        comment = result["comments"][0]
        
        assert comment["author"] == "TestUser"
        assert comment["like_count"] == 42
        assert comment["published_at"] == "2024-01-01"
        assert comment["updated_at"] == "2024-01-02"
        assert "sentiment" in comment
        assert "confidence" in comment
        assert "cleaned_text" in comment
    
    def test_analyzer_service_handles_empty_list(self, services):
        result = services["analyzer"].analyze_comments("test_video_id", [])
        
        # ✅ Returns dict not list!
        assert result["total_comments"] == 0
        assert result["valid_comments"] == 0
        assert result["comments"] == []
        assert result["overall_sentiment"] == "neutral"
        assert result["video_id"] == "test_video_id"
    
    def test_analyzer_service_batch_performance(self, services):
        comments = [
            {
                "author": f"User{i}",
                "text": f"This is comment number {i} and it is great!",
                "like_count": i,
                "published_at": "2024-01-01",
                "updated_at": "2024-01-01"
            }
            for i in range(50)
        ]
        
        start = time.time()
        result = services["analyzer"].analyze_comments("test_video_id", comments)
        duration = time.time() - start
        
        assert result["total_comments"] == 50
        assert len(result["comments"]) == 50
        assert duration < 10.0
    
    # ===== Aggregation Tests =====
    
    def test_distribution_adds_to_100(self, services):
        comments = [
            {"author": f"User{i}", "text": "Great video!", "like_count": i, "published_at": "2024-01-01", "updated_at": "2024-01-01"}
            for i in range(10)
        ]
        
        result = services["analyzer"].analyze_comments("test_video_id", comments)
        dist = result["sentiment_distribution"]
        
        total = dist["positive"] + dist["negative"] + dist["neutral"]
        assert abs(total - 100.0) < 0.1, f"Distribution adds to {total:.2f}, expected 100%"
    
    def test_overall_sentiment_matches_dominant(self, services):
        comments = [
            {"author": "User1", "text": "Amazing!", "like_count": 1, "published_at": "2024-01-01", "updated_at": "2024-01-01"},
            {"author": "User2", "text": "Wonderful!", "like_count": 1, "published_at": "2024-01-01", "updated_at": "2024-01-01"},
            {"author": "User3", "text": "Fantastic!", "like_count": 1, "published_at": "2024-01-01", "updated_at": "2024-01-01"},
            {"author": "User4", "text": "Love it!", "like_count": 1, "published_at": "2024-01-01", "updated_at": "2024-01-01"},
            {"author": "User5", "text": "Terrible!", "like_count": 1, "published_at": "2024-01-01", "updated_at": "2024-01-01"},
        ]
        
        result = services["analyzer"].analyze_comments("test_video_id", comments)
        assert result["overall_sentiment"] == "positive"
    
    def test_video_id_in_response(self, services):
        comments = [
            {"author": "User1", "text": "Great!", "like_count": 1, "published_at": "2024-01-01", "updated_at": "2024-01-01"}
        ]
        
        result = services["analyzer"].analyze_comments("my_video_abc123", comments)
        assert result["video_id"] == "my_video_abc123"
    
    def test_processing_time_is_tracked(self, services):
        comments = [
            {"author": "User1", "text": "Great!", "like_count": 1, "published_at": "2024-01-01", "updated_at": "2024-01-01"}
        ]
        
        result = services["analyzer"].analyze_comments("test_video_id", comments)
        
        assert "processing_time_ms" in result
        assert result["processing_time_ms"] > 0
    
    def test_average_confidence_is_valid(self, services):
        comments = [
            {"author": "User1", "text": "Great video!", "like_count": 1, "published_at": "2024-01-01", "updated_at": "2024-01-01"},
            {"author": "User2", "text": "Terrible!", "like_count": 1, "published_at": "2024-01-01", "updated_at": "2024-01-01"},
        ]
        
        result = services["analyzer"].analyze_comments("test_video_id", comments)
        assert 0.0 <= result["average_confidence"] <= 1.0
