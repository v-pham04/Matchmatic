import pytest
import json
from unittest.mock import patch, MagicMock
 
 
class TestGeminiClient:
    """Tests for the GeminiClient wrapper."""
 
    def test_call_model_returns_text(self):
        """call_model() should return the text from the Gemini response."""
        with patch("app.agents.gemini_client.client") as mock_client:
            mock_response = MagicMock()
            mock_response.text = "Hello from Gemini"
            mock_response.usage_metadata = None
            mock_client.models.generate_content.return_value = mock_response
 
            from app.agents.gemini_client import GeminiClient
            gc = GeminiClient()
            result = gc.call_model("Say hello")
            assert result == "Hello from Gemini"
 
    def test_call_model_json_parses_valid_json(self):
        """call_model_json() should parse a valid JSON response."""
        with patch("app.agents.gemini_client.client") as mock_client:
            mock_response = MagicMock()
            mock_response.text = '{"score": 85, "match_level": "HIGH"}'
            mock_response.usage_metadata = None
            mock_client.models.generate_content.return_value = mock_response
 
            from app.agents.gemini_client import GeminiClient
            gc = GeminiClient()
            result = gc.call_model_json("Score this")
            assert result["score"] == 85
            assert result["match_level"] == "HIGH"
 
    def test_call_model_json_strips_markdown_fences(self):
        """call_model_json() should strip ```json fences before parsing."""
        with patch("app.agents.gemini_client.client") as mock_client:
            mock_response = MagicMock()
            mock_response.text = '```json\n{"score": 72}\n```'
            mock_response.usage_metadata = None
            mock_client.models.generate_content.return_value = mock_response
 
            from app.agents.gemini_client import GeminiClient
            gc = GeminiClient()
            result = gc.call_model_json("Score this")
            assert result["score"] == 72
 
    def test_call_model_json_raises_on_invalid_json(self):
        """call_model_json() should raise ValueError if response is not JSON."""
        with patch("app.agents.gemini_client.client") as mock_client:
            mock_response = MagicMock()
            mock_response.text = "This is not JSON at all"
            mock_response.usage_metadata = None
            mock_client.models.generate_content.return_value = mock_response
 
            from app.agents.gemini_client import GeminiClient
            gc = GeminiClient()
            with pytest.raises(ValueError, match="not valid JSON"):
                gc.call_model_json("Score this")
 
 
class TestATSScorer:
    """Tests for the ATS Scorer agent."""
 
    def test_ats_scorer_returns_required_fields(self):
        """run_ats_scorer() should return all required fields."""
        mock_response = {
            "score": 78,
            "match_level": "MEDIUM",
            "matching_skills": ["Python", "Docker"],
            "missing_skills": ["Kubernetes"],
            "experience_match": "partial",
            "improvement_tip": "Add Kubernetes experience"
        }
 
        with patch("app.agents.ats_scorer.gemini_client") as mock_client:
            mock_client.call_model_json.return_value = mock_response
 
            from app.agents.ats_scorer import run_ats_scorer
            result = run_ats_scorer("Job description", "My resume")
 
            assert result["score"] == 78
            assert result["match_level"] == "MEDIUM"
            assert "Python" in result["matching_skills"]
 
    def test_ats_scorer_clamps_score_to_valid_range(self):
        """Score should always be between 0 and 100."""
        mock_response = {
            "score": 150,  # Invalid — should be clamped to 100
            "match_level": "HIGH",
            "matching_skills": [],
            "missing_skills": [],
        }
 
        with patch("app.agents.ats_scorer.gemini_client") as mock_client:
            mock_client.call_model_json.return_value = mock_response
 
            from app.agents.ats_scorer import run_ats_scorer
            result = run_ats_scorer("Job", "Resume")
            assert result["score"] == 100
 
    def test_ats_scorer_raises_on_empty_input(self):
        """run_ats_scorer() should raise ValueError if inputs are empty."""
        from app.agents.ats_scorer import run_ats_scorer
        with pytest.raises(ValueError):
            run_ats_scorer("", "My resume")
 
 
class TestVisaAnalyzer:
    """Tests for the Visa Analyzer agent."""
 
    def test_visa_analyzer_returns_correct_signal(self):
        """run_visa_analyzer() should return a valid visa_signal."""
        mock_response = {
            "visa_signal": "citizen_only",
            "evidence": "Must be authorized to work in the US",
            "f1_opt_compatible": False,
            "confidence": "HIGH"
        }
 
        with patch("app.agents.visa_analyzer.gemini_client") as mock_client:
            mock_client.call_model_json.return_value = mock_response
 
            from app.agents.visa_analyzer import run_visa_analyzer
            result = run_visa_analyzer("Job requiring US citizenship")
 
            assert result["visa_signal"] == "citizen_only"
            assert result["f1_opt_compatible"] == False
 
    def test_visa_analyzer_handles_empty_input(self):
        """run_visa_analyzer() should return unclear for empty input."""
        from app.agents.visa_analyzer import run_visa_analyzer
        result = run_visa_analyzer("")
        assert result["visa_signal"] == "unclear"
