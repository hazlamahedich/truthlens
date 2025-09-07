"""
Unit tests for Verification Agent
"""

import os
from unittest.mock import patch
from typing import Dict, Any, List

import pytest
from fastapi import HTTPException

# Import the modules to test
from verification import VerificationAgent, Source, verify_articles


class TestVerificationAgent:
    """Test cases for VerificationAgent class"""

    @pytest.fixture
    def agent(self):
        """Create a VerificationAgent instance for testing"""
        with patch.dict(os.environ, {"ENABLE_REAL_VERIFICATION": "false"}):
            return VerificationAgent()

    @pytest.fixture
    def agent_enabled(self):
        """Create a VerificationAgent instance with feature flag enabled"""
        with patch.dict(os.environ, {"ENABLE_REAL_VERIFICATION": "true"}):
            return VerificationAgent()

    @pytest.fixture
    def sample_sources(self) -> List[Dict[str, Any]]:
        """Sample sources for testing"""
        return [
            {
                "url": "https://example.com/article1",
                "title": "Test Article 1",
                "isVerified": True,  # Will be overridden per NFR7
            },
            {
                "url": "https://example.com/article2", 
                "title": "Test Article 2",
                "isVerified": False,
                "biasScore": 0.3
            },
            {
                "url": "https://example.com/article3",
                "title": "Test Article 3",
            }
        ]

    def test_initialization_feature_flag_disabled(self):
        """Test agent initializes with feature flag disabled"""
        with patch.dict(os.environ, {"ENABLE_REAL_VERIFICATION": "false"}):
            agent = VerificationAgent()
            assert agent._is_enabled == False

    def test_initialization_feature_flag_enabled(self):
        """Test agent initializes with feature flag enabled"""
        with patch.dict(os.environ, {"ENABLE_REAL_VERIFICATION": "true"}):
            agent = VerificationAgent()
            assert agent._is_enabled == True

    def test_initialization_feature_flag_missing(self):
        """Test agent defaults to disabled when flag is missing"""
        with patch.dict(os.environ, {}, clear=True):
            agent = VerificationAgent()
            assert agent._is_enabled == False

    def test_feature_flag_various_values(self):
        """Test different feature flag values"""
        # Test true values
        for value in ["true", "True", "TRUE", "1", "yes", "on"]:
            with patch.dict(os.environ, {"ENABLE_REAL_VERIFICATION": value}):
                agent = VerificationAgent()
                assert agent._is_enabled == True, f"Failed for value: {value}"

        # Test false values
        for value in ["false", "False", "FALSE", "0", "no", "off", "invalid"]:
            with patch.dict(os.environ, {"ENABLE_REAL_VERIFICATION": value}):
                agent = VerificationAgent()
                assert agent._is_enabled == False, f"Failed for value: {value}"

    @pytest.mark.asyncio
    async def test_verify_articles_empty_list(self, agent):
        """Test verification with empty source list"""
        result = await agent.verify_articles([])
        assert result == []

    @pytest.mark.asyncio
    async def test_verify_articles_mock_verification(self, agent, sample_sources):
        """Test mock verification sets isVerified to False per NFR7"""
        result = await agent.verify_articles(sample_sources)
        
        assert len(result) == 3
        # All sources should have isVerified=False per NFR7
        for source in result:
            assert source["isVerified"] == False
        
        # Verify structure integrity
        assert result[0]["url"] == "https://example.com/article1"
        assert result[0]["title"] == "Test Article 1"
        assert result[1]["biasScore"] == 0.3  # Preserved
        assert result[2]["url"] == "https://example.com/article3"

    @pytest.mark.asyncio
    async def test_verify_articles_enabled_uses_mock(self, agent_enabled, sample_sources):
        """Test that enabled flag still uses mock (real implementation pending)"""
        result = await agent_enabled.verify_articles(sample_sources)
        
        # Should still use mock verification for now
        assert len(result) == 3
        for source in result:
            assert source["isVerified"] == False

    @pytest.mark.asyncio
    async def test_verify_articles_invalid_sources(self, agent):
        """Test handling of invalid source structures"""
        invalid_sources = [
            {"url": "https://example.com/valid", "title": "Valid Source"},
            {"title": "Missing URL"},  # Missing URL
            {"url": "https://example.com/missing-title"},  # Missing title
            {"url": "", "title": "Empty URL"},  # Empty URL
            {"url": "https://example.com/no-title", "title": ""},  # Empty title
            "not_a_dict",  # Not a dictionary
            {"url": 123, "title": "Invalid URL type"},  # Invalid URL type
        ]
        
        result = await agent.verify_articles(invalid_sources)
        
        # Should only process valid sources
        assert len(result) == 1
        assert result[0]["url"] == "https://example.com/valid"
        assert result[0]["title"] == "Valid Source"
        assert result[0]["isVerified"] == False

    @pytest.mark.asyncio
    async def test_verify_articles_preserves_bias_score(self, agent):
        """Test that biasScore is preserved when present"""
        sources = [
            {
                "url": "https://example.com/article1",
                "title": "Article with bias score",
                "biasScore": 0.7
            },
            {
                "url": "https://example.com/article2", 
                "title": "Article without bias score"
            }
        ]
        
        result = await agent.verify_articles(sources)
        
        assert result[0]["biasScore"] == 0.7
        assert result[1].get("biasScore") is None

    @pytest.mark.asyncio 
    async def test_verify_articles_error_fallback(self, agent):
        """Test fallback behavior on verification error"""
        sources = [
            {"url": "https://example.com/article1", "title": "Test Article 1"}
        ]
        
        # Mock an error in validation
        with patch.object(agent, '_validate_sources', side_effect=Exception("Test error")):
            result = await agent.verify_articles(sources)
            
            # Should fallback gracefully
            assert len(result) == 1
            assert result[0]["isVerified"] == False  # Safe fallback

    def test_validate_sources_valid_input(self, agent, sample_sources):
        """Test source validation with valid input"""
        result = agent._validate_sources(sample_sources)
        
        assert len(result) == 3
        assert all("url" in source for source in result)
        assert all("title" in source for source in result)
        assert all("isVerified" in source for source in result)

    def test_validate_sources_mixed_input(self, agent):
        """Test source validation with mixed valid/invalid input"""
        sources = [
            {"url": "https://example.com/valid", "title": "Valid"},
            {"title": "No URL"},
            {"url": "https://example.com/valid2", "title": "Valid 2"},
            "invalid_type"
        ]
        
        result = agent._validate_sources(sources)
        
        # Should only return valid sources
        assert len(result) == 2
        assert result[0]["url"] == "https://example.com/valid"
        assert result[1]["url"] == "https://example.com/valid2"

    def test_perform_mock_verification(self, agent):
        """Test mock verification logic"""
        sources = [
            {"url": "https://example.com/1", "title": "Article 1", "isVerified": True},
            {"url": "https://example.com/2", "title": "Article 2", "isVerified": False},
        ]
        
        result = agent._perform_mock_verification(sources)
        
        # All should be marked unverified per NFR7
        assert len(result) == 2
        assert all(source["isVerified"] == False for source in result)

    def test_fallback_verification_missing_fields(self, agent):
        """Test fallback verification handles missing fields gracefully"""
        sources = [
            {"url": "https://example.com/1"},  # Missing title
            {"title": "Missing URL Article"},  # Missing URL
            {},  # Missing both
        ]
        
        result = agent._fallback_verification(sources)
        
        assert len(result) == 3
        assert result[0]["url"] == "https://example.com/1"
        assert result[0]["title"] == "Unknown"  # Fallback title
        assert result[1]["url"] == ""  # Fallback URL
        assert result[1]["title"] == "Missing URL Article"
        assert result[2]["url"] == ""
        assert result[2]["title"] == "Unknown"
        
        # All should be unverified for safety
        assert all(source["isVerified"] == False for source in result)


class TestVerifyArticlesFunction:
    """Test the standalone verify_articles function"""

    @pytest.mark.asyncio
    async def test_verify_articles_function(self):
        """Test the FastAPI endpoint function"""
        sources = [
            {"url": "https://example.com/1", "title": "Test 1"},
            {"url": "https://example.com/2", "title": "Test 2"},
        ]
        
        with patch("verification.verification_agent.verify_articles") as mock_verify:
            mock_verify.return_value = [
                {"url": "https://example.com/1", "title": "Test 1", "isVerified": False},
                {"url": "https://example.com/2", "title": "Test 2", "isVerified": False},
            ]
            
            result = await verify_articles(sources)
            
            assert len(result) == 2
            assert result[0]["url"] == "https://example.com/1"
            assert result[0]["title"] == "Test 1"
            assert result[0]["isVerified"] == False
            assert result[1]["url"] == "https://example.com/2"
            assert result[1]["title"] == "Test 2"
            assert result[1]["isVerified"] == False

    @pytest.mark.asyncio
    async def test_verify_articles_function_empty_input(self):
        """Test function with empty input"""
        result = await verify_articles([])
        assert result == []


class TestSourceDataModel:
    """Test Source data model"""

    def test_source_creation_minimal(self):
        """Test Source creation with minimal required fields"""
        source = Source(url="https://example.com", title="Test Title")
        assert source.url == "https://example.com"
        assert source.title == "Test Title"
        assert source.isVerified == False  # Default value
        assert source.biasScore is None  # Default value

    def test_source_creation_full(self):
        """Test Source creation with all fields"""
        source = Source(
            url="https://example.com",
            title="Test Title", 
            isVerified=True,
            biasScore=0.5
        )
        assert source.url == "https://example.com"
        assert source.title == "Test Title"
        assert source.isVerified == True
        assert source.biasScore == 0.5

    def test_source_defaults_nfr7_compliance(self):
        """Test that Source defaults to isVerified=False per NFR7"""
        source = Source(url="https://example.com", title="Test Title")
        assert source.isVerified == False  # Critical NFR7 requirement