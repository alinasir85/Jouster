import os
import sys
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import get_db, Base
from app.services import TextProcessor

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Sample test data
SAMPLE_TEXT = """
Artificial Intelligence is transforming the technology landscape. 
Machine learning algorithms are becoming increasingly sophisticated, 
enabling computers to perform tasks that were once thought to be 
exclusively human. The future of AI looks promising with applications 
in healthcare, finance, and education.
"""


class TestAPI:
    """Test suite for the LLM Knowledge Extractor API."""

    def test_root_endpoint(self):
        """Test the root endpoint returns HTML for web UI."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "LLM Knowledge Extractor" in response.text

    def test_api_endpoint(self):
        """Test the /api endpoint returns API information."""
        response = client.get("/api")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data

    def test_analyze_empty_input(self):
        """Test that empty input is properly rejected."""
        response = client.post("/analyze", json={"text": ""})
        assert response.status_code == 422

        response = client.post("/analyze", json={"text": "   "})
        assert response.status_code == 422

    @patch('app.api.routes.get_llm_service')
    def test_analyze_success(self, mock_get_llm_service):
        """Test successful text analysis."""
        # Mock LLM service
        mock_llm = MagicMock()
        mock_get_llm_service.return_value = mock_llm
        
        # Mock LLM response
        mock_llm.analyze_text.return_value = {
            "summary": "AI is transforming technology through machine learning.",
            "title": "AI and Machine Learning",
            "topics": ["artificial intelligence", "machine learning", "technology"],
            "sentiment": "positive"
        }

        response = client.post("/analyze", json={"text": SAMPLE_TEXT})
        assert response.status_code == 200

        data = response.json()
        assert "id" in data
        assert data["summary"] == "AI is transforming technology through machine learning."
        assert data["sentiment"] == "positive"
        assert len(data["topics"]) == 3
        assert len(data["keywords"]) == 3
        assert data["confidence_score"] is not None

    @patch('app.api.routes.get_llm_service')
    def test_analyze_llm_failure(self, mock_get_llm_service):
        """Test graceful handling of LLM API failure."""
        # Mock LLM service to raise exception
        mock_llm = MagicMock()
        mock_get_llm_service.return_value = mock_llm
        mock_llm.analyze_text.side_effect = Exception("API Error")

        response = client.post("/analyze", json={"text": SAMPLE_TEXT})
        assert response.status_code == 200

        data = response.json()
        assert "error" in data["summary"].lower() or "failed" in data["summary"].lower()
        assert data["sentiment"] == "neutral"
        assert data["topics"] == ["error", "processing", "failed"]

    @patch('app.api.routes.get_llm_service')
    def test_search_functionality(self, mock_get_llm_service):
        """Test search endpoint functionality."""
        # Mock LLM service
        mock_llm = MagicMock()
        mock_get_llm_service.return_value = mock_llm
        
        # First, create an analysis
        mock_llm.analyze_text.return_value = {
            "summary": "Python is a versatile programming language.",
            "title": "Python Programming",
            "topics": ["python", "programming", "development"],
            "sentiment": "positive"
        }

        # Analyze text
        response = client.post("/analyze", json={"text": "Python programming is awesome"})
        assert response.status_code == 200

        # Search for it
        response = client.get("/search?topic=python")
        assert response.status_code == 200

        data = response.json()
        assert data["total_count"] >= 1
        assert data["search_term"] == "python"
        assert len(data["analyses"]) >= 1

        # Search should find by topic
        found = False
        for analysis in data["analyses"]:
            if "python" in [t.lower() for t in analysis["topics"]]:
                found = True
                break
        assert found

    def test_search_missing_parameter(self):
        """Test search endpoint with missing parameter."""
        response = client.get("/search")
        assert response.status_code == 422

    def test_get_all_analyses(self):
        """Test retrieving all analyses."""
        response = client.get("/analyses")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_analysis_by_id(self):
        """Test retrieving a specific analysis by ID."""
        # First create an analysis
        with patch('app.api.routes.get_llm_service') as mock_get_llm_service:
            mock_llm = MagicMock()
            mock_get_llm_service.return_value = mock_llm
            mock_llm.analyze_text.return_value = {
                "summary": "Test summary",
                "title": "Test",
                "topics": ["test", "example", "demo"],
                "sentiment": "neutral"
            }
            response = client.post("/analyze", json={"text": "Test text"})
            analysis_id = response.json()["id"]

        # Get the analysis
        response = client.get(f"/analysis/{analysis_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == analysis_id

    def test_get_nonexistent_analysis(self):
        """Test retrieving a non-existent analysis."""
        response = client.get("/analysis/99999")
        assert response.status_code == 404


class TestTextProcessor:
    """Test suite for text processing functionality."""

    def test_keyword_extraction(self):
        """Test keyword extraction from text."""
        processor = TextProcessor()
        keywords = processor.extract_keywords(SAMPLE_TEXT)

        assert len(keywords) == 3
        assert all(isinstance(k, str) for k in keywords)
        # Should extract nouns like "intelligence", "technology", "learning"
        assert any(k in ["intelligence", "technology", "learning", "algorithms",
                         "computers", "tasks", "future", "applications",
                         "healthcare", "finance", "education"] for k in keywords)

    def test_confidence_score_calculation(self):
        """Test confidence score calculation."""
        processor = TextProcessor()
        score = processor.calculate_confidence_score(
            SAMPLE_TEXT,
            "AI is transforming technology",
            ["intelligence", "technology", "learning"]
        )

        assert 0 <= score <= 100
        assert isinstance(score, int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
