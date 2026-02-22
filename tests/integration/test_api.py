from fastapi import status
from unittest.mock import AsyncMock, patch, MagicMock
import pytest


# ── Helpers ──────────────────────────────────────────────────────────────────

VALID_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
VALID_VIDEO_ID = "dQw4w9WgXcQ"

MOCK_ANALYSIS_RESULT = {
    "video_id": VALID_VIDEO_ID,
    "total_comments": 2,
    "valid_comments": 2,
    "sentiment_distribution": {"positive": 50.0, "negative": 25.0, "neutral": 25.0},
    "overall_sentiment": "positive",
    "average_confidence": 0.91,
    "comments": [
        {
            "author": "User1",
            "text": "Great!",
            "cleaned_text": "great!",
            "like_count": 5,
            "published_at": "2024-01-01",
            "updated_at": "2024-01-01",
            "sentiment": "positive",
            "confidence": 0.95,
        },
        {
            "author": "User2",
            "text": "Terrible",
            "cleaned_text": "terrible",
            "like_count": 1,
            "published_at": "2024-01-02",
            "updated_at": "2024-01-02",
            "sentiment": "negative",
            "confidence": 0.87,
        },
    ],
    "processing_time_ms": 120,
    "cached": False,
    "source": "api",
}


# ── Shared fixture: mock the Redis client that dependencies.py holds ──────────
#
# dependencies.py does `cache_service = CacheService()` at module level.
# Patching the attribute on that already-created instance is the only reliable
# way to intercept calls — patching the class constructor is too late.

@pytest.fixture
def mock_redis():
    """
    Patch the redis_server on the module-level cache_service singleton
    that the rate_limiter dependency uses.
    """
    mock = MagicMock()
    mock.incr = AsyncMock(return_value=1)
    mock.expire = AsyncMock(return_value=True)
    with patch("src.api.dependencies.cache_service.redis_server", mock):
        yield mock


# ── Infrastructure ────────────────────────────────────────────────────────────

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "version" in data
    assert "docs" in data


# ── /api/v1/analyze — Input Validation ───────────────────────────────────────
#
# Pydantic rejects these before hitting any service, BUT the rate_limiter
# dependency still runs first (it's wired via Depends on the router).
# So we still need the Redis mock even for 422 tests.

class TestAnalyzeValidation:

    def test_missing_body_returns_422(self, client, mock_redis):
        response = client.post("/api/v1/analyze")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_missing_video_url_returns_422(self, client, mock_redis):
        response = client.post("/api/v1/analyze", json={"max_comments": 100})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_youtube_url_returns_422(self, client, mock_redis):
        response = client.post(
            "/api/v1/analyze",
            json={"video_url": "https://notyoutube.com/watch?v=abc123"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_url_without_scheme_returns_422(self, client, mock_redis):
        response = client.post(
            "/api/v1/analyze",
            json={"video_url": "youtube.com/watch?v=dQw4w9WgXcQ"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_max_comments_too_low_returns_422(self, client, mock_redis):
        response = client.post(
            "/api/v1/analyze",
            json={"video_url": VALID_URL, "max_comments": 0}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_max_comments_too_high_returns_422(self, client, mock_redis):
        response = client.post(
            "/api/v1/analyze",
            json={"video_url": VALID_URL, "max_comments": 999999}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ── /api/v1/analyze — Happy Path ─────────────────────────────────────────────

class TestAnalyzeSuccess:

    @pytest.fixture(autouse=True)
    def mock_all(self, mock_redis):
        """Patch all external I/O so tests are fast and deterministic."""
        with (
            patch("src.api.routes.analyze.cache_service.get", new_callable=AsyncMock, return_value=None),
            patch("src.api.routes.analyze.cache_service.set", new_callable=AsyncMock, return_value=True),
            patch(
                "src.api.routes.analyze.youtube_service.get_comments",
                new_callable=AsyncMock,
                return_value={"comments": MOCK_ANALYSIS_RESULT["comments"], "total": 2},
            ),
            patch(
                "src.api.routes.analyze.analyzer_service.analyze_comments",
                new_callable=AsyncMock,
                return_value=MOCK_ANALYSIS_RESULT.copy(),
            ),
        ):
            yield

    def test_returns_200(self, client):
        response = client.post("/api/v1/analyze", json={"video_url": VALID_URL})
        assert response.status_code == status.HTTP_200_OK

    def test_response_shape(self, client):
        response = client.post("/api/v1/analyze", json={"video_url": VALID_URL})
        data = response.json()
        required_keys = {
            "video_id", "total_comments", "valid_comments",
            "sentiment_distribution", "overall_sentiment",
            "average_confidence", "comments", "processing_time_ms",
            "cached", "source",
        }
        assert required_keys.issubset(data.keys())

    def test_video_id_in_response(self, client):
        response = client.post("/api/v1/analyze", json={"video_url": VALID_URL})
        assert response.json()["video_id"] == VALID_VIDEO_ID

    def test_sentiment_distribution_adds_to_100(self, client):
        response = client.post("/api/v1/analyze", json={"video_url": VALID_URL})
        dist = response.json()["sentiment_distribution"]
        total = dist["positive"] + dist["negative"] + dist["neutral"]
        assert abs(total - 100.0) < 0.1

    def test_cached_false_on_fresh_request(self, client):
        response = client.post("/api/v1/analyze", json={"video_url": VALID_URL})
        assert response.json()["cached"] is False

    def test_source_is_api_on_fresh_request(self, client):
        response = client.post("/api/v1/analyze", json={"video_url": VALID_URL})
        assert response.json()["source"] == "api"

    def test_default_max_comments_accepted(self, client):
        """Omitting max_comments should use the default and not error."""
        response = client.post("/api/v1/analyze", json={"video_url": VALID_URL})
        assert response.status_code == status.HTTP_200_OK

    def test_youtu_be_short_url_accepted(self, client):
        response = client.post(
            "/api/v1/analyze",
            json={"video_url": "https://youtu.be/dQw4w9WgXcQ"}
        )
        assert response.status_code == status.HTTP_200_OK


# ── /api/v1/analyze — Cache Hit ──────────────────────────────────────────────

class TestAnalyzeCacheHit:

    @pytest.fixture(autouse=True)
    def mock_cache_hit(self, mock_redis):
        cached = {**MOCK_ANALYSIS_RESULT, "cached": True, "source": "cache"}
        with patch("src.api.routes.analyze.cache_service.get", new_callable=AsyncMock, return_value=cached):
            yield

    def test_cached_true_on_cache_hit(self, client):
        response = client.post("/api/v1/analyze", json={"video_url": VALID_URL})
        assert response.json()["cached"] is True

    def test_source_is_cache_on_cache_hit(self, client):
        response = client.post("/api/v1/analyze", json={"video_url": VALID_URL})
        assert response.json()["source"] == "cache"


# ── /api/v1/analyze — Upstream Errors ────────────────────────────────────────

class TestAnalyzeErrors:

    def test_youtube_video_not_found_returns_404(self, client, mock_redis):
        with (
            patch("src.api.routes.analyze.cache_service.get", new_callable=AsyncMock, return_value=None),
            patch(
                "src.api.routes.analyze.youtube_service.get_comments",
                new_callable=AsyncMock,
                side_effect=ValueError("Video not found: dQw4w9WgXcQ"),
            ),
        ):
            response = client.post("/api/v1/analyze", json={"video_url": VALID_URL})
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_youtube_api_failure_returns_503(self, client, mock_redis):
        with (
            patch("src.api.routes.analyze.cache_service.get", new_callable=AsyncMock, return_value=None),
            patch(
                "src.api.routes.analyze.youtube_service.get_comments",
                new_callable=AsyncMock,
                side_effect=Exception("quota exceeded"),
            ),
        ):
            response = client.post("/api/v1/analyze", json={"video_url": VALID_URL})
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_analyzer_failure_returns_500(self, client, mock_redis):
        with (
            patch("src.api.routes.analyze.cache_service.get", new_callable=AsyncMock, return_value=None),
            patch(
                "src.api.routes.analyze.youtube_service.get_comments",
                new_callable=AsyncMock,
                return_value={"comments": [], "total": 0},
            ),
            patch(
                "src.api.routes.analyze.analyzer_service.analyze_comments",
                new_callable=AsyncMock,
                side_effect=Exception("model crashed"),
            ),
        ):
            response = client.post("/api/v1/analyze", json={"video_url": VALID_URL})
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# ── /api/v1/analyze — Rate Limiting ──────────────────────────────────────────

class TestRateLimiting:

    def test_rate_limit_exceeded_returns_429(self, client):
        mock = MagicMock()
        mock.incr = AsyncMock(return_value=11)  # limit is 10
        mock.expire = AsyncMock(return_value=True)
        with patch("src.api.dependencies.cache_service.redis_server", mock):
            response = client.post("/api/v1/analyze", json={"video_url": VALID_URL})
            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_rate_limit_response_has_retry_after_header(self, client):
        mock = MagicMock()
        mock.incr = AsyncMock(return_value=11)
        mock.expire = AsyncMock(return_value=True)
        with patch("src.api.dependencies.cache_service.redis_server", mock):
            response = client.post("/api/v1/analyze", json={"video_url": VALID_URL})
            assert "retry-after" in response.headers