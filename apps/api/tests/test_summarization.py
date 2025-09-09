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
            assert config.max_output_tokens == 2500
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
    
    def test_debate_format_template_simple(self):
        """Test simple debate format prompt template generation"""
        articles = [
            {"title": "Article 1", "url": "http://example.com/1", "description": "Test description 1"},
            {"title": "Article 2", "url": "http://example.com/2", "description": "Test description 2"}
        ]
        
        prompt = PromptTemplates.debate_format("climate change", articles, use_enhanced=False)
        
        assert "climate change" in prompt
        assert "Article 1" in prompt
        assert "Article 2" in prompt
        assert "for" in prompt.lower()
        assert "against" in prompt.lower()
        assert "JSON" in prompt
        assert "statement" in prompt
    
    def test_debate_format_template_enhanced(self):
        """Test enhanced multi-perspective debate format prompt template generation"""
        articles = [
            {"title": "Climate Article", "url": "http://example.com/1", "description": "Climate change impacts"},
            {"title": "Policy Article", "url": "http://example.com/2", "description": "Policy responses"}
        ]
        
        prompt = PromptTemplates.debate_format("climate policy", articles, use_enhanced=True)
        
        assert "climate policy" in prompt
        assert "Climate Article" in prompt
        assert "Policy Article" in prompt
        assert "perspectives" in prompt
        assert "viewpoint" in prompt
        assert "source_indices" in prompt
        assert "consensus_points" in prompt
        assert "disputed_points" in prompt
        assert "support_level" in prompt
        assert "strength" in prompt
    
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
        config.max_output_tokens = 2500
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
    
    @pytest.fixture
    def mock_env_debate_format_enabled(self):
        """Mock environment with enhanced debate format enabled"""
        env_vars = {
            "ENABLE_REAL_SUMMARIZATION": "false",
            "ENABLE_DEBATE_FORMAT": "true",
            "GEMINI_API_KEY": "test-api-key-123"
        }
        return patch.dict(os.environ, env_vars)
    
    @pytest.fixture
    def mock_env_debate_format_disabled(self):
        """Mock environment with enhanced debate format disabled"""
        env_vars = {
            "ENABLE_REAL_SUMMARIZATION": "false", 
            "ENABLE_DEBATE_FORMAT": "false",
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
    
    @pytest.mark.asyncio
    async def test_enhanced_debate_format_enabled(self, mock_env_debate_format_enabled):
        """Test enhanced multi-perspective debate format when flag is enabled"""
        with mock_env_debate_format_enabled:
            agent = SummarizationAgent()
            
            articles = [
                {"title": "Climate Study", "url": "http://example.com/1", "description": "Climate research findings"},
                {"title": "Policy Analysis", "url": "http://example.com/2", "description": "Policy implications"}
            ]
            
            result = await agent.summarize_articles(articles, "debate")
            
            assert result["format"] == "debate"
            assert "content" in result
            assert "sources" in result
            
            # Validate enhanced format structure
            content = result["content"]
            assert "topic" in content
            assert "perspectives" in content
            assert "consensus_points" in content
            assert "disputed_points" in content
            
            # Validate perspectives structure
            perspectives = content["perspectives"]
            assert isinstance(perspectives, list)
            assert len(perspectives) >= 1
            
            for perspective in perspectives:
                assert "viewpoint" in perspective
                assert "position" in perspective
                assert "support_level" in perspective
                assert "arguments" in perspective
                assert isinstance(perspective["arguments"], list)
                
                for argument in perspective["arguments"]:
                    assert "point" in argument
                    assert "source_indices" in argument
                    assert "strength" in argument
                    assert argument["strength"] in ["strong", "moderate", "weak"]
    
    @pytest.mark.asyncio
    async def test_enhanced_debate_format_disabled_backward_compatibility(self, mock_env_debate_format_disabled):
        """Test backward compatibility when enhanced debate format is disabled"""
        with mock_env_debate_format_disabled:
            agent = SummarizationAgent()
            
            articles = [
                {"title": "Test Article", "url": "http://example.com", "description": "Test description"}
            ]
            
            result = await agent.summarize_articles(articles, "debate")
            
            assert result["format"] == "debate"
            assert "content" in result
            
            # Validate simple format structure (backward compatibility)
            content = result["content"]
            assert "statement" in content
            assert "for" in content
            assert "against" in content
            assert isinstance(content["for"], list)
            assert isinstance(content["against"], list)
    
    @pytest.mark.asyncio
    async def test_input_validation_security(self, mock_env_disabled):
        """Test input validation for security"""
        with mock_env_disabled:
            agent = SummarizationAgent()
            
            # Test invalid article structure
            with pytest.raises(HTTPException) as exc_info:
                await agent.summarize_articles("not a list", "debate")
            assert exc_info.value.status_code == 400
            assert "Articles must be a list" in exc_info.value.detail
            
            # Test invalid format type
            with pytest.raises(HTTPException) as exc_info:
                await agent.summarize_articles([], "invalid_format")
            assert exc_info.value.status_code == 400
            assert "Invalid format type" in exc_info.value.detail
            
            # Test article with excessive length
            long_article = {
                "title": "x" * 501,  # Over 500 char limit
                "url": "http://example.com",
                "description": "test"
            }
            with pytest.raises(HTTPException) as exc_info:
                await agent.summarize_articles([long_article], "debate")
            assert exc_info.value.status_code == 400
            assert "title too long" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_empty_articles_enhanced_format(self, mock_env_debate_format_enabled):
        """Test empty articles handling with enhanced format"""
        with mock_env_debate_format_enabled:
            agent = SummarizationAgent()
            
            result = await agent.summarize_articles([], "debate")
            
            assert result["format"] == "debate"
            assert result["sources"] == []
            
            # Validate enhanced empty format structure
            content = result["content"]
            assert "topic" in content
            assert "perspectives" in content
            assert "consensus_points" in content
            assert "disputed_points" in content
            assert len(content["perspectives"]) == 1
            assert content["perspectives"][0]["support_level"] == 0.0
    
    @pytest.mark.asyncio
    async def test_source_attribution_enhanced_format(self, mock_env_debate_format_enabled):
        """Test source attribution in enhanced format"""
        with mock_env_debate_format_enabled:
            agent = SummarizationAgent()
            
            articles = [
                {"title": "Source 1", "url": "http://example.com/1", "description": "First source"},
                {"title": "Source 2", "url": "http://example.com/2", "description": "Second source"},
                {"title": "Source 3", "url": "http://example.com/3", "description": "Third source"}
            ]
            
            result = await agent.summarize_articles(articles, "debate")
            
            # Check that source indices are properly referenced
            content = result["content"]
            perspectives = content["perspectives"]
            
            for perspective in perspectives:
                for argument in perspective["arguments"]:
                    source_indices = argument["source_indices"]
                    assert isinstance(source_indices, list)
                    # All indices should be valid (within range of sources)
                    for idx in source_indices:
                        assert 0 <= idx < len(articles)
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self, mock_env_disabled):
        """Test that performance monitoring logs are generated"""
        with mock_env_disabled:
            agent = SummarizationAgent()
            
            articles = [
                {"title": "Perf Test", "url": "http://example.com", "description": "Performance test article"}
            ]
            
            with patch('summarization.logger') as mock_logger:
                await agent.summarize_articles(articles, "debate")
                
                # Check that performance logging occurred
                logged_messages = [call.args[0] for call in mock_logger.info.call_args_list]
                perf_messages = [msg for msg in logged_messages if "completed in" in msg and "s for" in msg]
                assert len(perf_messages) >= 1


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


class TestEnhancedDebateFormatIntegration:
    """Test enhanced debate format integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_llm_call_with_enhanced_prompt(self):
        """Test LLM call with enhanced debate format prompt"""
        env_vars = {
            "ENABLE_REAL_SUMMARIZATION": "true",
            "ENABLE_DEBATE_FORMAT": "true", 
            "GEMINI_API_KEY": "test-api-key-123"
        }
        
        with patch.dict(os.environ, env_vars):
            agent = SummarizationAgent()
            
            articles = [
                {"title": "Tech Article", "url": "http://example.com/1", "description": "Technology analysis"},
                {"title": "Business Article", "url": "http://example.com/2", "description": "Business perspective"}
            ]
            
            # Mock LLM response with enhanced format
            mock_enhanced_response = {
                "topic": "Technology and Business Analysis",
                "perspectives": [
                    {
                        "viewpoint": "Technology Optimists",
                        "position": "Technology drives business innovation",
                        "support_level": 0.7,
                        "arguments": [
                            {
                                "point": "Digital transformation increases efficiency",
                                "source_indices": [0, 1],
                                "strength": "strong"
                            }
                        ]
                    },
                    {
                        "viewpoint": "Cautious Adopters",
                        "position": "Technology adoption requires careful planning",
                        "support_level": 0.3,
                        "arguments": [
                            {
                                "point": "Implementation costs can be prohibitive",
                                "source_indices": [1],
                                "strength": "moderate"
                            }
                        ]
                    }
                ],
                "consensus_points": [
                    {
                        "point": "Technology investment is necessary for competitiveness",
                        "source_indices": [0, 1]
                    }
                ],
                "disputed_points": [
                    {
                        "point": "Timeline for return on investment",
                        "perspectives_involved": ["Technology Optimists", "Cautious Adopters"]
                    }
                ]
            }
            
            with patch.object(agent.client, 'call_llm') as mock_call_llm:
                mock_call_llm.return_value = json.dumps(mock_enhanced_response)
                
                result = await agent.summarize_articles(articles, "debate")
                
                # Verify enhanced format structure
                assert result["format"] == "debate"
                content = result["content"]
                assert content["topic"] == "Technology and Business Analysis"
                assert len(content["perspectives"]) == 2
                assert len(content["consensus_points"]) == 1
                assert len(content["disputed_points"]) == 1
                
                # Verify prompt was enhanced
                call_args = mock_call_llm.call_args[0]
                prompt = call_args[0]
                assert "perspectives" in prompt
                assert "source_indices" in prompt
                assert "consensus_points" in prompt
    
    @pytest.mark.asyncio
    async def test_output_validation_enhanced_format(self):
        """Test output validation for enhanced debate format"""
        env_vars = {
            "ENABLE_REAL_SUMMARIZATION": "false",
            "ENABLE_DEBATE_FORMAT": "true"
        }
        
        with patch.dict(os.environ, env_vars):
            agent = SummarizationAgent()
            
            # Test valid enhanced format
            valid_content = {
                "topic": "Test Topic",
                "perspectives": [
                    {
                        "viewpoint": "Test View",
                        "position": "Test Position",
                        "support_level": 0.5,
                        "arguments": [
                            {
                                "point": "Test Point",
                                "source_indices": [0],
                                "strength": "moderate"
                            }
                        ]
                    }
                ],
                "consensus_points": [
                    {
                        "point": "Test Consensus",
                        "source_indices": [0]
                    }
                ],
                "disputed_points": [
                    {
                        "point": "Test Dispute",
                        "perspectives_involved": ["Test View"]
                    }
                ]
            }
            
            assert agent._validate_output(valid_content, "debate") is True
            
            # Test invalid enhanced format (missing required field)
            invalid_content = {
                "topic": "Test Topic",
                "perspectives": []  # Missing other required fields
            }
            
            assert agent._validate_output(invalid_content, "debate") is False
    
    @pytest.mark.asyncio
    async def test_token_counting_and_limits(self):
        """Test token counting and monitoring"""
        env_vars = {
            "ENABLE_REAL_SUMMARIZATION": "true",
            "ENABLE_DEBATE_FORMAT": "true",
            "GEMINI_API_KEY": "test-api-key-123"
        }
        
        with patch.dict(os.environ, env_vars):
            agent = SummarizationAgent()
            
            # Verify max_output_tokens was increased to 2500
            assert agent.config.max_output_tokens == 2500
            
            articles = [
                {"title": "Article 1", "url": "http://example.com/1", "description": "Test description 1"},
                {"title": "Article 2", "url": "http://example.com/2", "description": "Test description 2"}
            ]
            
            with patch.object(agent.client, 'call_llm') as mock_call_llm, \
                 patch('summarization.logger') as mock_logger:
                
                mock_call_llm.return_value = '{"topic": "test", "perspectives": [], "consensus_points": [], "disputed_points": []}'
                
                await agent.summarize_articles(articles, "debate")
                
                # Check that token estimation logging occurred
                logged_messages = [call.args[0] for call in mock_logger.info.call_args_list]
                token_messages = [msg for msg in logged_messages if "Estimated prompt tokens" in msg]
                assert len(token_messages) >= 1


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