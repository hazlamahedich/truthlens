"""
Unit tests for Summarization Agent
Tests LLM integration, feature flags, error handling, and mock fallbacks
"""

import asyncio
import json
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

# Import the modules under test
from summarization import (
    LLMConfig,
    LLMClient, 
    PromptTemplates,
    SummarizationAgent,
    summarize_articles
)


class TestLLMConfig:
    """Test LLM configuration"""
    
    def test_config_initialization_default(self):
        """Test configuration initialization with default values"""
        with patch.dict(os.environ, {}, clear=True):
            config = LLMConfig()
            
            assert config.gemini_api_key is None
            assert config.model == "gemini-1.5-flash"
            assert config.timeout == 12
            assert config.max_output_tokens == 1500
            assert config.temperature == 0.7
    
    def test_config_initialization_with_env(self):
        """Test configuration initialization with environment variables"""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-api-key-123"}):
            config = LLMConfig()
            
            assert config.gemini_api_key == "test-api-key-123"
            assert config.is_configured() is True
    
    def test_is_configured_false_cases(self):
        """Test is_configured returns False for invalid configurations"""
        with patch.dict(os.environ, {}, clear=True):
            config = LLMConfig()
            assert config.is_configured() is False
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            config = LLMConfig()
            assert config.is_configured() is False
            
        with patch.dict(os.environ, {"GEMINI_API_KEY": "your_gemini_key_here"}):
            config = LLMConfig()
            assert config.is_configured() is False


class TestPromptTemplates:
    """Test prompt template generation"""
    
    def test_debate_format_template(self):
        """Test debate format prompt template generation"""
        articles = [
            {"title": "Article 1", "url": "http://example.com/1", "description": "Test description 1"},
            {"title": "Article 2", "url": "http://example.com/2", "description": "Test description 2"}
        ]
        
        prompt = PromptTemplates.debate_format("climate change", articles)
        
        assert "climate change" in prompt
        assert "Article 1" in prompt
        assert "Article 2" in prompt
        assert "for" in prompt.lower()
        assert "against" in prompt.lower()
        assert "JSON" in prompt
    
    def test_venn_diagram_format_template(self):
        """Test venn diagram format prompt template generation"""
        articles = [
            {"title": "Politics Article", "url": "http://example.com/1", "description": "Political perspective"}
        ]
        
        prompt = PromptTemplates.venn_diagram_format("election", articles)
        
        assert "election" in prompt
        assert "Politics Article" in prompt
        assert "topic_a" in prompt
        assert "topic_b" in prompt
        assert "unique_a" in prompt
        assert "unique_b" in prompt
        assert "common" in prompt
    
    def test_prompt_template_with_empty_articles(self):
        """Test prompt template generation with empty articles list"""
        prompt = PromptTemplates.debate_format("test query", [])
        
        assert "test query" in prompt
        assert "JSON" in prompt


class TestLLMClient:
    """Test LLM client HTTP integration"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing"""
        config = MagicMock()
        config.gemini_api_key = "test-api-key"
        config.gemini_base_url = "https://api.test.com/v1beta/models"
        config.model = "gemini-1.5-flash"
        config.timeout = 12
        config.max_output_tokens = 1500
        config.temperature = 0.7
        config.is_configured.return_value = True
        return config
    
    @pytest.fixture
    def llm_client(self, mock_config):
        """Create LLM client with mock config"""
        return LLMClient(mock_config)
    
    @pytest.mark.asyncio
    async def test_successful_llm_call(self, llm_client):
        """Test successful LLM API call"""
        mock_response_data = {
            "candidates": [{
                "content": {
                    "parts": [{"text": '{"statement": "test", "for": ["arg1"], "against": ["arg2"]}'}]
                }
            }]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_response_data
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await llm_client.call_llm("test prompt")
            
            assert result == '{"statement": "test", "for": ["arg1"], "against": ["arg2"]}'
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authentication_error(self, llm_client):
        """Test handling of authentication errors"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_post.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(HTTPException) as exc_info:
                await llm_client.call_llm("test prompt")
            
            assert exc_info.value.status_code == 500
            assert "configuration error" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, llm_client):
        """Test rate limit handling with retries"""
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('asyncio.sleep') as mock_sleep:
            
            mock_response = AsyncMock()
            mock_response.status = 429
            mock_response.headers.get.return_value = "60"
            mock_post.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(HTTPException) as exc_info:
                await llm_client.call_llm("test prompt", max_retries=2)
            
            assert exc_info.value.status_code == 503
            assert "temporarily busy" in exc_info.value.detail
            assert mock_sleep.call_count >= 2  # Verify retry attempts
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, llm_client):
        """Test timeout error handling"""
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('asyncio.sleep') as mock_sleep:
            
            mock_post.side_effect = asyncio.TimeoutError()
            
            with pytest.raises(HTTPException) as exc_info:
                await llm_client.call_llm("test prompt", max_retries=1)
            
            assert exc_info.value.status_code == 503
            assert "timeout" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_unconfigured_client(self):
        """Test client behavior when not properly configured"""
        config = MagicMock()
        config.is_configured.return_value = False
        client = LLMClient(config)
        
        with pytest.raises(HTTPException) as exc_info:
            await client.call_llm("test prompt")
        
        assert exc_info.value.status_code == 500
        assert "configuration error" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_malformed_response(self, llm_client):
        """Test handling of malformed API responses"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"unexpected": "format"}
            mock_post.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(HTTPException) as exc_info:
                await llm_client.call_llm("test prompt")
            
            assert exc_info.value.status_code == 500
            assert "response format error" in exc_info.value.detail


class TestSummarizationAgent:
    """Test the main summarization agent"""
    
    @pytest.fixture
    def mock_env_enabled(self):
        """Mock environment with feature flag enabled"""
        env_vars = {
            "ENABLE_REAL_SUMMARIZATION": "true",
            "GEMINI_API_KEY": "test-api-key-123"
        }
        return patch.dict(os.environ, env_vars)
    
    @pytest.fixture
    def mock_env_disabled(self):
        """Mock environment with feature flag disabled"""
        env_vars = {
            "ENABLE_REAL_SUMMARIZATION": "false",
            "GEMINI_API_KEY": "test-api-key-123"
        }
        return patch.dict(os.environ, env_vars)
    
    @pytest.mark.asyncio
    async def test_feature_flag_disabled_uses_mock(self, mock_env_disabled):
        """Test that disabled feature flag uses mock summarization"""
        with mock_env_disabled:
            agent = SummarizationAgent()
            
            articles = [
                {"title": "Test Article", "url": "http://example.com", "description": "Test description"}
            ]
            
            result = await agent.summarize_articles(articles, "debate")
            
            assert result["format"] == "debate"
            assert "content" in result
            assert "sources" in result
            assert result["content"]["statement"] is not None
            assert isinstance(result["content"]["for"], list)
            assert isinstance(result["content"]["against"], list)
    
    @pytest.mark.asyncio
    async def test_feature_flag_enabled_attempts_llm(self, mock_env_enabled):
        """Test that enabled feature flag attempts LLM call"""
        with mock_env_enabled:
            agent = SummarizationAgent()
            
            articles = [
                {"title": "Test Article", "url": "http://example.com", "description": "Test description"}
            ]
            
            # Mock LLM client to avoid actual API calls
            with patch.object(agent.client, 'call_llm') as mock_call_llm:
                mock_call_llm.return_value = json.dumps({
                    "statement": "AI generated statement",
                    "for": ["AI argument 1", "AI argument 2"],
                    "against": ["AI counter 1", "AI counter 2"]
                })
                
                result = await agent.summarize_articles(articles, "debate")
                
                assert result["format"] == "debate"
                assert result["content"]["statement"] == "AI generated statement"
                assert len(result["content"]["for"]) == 2
                assert len(result["content"]["against"]) == 2
                mock_call_llm.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_venn_diagram_format(self, mock_env_disabled):
        """Test venn diagram format generation"""
        with mock_env_disabled:
            agent = SummarizationAgent()
            
            articles = [
                {"title": "Test Article", "url": "http://example.com", "description": "Test description"}
            ]
            
            result = await agent.summarize_articles(articles, "venn_diagram")
            
            assert result["format"] == "venn_diagram"
            assert "topic_a" in result["content"]
            assert "topic_b" in result["content"]
            assert "unique_a" in result["content"]
            assert "unique_b" in result["content"]
            assert "common" in result["content"]
    
    @pytest.mark.asyncio
    async def test_empty_articles_handling(self, mock_env_disabled):
        """Test handling of empty articles list"""
        with mock_env_disabled:
            agent = SummarizationAgent()
            
            result = await agent.summarize_articles([], "debate")
            
            assert result["format"] == "debate"
            assert result["sources"] == []
            assert "No articles" in result["content"]["statement"]
    
    @pytest.mark.asyncio
    async def test_llm_error_fallback(self, mock_env_enabled):
        """Test fallback to mock when LLM call fails"""
        with mock_env_enabled:
            agent = SummarizationAgent()
            
            articles = [
                {"title": "Test Article", "url": "http://example.com", "description": "Test description"}
            ]
            
            # Mock LLM client to raise an exception
            with patch.object(agent.client, 'call_llm') as mock_call_llm:
                mock_call_llm.side_effect = HTTPException(status_code=503, detail="Service unavailable")
                
                result = await agent.summarize_articles(articles, "debate")
                
                # Should fall back to mock content
                assert result["format"] == "debate"
                assert "content" in result
                assert "sources" in result
                assert len(result["sources"]) == 1
    
    @pytest.mark.asyncio 
    async def test_articles_to_sources_conversion(self, mock_env_disabled):
        """Test conversion of articles to sources format"""
        with mock_env_disabled:
            agent = SummarizationAgent()
            
            articles = [
                {
                    "title": "Test Article 1",
                    "url": "http://example.com/1",
                    "description": "Test description 1"
                },
                {
                    "title": "Test Article 2", 
                    "url": "http://example.com/2",
                    "description": "Test description 2"
                }
            ]
            
            result = await agent.summarize_articles(articles, "debate")
            
            assert len(result["sources"]) == 2
            assert result["sources"][0]["title"] == "Test Article 1"
            assert result["sources"][0]["url"] == "http://example.com/1"
            assert result["sources"][0]["isVerified"] is False
            assert result["sources"][1]["title"] == "Test Article 2"
            assert result["sources"][1]["url"] == "http://example.com/2"
            assert result["sources"][1]["isVerified"] is False


class TestSummarizeArticlesFunction:
    """Test the module-level function"""
    
    @pytest.mark.asyncio
    async def test_summarize_articles_function(self):
        """Test the module-level summarize_articles function"""
        articles = [
            {"title": "Function Test", "url": "http://example.com", "description": "Test"}
        ]
        
        with patch.dict(os.environ, {"ENABLE_REAL_SUMMARIZATION": "false"}):
            result = await summarize_articles(articles, "debate")
            
            assert result["format"] == "debate"
            assert "content" in result
            assert "sources" in result


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases"""
    
    @pytest.mark.asyncio
    async def test_json_parsing_edge_cases(self):
        """Test various JSON parsing scenarios"""
        agent = SummarizationAgent()
        
        # Test valid JSON response
        valid_json = '{"statement": "test", "for": [], "against": []}'
        result = agent._extract_json_from_text(valid_json, "debate")
        assert result is not None
        assert result["statement"] == "test"
        
        # Test JSON embedded in text
        embedded_json = 'Here is the result: {"statement": "embedded", "for": [], "against": []} and more text'
        result = agent._extract_json_from_text(embedded_json, "debate")
        assert result is not None
        assert result["statement"] == "embedded"
        
        # Test malformed JSON
        malformed_json = '{"statement": "incomplete", "for": ['
        result = agent._extract_json_from_text(malformed_json, "debate")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_performance_benchmarks(self):
        """Test that performance requirements are met"""
        import time
        
        with patch.dict(os.environ, {"ENABLE_REAL_SUMMARIZATION": "false"}):
            agent = SummarizationAgent()
            
            # Large article set to test performance
            articles = [
                {
                    "title": f"Article {i}",
                    "url": f"http://example.com/{i}",
                    "description": f"Test description for article {i}" * 20  # Make it longer
                }
                for i in range(10)
            ]
            
            start_time = time.time()
            result = await agent.summarize_articles(articles, "debate")
            end_time = time.time()
            
            # Should complete well under 15 second requirement (mocked should be very fast)
            assert end_time - start_time < 1.0
            assert len(result["sources"]) == 10
            
            # Clean up resources
            await agent.cleanup()


if __name__ == "__main__":
    pytest.main([__file__])