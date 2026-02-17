from src.models.preprocessing import TextProcessor
import pytest

class TestTextProcessor:
    """Test suite for texpreprocessor"""

    @pytest.fixture
    def preprocessor(self):
        return TextProcessor()
    
    # === Tests for clean() method ===
    def test_clean_removes_urls(self, preprocessor):
        text = "Check this out https://example.com amazing!"
        result = preprocessor.clean(text)
        assert "https://example.com" not in result
        assert "example.com" not in result
        assert "check this out amazing" in result
    
    def test_clean_removes_html(self, preprocessor):
        text = "This is <b>bold</b> text"
        result = preprocessor.clean(text)
        assert "<b>" not in result
        assert "</b>" not in result
        assert "this is bold text" == result
    
    def test_clean_converts_emojis(self, preprocessor):
        text = "Great video! 😍"
        result = preprocessor.clean(text)
        assert "😍" not in result
        assert "heart" in result.lower() or "face" in result.lower()
    
    def test_clean_reduces_multiple_question_marks(self, preprocessor):
        text = "Really???"
        result = preprocessor.clean(text)
        assert result == "really?"
        assert "???" not in result
    
    def test_clean_reduces_excessive_letters(self, preprocessor):
        text = "yesssssss"
        result = preprocessor.clean(text)
        assert result == "yess"
        assert "ssssss" not in result
    
    def test_clean_reduces_excessive_letters_preserves_doubles(self, preprocessor):
        text = "goood"
        result = preprocessor.clean(text)
        assert result == "good"
    
    def test_clean_normalizes_whitespace(self, preprocessor):
        text = "too    many     spaces"
        result = preprocessor.clean(text)
        assert result == "too many spaces"
        assert "    " not in result
    
    def test_clean_strips_leading_trailing_whitespace(self, preprocessor):
        text = "   spaces around   "
        result = preprocessor.clean(text)
        assert result == "spaces around"
        assert not result.startswith(" ")
        assert not result.endswith(" ")
    
    def test_clean_handles_empty_string(self, preprocessor):
        text = ""
        result = preprocessor.clean(text)
        assert result == ""
    
    def test_clean_handles_none(self, preprocessor):
        text = None
        result = preprocessor.clean(text)
        assert result == ""
    
    def test_clean_handles_whitespace_only(self, preprocessor):
        text = "    "
        result = preprocessor.clean(text)
        assert result == ""
    
    def test_clean_complex_case(self, preprocessor):
        text = "OMG this is AMAZINGGG!!!! 😍😍 https://link.com"
        result = preprocessor.clean(text)
        assert "https://link.com" not in result
        assert "😍" not in result
        assert result.islower()
        assert "!!!!" not in result
        assert "omg" in result
        assert "amazingg" in result
    
    def test_is_valid_accepts_normal_text(self):
        assert TextProcessor.is_valid("this is valid") is True
    
    def test_is_valid_accepts_short_text(self):
        assert TextProcessor.is_valid("ok") is True
        assert TextProcessor.is_valid("no") is True
    
    def test_is_valid_rejects_empty(self):
        assert TextProcessor.is_valid("") is False
    
    def test_is_valid_rejects_whitespace(self):
        assert TextProcessor.is_valid("   ") is False
        assert TextProcessor.is_valid("\t") is False
        assert TextProcessor.is_valid("\n") is False
    
    def test_is_valid_rejects_single_char(self):
        assert TextProcessor.is_valid("a") is False
        assert TextProcessor.is_valid("?") is False
    
    def test_is_valid_rejects_none(self):
        assert TextProcessor.is_valid(None) is False
    
    # Parameterized tests 
    
    @pytest.mark.parametrize("text,expected_valid", [
        ("Great video!", True),
        ("First!", True),
        ("ok", True),
        ("😍😍", True),
        ("https://only-url.com", False),
        ("   ", False),
        ("", False),
    ])
    def test_clean_and_validate_parametrized(self, preprocessor, text, expected_valid):
        cleaned = preprocessor.clean(text)
        result = TextProcessor.is_valid(cleaned)
        assert result == expected_valid, \
            f"Failed for '{text}' → cleaned: '{cleaned}' → valid: {result}"