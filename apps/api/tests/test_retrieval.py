"""
Unit tests for Retrieval Agent
"""

import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException

# Import the modules to test
from retrieval import RetrievalAgent, Source, fetch_articles


class TestRetrievalAgent:
    """Test cases for RetrievalAgent class"""

    @pytest.fixture
    def agent(self):
        """Create a RetrievalAgent instance for testing"""
        with patch.dict(os.environ, {"NEWSAPI_KEY": "test_key"}):
            return RetrievalAgent()

    @pytest.fixture
    def mock_news_response(self):
        """Mock response from NewsAPI"""
        return {
            "status": "ok",
            "totalResults": 2,
            "articles": [
                {
                    "title": "Test Article 1",
                    "url": "https://example.com/article1",
                    "description": "Test description 1",
                    "publishedAt": "2024-01-01T00:00:00Z",
                },
                {
                    "title": "Test Article 2",
                    "url": "https://example.com/article2",
                    "description": "Test description 2",
                    "publishedAt": "2024-01-01T01:00:00Z",
                },
            ],
        }

    def test_initialization_with_api_key(self):
        """Test agent initializes correctly with API key"""
        with patch.dict(os.environ, {"NEWSAPI_KEY": "test_key"}):
            agent = RetrievalAgent()
            assert len(agent.apis) == 1
            assert agent.apis[0].name == "NewsAPI.org"
            assert agent.apis[0].api_key == "test_key"

    def test_initialization_without_api_key(self):
        """Test agent initializes with no APIs when key missing"""
        with patch.dict(os.environ, {}, clear=True):
            agent = RetrievalAgent()
            assert len(agent.apis) == 0

    @pytest.mark.asyncio
    async def test_fetch_articles_empty_query(self, agent):
        """Test error handling for empty query"""
        with pytest.raises(HTTPException) as exc_info:
            await agent.fetch_articles("")
        assert exc_info.value.status_code == 400
        assert "Query parameter is required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_fetch_articles_long_query(self, agent):
        """Test query truncation for long queries"""
        long_query = "x" * 600  # 600 characters

        # Mock the HTTP client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"articles": []}

        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_context)
            mock_context.__aexit__ = AsyncMock(return_value=False)
            mock_context.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_context

            await agent.fetch_articles(long_query)

            # Verify the query was truncated to 500 chars
            call_args = mock_context.get.call_args
            params = call_args[1]["params"]
            # URL-encoded query might be different length, but should be shorter
            assert len(params["q"]) <= 500

    @pytest.mark.asyncio
    async def test_fetch_articles_no_apis_configured(self):
        """Test error when no APIs are configured"""
        with patch.dict(os.environ, {}, clear=True):
            agent = RetrievalAgent()
            with pytest.raises(HTTPException) as exc_info:
                await agent.fetch_articles("test query")
            assert exc_info.value.status_code == 500
            assert "News API configuration error" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_fetch_articles_success(self, agent, mock_news_response):
        """Test successful article fetching"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_news_response

        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_context)
            mock_context.__aexit__ = AsyncMock(return_value=False)
            mock_context.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_context

            result = await agent.fetch_articles("test query")

            assert len(result) == 2
            assert result[0].title == "Test Article 1"
            assert result[0].url == "https://example.com/article1"
            assert result[0].isVerified == False
            assert result[1].title == "Test Article 2"
            assert result[1].url == "https://example.com/article2"
            assert result[1].isVerified == False

    @pytest.mark.asyncio
    async def test_fetch_articles_rate_limit(self, agent):
        """Test rate limiting handling"""
        mock_response = MagicMock()
        mock_response.status_code = 429

        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_context)
            mock_context.__aexit__ = AsyncMock(return_value=False)
            mock_context.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_context

            with pytest.raises(HTTPException) as exc_info:
                await agent.fetch_articles("test query")

            assert exc_info.value.status_code == 503
            assert "temporarily unavailable" in str(exc_info.value.detail)
            assert "Retry-After" in exc_info.value.headers

    @pytest.mark.asyncio
    async def test_fetch_articles_timeout(self, agent):
        """Test timeout handling"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_context)
            mock_context.__aexit__ = AsyncMock(return_value=False)
            mock_context.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client.return_value = mock_context

            with pytest.raises(HTTPException) as exc_info:
                await agent.fetch_articles("test query")

            assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_fetch_articles_api_error(self, agent):
        """Test API error handling"""
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_context)
            mock_context.__aexit__ = AsyncMock(return_value=False)
            mock_context.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_context

            result = await agent.fetch_articles("test query")
            assert result == []  # Should return empty list on API error

    @pytest.mark.asyncio
    async def test_fetch_articles_malformed_response(self, agent):
        """Test handling of malformed API response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "error": "Invalid response"
        }  # Missing articles key

        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_context)
            mock_context.__aexit__ = AsyncMock(return_value=False)
            mock_context.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_context

            result = await agent.fetch_articles("test query")
            assert result == []  # Should return empty list on malformed response

    def test_sanitize_query(self, agent):
        """Test query sanitization"""
        dangerous_query = "test'; DROP TABLE users; --"
        sanitized = agent._sanitize_query(dangerous_query)

        # Should remove dangerous characters
        assert "'" not in sanitized
        assert '"' not in sanitized
        assert ";" not in sanitized
        assert "--" not in sanitized

    def test_is_valid_url(self, agent):
        """Test URL validation"""
        assert agent._is_valid_url("https://example.com") == True
        assert agent._is_valid_url("http://example.com") == True
        assert agent._is_valid_url("ftp://example.com") == False
        assert agent._is_valid_url("") == False
        assert agent._is_valid_url(None) == False

    def test_transform_newsapi_response_missing_fields(self, agent):
        """Test transformation with missing required fields"""
        articles = [
            {"title": "Valid Article", "url": "https://example.com/valid"},
            {"title": "Missing URL"},  # No URL
            {"url": "https://example.com/no-title"},  # No title
            {"url": "invalid-url", "title": "Invalid URL"},  # Invalid URL
        ]

        result = agent._transform_newsapi_response(articles)

        # Should only return valid articles with fallback for missing title
        assert len(result) == 2
        assert result[0].title == "Valid Article"
        assert result[1].title  # Should have fallback title for missing title case

    def test_transform_newsapi_response_deduplication(self, agent):
        """Test deduplication of articles"""
        articles = [
            {"title": "Article 1", "url": "https://example.com/article1"},
            {"title": "Article 2", "url": "https://example.com/article2"},
            {
                "title": "Article 1 Duplicate",
                "url": "https://example.com/article1",
            },  # Duplicate URL
        ]

        result = agent._transform_newsapi_response(articles)

        # Should remove duplicate
        assert len(result) == 2
        assert result[0].url == "https://example.com/article1"
        assert result[1].url == "https://example.com/article2"

    def test_rate_limiting_cache(self, agent):
        """Test rate limiting cache functionality"""
        api_name = "test_api"

        # Initially not rate limited
        assert agent._is_rate_limited(api_name) == False

        # Add to cache
        agent._error_cache[api_name] = datetime.now()
        assert agent._is_rate_limited(api_name) == True

        # Expired cache entry
        agent._error_cache[api_name] = datetime.now() - timedelta(seconds=70)
        assert agent._is_rate_limited(api_name) == False
        assert api_name not in agent._error_cache  # Should be cleaned up


class TestFetchArticlesFunction:
    """Test the standalone fetch_articles function"""

    @pytest.mark.asyncio
    async def test_fetch_articles_function(self):
        """Test the FastAPI endpoint function"""
        with patch("retrieval.retrieval_agent.fetch_articles") as mock_fetch:
            mock_sources = [
                Source(url="https://example.com/1", title="Test 1", isVerified=False),
                Source(url="https://example.com/2", title="Test 2", isVerified=False),
            ]
            mock_fetch.return_value = mock_sources

            result = await fetch_articles("test query")

            assert len(result) == 2
            assert result[0]["url"] == "https://example.com/1"
            assert result[0]["title"] == "Test 1"
            assert result[0]["isVerified"] == False
