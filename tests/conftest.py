import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.models.preprocessing import TextProcessor
from src.models.sentiment import SentimentAnalyzer
from src.services.analyzer import AnalyzerService


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(scope="session")
def services():
    """
    Create all services ONCE for the entire test session.
    scope="session" = loaded once, shared across ALL test files.
    Perfect for expensive ML model loading.
    """
    return {
        "preprocessor": TextProcessor(),
        "sentiment": SentimentAnalyzer(),
        "analyzer": AnalyzerService()
    }