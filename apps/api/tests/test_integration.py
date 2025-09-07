"""
Integration tests for TruthLens API components
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Import modules to test
from orchestrator import OrchestratorAgent, orchestrate_query
from query import app


class TestOrchestratorIntegration:
    """Integration tests for Orchestrator-Retrieval interaction"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing"""
        return OrchestratorAgent()

    @pytest.mark.asyncio
    async def test_orchestrator_retrieval_integration_success(self, orchestrator):
        """Test successful integration between orchestrator and retrieval"""
        # Mock the fetch_articles function directly
        expected_sources = [
            {
                "url": "https://example.com/ai-breakthrough",
                "title": "AI Breakthrough in 2024",
                "isVerified": False,
            },
            {
                "url": "https://example.com/ml-evolution",
                "title": "Machine Learning Evolution",
                "isVerified": False,
            },
            {
                "url": "https://example.com/tech-update",
                "title": "Tech Industry Update",
                "isVerified": False,
            },
        ]

        with patch("orchestrator.fetch_articles", return_value=expected_sources):
            # Test orchestrator processing
            result = await orchestrator.process_query("artificial intelligence")

            # Verify structure
            assert "format" in result
            assert "content" in result
            assert "sources" in result
            assert result["format"] == "debate"

            # Verify content structure
            content = result["content"]
            assert "statement" in content
            assert "for" in content
            assert "against" in content
            assert isinstance(content["for"], list)
            assert isinstance(content["against"], list)

            # Verify sources
            sources = result["sources"]
            assert len(sources) == 3
            assert sources[0]["url"] == "https://example.com/ai-breakthrough"
            assert sources[0]["title"] == "AI Breakthrough in 2024"
            assert sources[0]["isVerified"] == False

            # Verify mock summary references actual sources
            assert "3 news sources" in content["statement"]
            assert len(content["for"]) > 0
            assert len(content["against"]) > 0

    @pytest.mark.asyncio
    async def test_orchestrator_handles_retrieval_errors(self, orchestrator):
        """Test orchestrator handles retrieval agent errors gracefully"""
        # Mock fetch_articles to raise an exception
        with patch("orchestrator.fetch_articles", side_effect=Exception("API Error")):
            result = await orchestrator.process_query("test query")

            # Should return error response with empty sources
            assert result["format"] == "debate"
            assert "Error processing query" in result["content"]["statement"]
            assert result["sources"] == []

    @pytest.mark.asyncio
    async def test_orchestrator_empty_results(self, orchestrator):
        """Test orchestrator handles empty results from retrieval"""
        with patch("orchestrator.fetch_articles", return_value=[]):
            result = await orchestrator.process_query("obscure query")

            # Should handle empty results gracefully
            assert result["format"] == "debate"
            assert result["sources"] == []
            assert "No articles found" in result["content"]["statement"]

    def test_mock_summary_generation_with_sources(self, orchestrator):
        """Test mock summary generation logic"""
        # Test with multiple sources
        sources = [
            {"title": "Source 1", "url": "https://example.com/1"},
            {"title": "Source 2", "url": "https://example.com/2"},
            {"title": "Source 3", "url": "https://example.com/3"},
            {"title": "Source 4", "url": "https://example.com/4"},
            {"title": "Source 5", "url": "https://example.com/5"},
        ]

        content = orchestrator._generate_mock_summary("test query", sources)

        assert "test query" in content["statement"]
        assert "5 sources" in content["statement"]
        assert len(content["for"]) >= 1
        assert len(content["against"]) >= 1

        # Verify references to actual sources
        for arg in content["for"]:
            assert any(source["title"] in arg for source in sources[:3])

    def test_mock_summary_generation_no_sources(self, orchestrator):
        """Test mock summary generation with no sources"""
        content = orchestrator._generate_mock_summary("test query", [])

        assert "No articles found" in content["statement"]
        assert "No supporting arguments available" in content["for"]
        assert "No opposing arguments available" in content["against"]


class TestEndToEndIntegration:
    """End-to-end integration tests through FastAPI"""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client"""
        return TestClient(app)

    def test_end_to_end_query_success(self, client):
        """Test complete end-to-end query processing"""
        expected_sources = [
            {
                "title": "Breaking News: AI Revolution",
                "url": "https://news.example.com/ai-revolution",
                "isVerified": False,
            },
            {
                "title": "Tech Industry Analysis",
                "url": "https://tech.example.com/industry-analysis",
                "isVerified": False,
            },
        ]

        # Mock the orchestrator function
        with patch(
            "query.orchestrate_query",
            return_value={
                "format": "debate",
                "content": {
                    "statement": "Analysis of 'artificial intelligence news' based on 2 sources",
                    "for": ["Supporting argument 1", "Supporting argument 2"],
                    "against": ["Opposing argument 1"],
                },
                "sources": expected_sources,
            },
        ):
            # Make API request
            response = client.post(
                "/api/query", json={"queryText": "artificial intelligence news"}
            )

            # Verify response
            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "format" in data
            assert "content" in data
            assert "sources" in data
            assert data["format"] == "debate"

            # Verify sources
            assert len(data["sources"]) == 2
            assert data["sources"][0]["title"] == "Breaking News: AI Revolution"
            assert data["sources"][0]["url"] == "https://news.example.com/ai-revolution"
            assert data["sources"][0]["isVerified"] == False

    def test_end_to_end_query_api_error(self, client):
        """Test end-to-end handling of API configuration errors"""
        # Mock orchestrator to raise exception
        with patch("query.orchestrate_query", side_effect=Exception("API Error")):
            response = client.post("/api/query", json={"queryText": "test query"})

            # Should return fallback response
            assert response.status_code == 200
            data = response.json()
            assert "Error processing query" in data["content"]["statement"]

    def test_end_to_end_query_validation(self, client):
        """Test request validation"""
        # Test missing queryText
        response = client.post("/api/query", json={})
        assert response.status_code == 422  # Validation error


class TestPerformanceIntegration:
    """Performance-related integration tests"""

    @pytest.mark.asyncio
    async def test_response_time_benchmark(self):
        """Test that response time meets performance requirements"""
        import time

        # Mock fast response
        with patch(
            "orchestrator.fetch_articles",
            return_value=[
                {
                    "title": "Fast Article",
                    "url": "https://example.com/fast",
                    "isVerified": False,
                }
            ],
        ):
            start_time = time.time()
            result = await orchestrate_query("performance test")
            end_time = time.time()

            # Should complete in under 3 seconds (performance requirement)
            assert (end_time - start_time) < 3.0
            assert result["format"] == "debate"

    @pytest.mark.asyncio
    async def test_large_response_handling(self):
        """Test handling of maximum response size"""
        # Mock response with 20 articles (max per requirements)
        large_sources = []
        for i in range(20):
            large_sources.append(
                {
                    "title": f"Article {i}",
                    "url": f"https://example.com/article{i}",
                    "isVerified": False,
                }
            )

        with patch("orchestrator.fetch_articles", return_value=large_sources):
            result = await orchestrate_query("large response test")

            # Should handle all 20 articles
            assert len(result["sources"]) == 20
            assert result["format"] == "debate"

            # Content should reference the number of sources
            assert "20 news sources" in result["content"]["statement"]


class TestRetrievalOrchestrationFlow:
    """Test the complete flow from query to orchestrator to retrieval"""

    @pytest.mark.asyncio
    async def test_orchestrator_calls_retrieval_correctly(self):
        """Test that orchestrator properly calls and processes retrieval results"""
        # Mock the retrieval function with realistic data
        mock_sources = [
            {
                "url": "https://techcrunch.com/ai-news",
                "title": "Latest AI Developments",
                "isVerified": False,
            },
            {
                "url": "https://arstechnica.com/machine-learning",
                "title": "Machine Learning Breakthrough",
                "isVerified": False,
            },
        ]

        with patch("orchestrator.fetch_articles") as mock_fetch:
            mock_fetch.return_value = mock_sources

            orchestrator = OrchestratorAgent()
            result = await orchestrator.process_query("AI technology")

            # Verify fetch_articles was called
            mock_fetch.assert_called_once_with("AI technology")

            # Verify orchestrator processed the results correctly
            assert result["sources"] == mock_sources
            assert result["format"] == "debate"
            assert "2 news sources" in result["content"]["statement"]

            # Verify mocked agents are kept as mocked (AC 3)
            content = result["content"]
            assert isinstance(content["for"], list)
            assert isinstance(content["against"], list)
            # Summary should be mock - new summarization agent uses generic mock content
            # This is expected behavior as per implementation
            assert len(content["for"]) >= 1
            assert len(content["against"]) >= 1

    @pytest.mark.asyncio
    async def test_data_format_consistency(self):
        """Test that data format is consistent between agents"""
        from retrieval import Source

        # Create sources using the actual Source model
        source_objects = [
            Source(url="https://example.com/1", title="Test 1", isVerified=False),
            Source(url="https://example.com/2", title="Test 2", isVerified=False),
        ]

        # Convert to dict format (as retrieval function does)
        sources_as_dicts = [source.model_dump() for source in source_objects]

        with patch("orchestrator.fetch_articles", return_value=sources_as_dicts):
            orchestrator = OrchestratorAgent()
            result = await orchestrator.process_query("format test")

            # Verify the data format is preserved through the pipeline
            assert len(result["sources"]) == 2
            for source in result["sources"]:
                assert "url" in source
                assert "title" in source
                assert "isVerified" in source
                assert (
                    source["isVerified"] == False
                )  # As per AC 3 (verification mocked)
