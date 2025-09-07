"""
Integration tests for Verification Agent
Tests the complete flow: Retrieval → Verification → Summarization
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch
import time

import pytest
from fastapi import HTTPException

# Import modules to test
from orchestrator import orchestrate_query
from retrieval import RetrievalAgent, NewsAPIConfig
from verification import VerificationAgent
from summarization import SummarizationAgent


class TestVerificationIntegration:
    """Integration tests for verification within the full pipeline"""

    def _get_test_sources(self):
        """Helper method to get consistent test sources for all tests"""
        return [
            {
                "url": "https://newsapi.example.com/article1",
                "title": "Breaking News: Major Event", 
                "isVerified": False,
            },
            {
                "url": "https://newsapi.example.com/article2", 
                "title": "Analysis: Expert Opinion",
                "isVerified": False,
            },
            {
                "url": "https://newsapi.example.com/article3",
                "title": "Local Impact: Community Response",
                "isVerified": False,
            },
        ]

    @pytest.mark.asyncio
    async def test_end_to_end_verification_disabled(self):
        """Test complete pipeline with verification disabled (NFR7 compliance)"""
        query = "test news query"
        
        # Mock environment with real summarization disabled for predictable testing
        env_vars = {
            "NEWSAPI_KEY": "test_key",
            "ENABLE_REAL_VERIFICATION": "false",  # Disabled per NFR7
            "ENABLE_REAL_SUMMARIZATION": "false",  # Use mock for predictable results
        }

        with patch.dict(os.environ, env_vars):
            # Mock the fetch_articles function directly to return our test sources
            test_sources = self._get_test_sources()
            
            with patch("orchestrator.fetch_articles", return_value=test_sources):
                # Execute full pipeline
                result = await orchestrate_query(query)

                # Verify response structure
                assert "format" in result
                assert "content" in result
                assert "sources" in result
                
                # Verify verification status per NFR7
                assert len(result["sources"]) == 3
                for source in result["sources"]:
                    assert source["isVerified"] == False  # Critical NFR7 requirement
                    assert "url" in source
                    assert "title" in source

                # Verify sources match original articles
                source_urls = {source["url"] for source in result["sources"]}
                expected_urls = {
                    "https://newsapi.example.com/article1",
                    "https://newsapi.example.com/article2", 
                    "https://newsapi.example.com/article3",
                }
                assert source_urls == expected_urls

    @pytest.mark.asyncio
    async def test_end_to_end_verification_enabled_uses_mock(self):
        """Test that even when enabled, verification uses mock behavior for now"""
        query = "test news query"
        
        env_vars = {
            "NEWSAPI_KEY": "test_key",
            "ENABLE_REAL_VERIFICATION": "true",  # Enabled but should use mock
            "ENABLE_REAL_SUMMARIZATION": "false",
        }

        with patch.dict(os.environ, env_vars):
            test_sources = self._get_test_sources()
            with patch("orchestrator.fetch_articles", return_value=test_sources):
                result = await orchestrate_query(query)

                # Even with flag enabled, should use mock per current implementation
                assert len(result["sources"]) == 3
                for source in result["sources"]:
                    assert source["isVerified"] == False  # Still false per current mock

    @pytest.mark.asyncio
    async def test_verification_error_handling_in_pipeline(self):
        """Test pipeline handles verification errors gracefully"""
        query = "test news query"
        
        env_vars = {
            "NEWSAPI_KEY": "test_key",
            "ENABLE_REAL_VERIFICATION": "false",
            "ENABLE_REAL_SUMMARIZATION": "false",
        }

        with patch.dict(os.environ, env_vars):
            test_sources = self._get_test_sources()
            with patch("orchestrator.fetch_articles", return_value=test_sources):
                # Mock verification to raise an error
                with patch("verification.verification_agent.verify_articles", side_effect=Exception("Verification error")):
                    # Pipeline should still complete with fallback
                    result = await orchestrate_query(query)
                    
                    assert "sources" in result
                    # Sources should be available from fallback error handling

    @pytest.mark.asyncio
    async def test_verification_with_empty_retrieval_results(self):
        """Test verification behavior when retrieval returns no articles"""
        query = "test news query"

        env_vars = {
            "NEWSAPI_KEY": "test_key",
            "ENABLE_REAL_VERIFICATION": "false",
            "ENABLE_REAL_SUMMARIZATION": "false",
        }

        with patch.dict(os.environ, env_vars):
            # Mock empty sources from retrieval  
            with patch("orchestrator.fetch_articles", return_value=[]):
                result = await orchestrate_query(query)
                
                # Should handle empty sources gracefully
                assert result["sources"] == []

    @pytest.mark.asyncio
    async def test_source_object_integrity_through_pipeline(self):
        """Test that Source objects maintain integrity through the pipeline"""
        query = "test news query"
        
        env_vars = {
            "NEWSAPI_KEY": "test_key",
            "ENABLE_REAL_VERIFICATION": "false",
            "ENABLE_REAL_SUMMARIZATION": "false",
        }

        with patch.dict(os.environ, env_vars):
            test_sources = self._get_test_sources()
            with patch("orchestrator.fetch_articles", return_value=test_sources):
                result = await orchestrate_query(query)

                # Verify Source object structure integrity
                for source in result["sources"]:
                    # Required fields per Source data model
                    assert isinstance(source["url"], str)
                    assert isinstance(source["title"], str)
                    assert isinstance(source["isVerified"], bool)
                    
                    # Optional field handling
                    if "biasScore" in source:
                        assert source["biasScore"] is None or isinstance(source["biasScore"], (int, float))

                    # Verify no data corruption
                    assert source["url"].startswith("http")
                    assert len(source["title"]) > 0
                    assert source["isVerified"] == False  # NFR7 compliance

    @pytest.mark.asyncio
    async def test_verification_performance_within_pipeline(self):
        """Test that verification doesn't add significant latency"""
        query = "test news query"
        
        env_vars = {
            "NEWSAPI_KEY": "test_key",
            "ENABLE_REAL_VERIFICATION": "false",
            "ENABLE_REAL_SUMMARIZATION": "false",
        }

        with patch.dict(os.environ, env_vars):
            test_sources = self._get_test_sources()
            with patch("orchestrator.fetch_articles", return_value=test_sources):
                start_time = time.time()
                result = await orchestrate_query(query)
                end_time = time.time()

                # Verification should add minimal overhead (<100ms per story requirement)
                execution_time = end_time - start_time
                
                # Mock execution should be very fast
                assert execution_time < 1.0  # Should be much faster than 1 second
                assert len(result["sources"]) == 3

    @pytest.mark.asyncio
    async def test_verification_feature_flag_validation(self):
        """Test feature flag validation during pipeline execution"""
        query = "test news query"
        
        # Test both flag states
        for flag_value in ["true", "false"]:
            env_vars = {
                "NEWSAPI_KEY": "test_key",
                "ENABLE_REAL_VERIFICATION": flag_value,
                "ENABLE_REAL_SUMMARIZATION": "false",
            }

            with patch.dict(os.environ, env_vars):
                test_sources = self._get_test_sources()
                with patch("orchestrator.fetch_articles", return_value=test_sources):
                    result = await orchestrate_query(query)
                    
                    # Regardless of flag value, should use mock verification for now
                    assert len(result["sources"]) == 3
                    for source in result["sources"]:
                        assert source["isVerified"] == False  # Per current implementation

    @pytest.mark.asyncio
    async def test_ui_compatibility_source_format(self):
        """Test that verification output is compatible with UI expectations"""
        query = "test news query"
        
        env_vars = {
            "NEWSAPI_KEY": "test_key",
            "ENABLE_REAL_VERIFICATION": "false",
            "ENABLE_REAL_SUMMARIZATION": "false",
        }

        with patch.dict(os.environ, env_vars):
            test_sources = self._get_test_sources()
            with patch("orchestrator.fetch_articles", return_value=test_sources):
                result = await orchestrate_query(query)

                # Verify UI-compatible format
                assert "sources" in result
                assert isinstance(result["sources"], list)
                
                for source in result["sources"]:
                    # UI expects these exact fields for verification display
                    assert "url" in source
                    assert "title" in source
                    assert "isVerified" in source
                    
                    # Types must be correct for TypeScript interface
                    assert isinstance(source["url"], str)
                    assert isinstance(source["title"], str)
                    assert isinstance(source["isVerified"], bool)
                    
                    # URL must be valid for links
                    assert source["url"].startswith("http")
                    
                    # Title must not be empty for display
                    assert len(source["title"].strip()) > 0