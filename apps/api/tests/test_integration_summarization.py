"""
Integration tests for Summarization Agent
Tests end-to-end flow: Retrieval → Verification → Summarization → UI
"""

import json
import os
import pytest
from unittest.mock import patch, AsyncMock

from orchestrator import OrchestratorAgent
from summarization import SummarizationAgent


class TestOrchestratorSummarizationIntegration:
    """Test integration between Orchestrator and Summarization agents"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_flow_mock_mode(self):
        """Test complete flow with summarization in mock mode"""
        orchestrator = OrchestratorAgent()
        
        # Mock the retrieval agent to return test data
        mock_articles = [
            {
                "title": "Climate Change Impact",
                "url": "http://example.com/climate1",
                "description": "Climate change is affecting global temperatures and weather patterns.",
                "publishedAt": "2025-01-07T10:00:00Z",
                "source": {"name": "Test News"}
            },
            {
                "title": "Green Energy Solutions",
                "url": "http://example.com/energy1", 
                "description": "Renewable energy sources are becoming more cost-effective and widespread.",
                "publishedAt": "2025-01-07T11:00:00Z",
                "source": {"name": "Energy Today"}
            }
        ]
        
        with patch('orchestrator.fetch_articles') as mock_fetch, \
             patch.dict(os.environ, {"ENABLE_REAL_SUMMARIZATION": "false"}):
            
            mock_fetch.return_value = mock_articles
            
            result = await orchestrator.process_query("climate change energy")
            
            # Verify complete response structure
            assert "format" in result
            assert "content" in result
            assert "sources" in result
            
            # Verify format
            assert result["format"] == "debate"
            
            # Verify content structure for debate format
            content = result["content"]
            assert "statement" in content
            assert "for" in content
            assert "against" in content
            assert isinstance(content["for"], list)
            assert isinstance(content["against"], list)
            
            # Verify sources are preserved
            sources = result["sources"]
            assert len(sources) == 2
            assert sources[0]["title"] == "Climate Change Impact"
            assert sources[0]["url"] == "http://example.com/climate1"
            assert sources[0]["isVerified"] is False
            assert sources[1]["title"] == "Green Energy Solutions"
            assert sources[1]["url"] == "http://example.com/energy1"
            assert sources[1]["isVerified"] is False
    
    @pytest.mark.asyncio
    async def test_end_to_end_flow_with_llm_enabled(self):
        """Test complete flow with LLM enabled (mocked LLM response)"""
        orchestrator = OrchestratorAgent()
        
        mock_articles = [
            {
                "title": "AI Technology Progress",
                "url": "http://example.com/ai1",
                "description": "Artificial intelligence is advancing rapidly with new breakthroughs.",
                "publishedAt": "2025-01-07T12:00:00Z",
                "source": {"name": "Tech Weekly"}
            }
        ]
        
        # Mock LLM response
        mock_llm_response = {
            "statement": "AI technology is rapidly evolving with significant implications",
            "for": [
                "AI breakthrough in machine learning shows 40% improvement",
                "New AI models demonstrate enhanced reasoning capabilities", 
                "Industry adoption of AI increasing productivity by 25%"
            ],
            "against": [
                "AI development raises concerns about job displacement",
                "Ethical implications of AI decision-making remain unresolved",
                "Technical limitations still present in current AI systems"
            ]
        }
        
        with patch('orchestrator.fetch_articles') as mock_fetch, \
             patch('summarization.summarization_agent._is_enabled', True), \
             patch('summarization.summarization_agent.config.is_configured', return_value=True), \
             patch('summarization.LLMClient.call_llm') as mock_llm_call:
            
            mock_fetch.return_value = mock_articles
            mock_llm_call.return_value = json.dumps(mock_llm_response)
            
            result = await orchestrator.process_query("AI technology")
            
            # Verify LLM-generated content is used
            assert result["format"] == "debate"
            content = result["content"]
            assert content["statement"] == mock_llm_response["statement"]
            assert len(content["for"]) == 3
            assert len(content["against"]) == 3
            assert "AI breakthrough" in content["for"][0]
            
            # Verify sources are still preserved
            assert len(result["sources"]) == 1
            assert result["sources"][0]["title"] == "AI Technology Progress"
    
    @pytest.mark.asyncio
    async def test_venn_diagram_format_integration(self):
        """Test integration with venn_diagram format"""
        # Test direct summarization agent call with venn_diagram format
        agent = SummarizationAgent()
        
        mock_articles = [
            {
                "title": "Democrats Climate Policy",
                "url": "http://example.com/dem1",
                "description": "Democratic climate policies focus on renewable energy investment."
            },
            {
                "title": "Republican Climate Position", 
                "url": "http://example.com/rep1",
                "description": "Republican climate position emphasizes economic considerations."
            }
        ]
        
        with patch.dict(os.environ, {"ENABLE_REAL_SUMMARIZATION": "false"}):
            result = await agent.summarize_articles(mock_articles, "venn_diagram")
            
            assert result["format"] == "venn_diagram"
            content = result["content"]
            
            # Verify venn diagram structure
            assert "topic_a" in content
            assert "topic_b" in content
            assert "unique_a" in content
            assert "unique_b" in content
            assert "common" in content
            
            # Verify all fields are lists or strings as expected
            assert isinstance(content["topic_a"], str)
            assert isinstance(content["topic_b"], str)
            assert isinstance(content["unique_a"], list)
            assert isinstance(content["unique_b"], list)
            assert isinstance(content["common"], list)
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error handling across the integration"""
        orchestrator = OrchestratorAgent()
        
        # Test when retrieval fails
        with patch('orchestrator.fetch_articles') as mock_fetch:
            mock_fetch.side_effect = Exception("NewsAPI unavailable")
            
            result = await orchestrator.process_query("test query")
            
            # Should get error fallback response
            assert result["format"] == "debate"
            assert "Error processing query" in result["content"]["statement"]
            assert result["sources"] == []
    
    @pytest.mark.asyncio
    async def test_empty_articles_integration(self):
        """Test integration when no articles are retrieved"""
        orchestrator = OrchestratorAgent()
        
        with patch('orchestrator.fetch_articles') as mock_fetch, \
             patch.dict(os.environ, {"ENABLE_REAL_SUMMARIZATION": "false"}):
            
            mock_fetch.return_value = []  # No articles found
            
            result = await orchestrator.process_query("obscure topic")
            
            # Should handle empty articles gracefully
            assert result["format"] == "debate"
            assert result["sources"] == []
            assert "No articles" in result["content"]["statement"]
    
    @pytest.mark.asyncio
    async def test_performance_integration(self):
        """Test performance requirements in integration scenario"""
        import time
        
        orchestrator = OrchestratorAgent()
        
        # Create larger dataset to test performance
        mock_articles = [
            {
                "title": f"Article {i}",
                "url": f"http://example.com/{i}",
                "description": f"Detailed description for article {i}. " * 10,  # Make descriptions longer
                "publishedAt": "2025-01-07T12:00:00Z",
                "source": {"name": f"Source {i}"}
            }
            for i in range(20)  # 20 articles
        ]
        
        with patch('orchestrator.fetch_articles') as mock_fetch, \
             patch.dict(os.environ, {"ENABLE_REAL_SUMMARIZATION": "false"}):
            
            mock_fetch.return_value = mock_articles
            
            start_time = time.time()
            result = await orchestrator.process_query("performance test query")
            end_time = time.time()
            
            # Verify performance requirement (< 15 seconds total)
            duration = end_time - start_time
            assert duration < 15.0, f"Performance requirement failed: {duration}s > 15s"
            
            # Verify all articles were processed
            assert len(result["sources"]) == 20
            assert result["format"] == "debate"


class TestSummarizationDataModelCompliance:
    """Test compliance with Summary and Source data models"""
    
    @pytest.mark.asyncio
    async def test_summary_data_model_compliance(self):
        """Test that summarization output matches Summary data model"""
        agent = SummarizationAgent()
        
        mock_articles = [
            {
                "title": "Test Article",
                "url": "http://example.com/test",
                "description": "Test description for data model validation"
            }
        ]
        
        with patch.dict(os.environ, {"ENABLE_REAL_SUMMARIZATION": "false"}):
            # Test debate format
            result = await agent.summarize_articles(mock_articles, "debate")
            
            # Verify Summary interface compliance
            assert "format" in result
            assert "content" in result
            assert "sources" in result
            
            assert result["format"] in ["debate", "venn_diagram"]
            assert isinstance(result["content"], dict)
            assert isinstance(result["sources"], list)
            
            # Test venn_diagram format
            result_venn = await agent.summarize_articles(mock_articles, "venn_diagram")
            
            assert result_venn["format"] == "venn_diagram"
            assert isinstance(result_venn["content"], dict)
            assert isinstance(result_venn["sources"], list)
    
    @pytest.mark.asyncio
    async def test_source_data_model_compliance(self):
        """Test that Source objects match the Source data model"""
        agent = SummarizationAgent()
        
        mock_articles = [
            {
                "title": "Source Model Test",
                "url": "http://example.com/source",
                "description": "Testing source data model compliance"
            }
        ]
        
        with patch.dict(os.environ, {"ENABLE_REAL_SUMMARIZATION": "false"}):
            result = await agent.summarize_articles(mock_articles, "debate")
            
            sources = result["sources"]
            assert len(sources) == 1
            
            source = sources[0]
            
            # Verify Source interface compliance
            assert "url" in source
            assert "title" in source
            assert "isVerified" in source
            
            assert isinstance(source["url"], str)
            assert isinstance(source["title"], str)
            assert isinstance(source["isVerified"], bool)
            
            # Verify specific values
            assert source["url"] == "http://example.com/source"
            assert source["title"] == "Source Model Test"
            assert source["isVerified"] is False  # Per story requirement
            
            # biasScore should be omitted (optional field)
            assert "biasScore" not in source or source.get("biasScore") is None


class TestFeatureFlagScenarios:
    """Test various feature flag scenarios"""
    
    @pytest.mark.asyncio
    async def test_feature_flag_environment_variations(self):
        """Test different feature flag environment variable formats"""
        agent_class = SummarizationAgent
        
        test_cases = [
            ("true", True),
            ("1", True), 
            ("yes", True),
            ("on", True),
            ("TRUE", True),
            ("false", False),
            ("0", False),
            ("no", False),
            ("off", False),
            ("FALSE", False),
            ("", False),
            ("invalid", False)
        ]
        
        for flag_value, expected_enabled in test_cases:
            with patch.dict(os.environ, {"ENABLE_REAL_SUMMARIZATION": flag_value}):
                agent = agent_class()
                assert agent._is_enabled == expected_enabled, f"Flag '{flag_value}' should be {expected_enabled}"
    
    @pytest.mark.asyncio
    async def test_feature_flag_missing_environment(self):
        """Test behavior when feature flag environment variable is missing"""
        with patch.dict(os.environ, {}, clear=True):
            agent = SummarizationAgent()
            # Should default to False when environment variable is missing
            assert agent._is_enabled is False


if __name__ == "__main__":
    pytest.main([__file__])