"""
Retrieval Agent for TruthLens
Handles fetching articles from configured news APIs
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
# urllib.parse import removed - httpx handles URL encoding

import httpx
from fastapi import HTTPException
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Data Models
class Source(BaseModel):
    """Source model matching TypeScript interface"""

    url: str
    title: str
    isVerified: bool = False  # Default to False as per story requirements
    biasScore: Optional[float] = None  # Optional for future use


class NewsAPIConfig(BaseModel):
    """Configuration for a news API"""

    name: str
    api_key: str
    base_url: str
    enabled: bool = True
    rate_limit: int = 100  # requests per day
    timeout: int = 8  # seconds


class RetrievalAgent:
    """Agent for retrieving news articles from configured APIs"""

    def __init__(self):
        """Initialize the retrieval agent with configured APIs"""
        self.apis: List[NewsAPIConfig] = []
        self._error_cache: Dict[str, datetime] = {}  # Cache for rate limit errors
        self._configure_apis()

    def _configure_apis(self):
        """Configure available news APIs"""
        # NewsAPI.org configuration (recommended in story)
        newsapi_key = os.getenv("NEWSAPI_KEY", "")
        if newsapi_key:
            self.apis.append(
                NewsAPIConfig(
                    name="NewsAPI.org",
                    api_key=newsapi_key,
                    base_url="https://newsapi.org/v2",
                    enabled=True,
                    rate_limit=100,
                )
            )
            logger.info("NewsAPI.org configured successfully")
        else:
            logger.warning("NEWSAPI_KEY not found in environment variables")

    async def fetch_articles(self, query: str) -> List[Source]:
        """
        Fetch articles from configured news APIs

        Args:
            query: Search query string

        Returns:
            List of Source objects matching the query

        Raises:
            HTTPException: For various error conditions
        """
        # Input validation
        if not query:
            raise HTTPException(status_code=400, detail="Query parameter is required")

        # Truncate query if too long
        if len(query) > 500:
            logger.warning(f"Query truncated from {len(query)} to 500 characters")
            query = query[:500]

        # Sanitize query
        query = self._sanitize_query(query)

        # Check for configured APIs
        enabled_apis = [api for api in self.apis if api.enabled]
        if not enabled_apis:
            logger.error("No news APIs configured")
            raise HTTPException(status_code=500, detail="News API configuration error")

        # Use the first enabled API (NewsAPI.org if configured)
        api_config = enabled_apis[0]

        # Check error cache for rate limiting
        if self._is_rate_limited(api_config.name):
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable, please try again later",
                headers={"Retry-After": "60"},
            )

        try:
            articles = await self._fetch_from_newsapi(api_config, query)
            return articles
        except HTTPException:
            # Re-raise HTTP exceptions (rate limits, timeouts)
            raise
        except Exception as e:
            logger.error(f"Error fetching articles: {str(e)}")
            # Return empty list for other errors
            return []

    def _sanitize_query(self, query: str) -> str:
        """Sanitize query to prevent injection attacks"""
        # Remove potentially dangerous characters
        dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "\\"]
        sanitized = query
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")

        # Return sanitized query without URL encoding (httpx will handle encoding)
        return sanitized

    def _is_rate_limited(self, api_name: str) -> bool:
        """Check if API is currently rate limited"""
        if api_name in self._error_cache:
            # Check if 60 seconds have passed
            if datetime.now() - self._error_cache[api_name] < timedelta(seconds=60):
                return True
            else:
                # Clear expired cache entry
                del self._error_cache[api_name]
        return False

    async def _fetch_from_newsapi(
        self, config: NewsAPIConfig, query: str
    ) -> List[Source]:
        """
        Fetch articles from NewsAPI.org

        Args:
            config: API configuration
            query: Search query

        Returns:
            List of Source objects
        """
        url = f"{config.base_url}/everything"
        params = {
            "q": query,
            "apiKey": config.api_key,
            "sortBy": "publishedAt",
            "pageSize": 20,  # Limit to 20 articles as per requirements
            "language": "en",
        }

        async with httpx.AsyncClient(timeout=config.timeout) as client:
            try:
                response = await client.get(url, params=params)

                # Handle rate limiting
                if response.status_code == 429:
                    self._error_cache[config.name] = datetime.now()
                    raise HTTPException(
                        status_code=503,
                        detail="Service temporarily unavailable, please try again later",
                        headers={"Retry-After": "60"},
                    )

                # Handle other errors
                if response.status_code != 200:
                    logger.error(f"API returned status {response.status_code}")
                    return []

                data = response.json()

                # Validate response structure
                if "articles" not in data:
                    logger.error("Invalid API response structure")
                    return []

                # Transform to Source objects
                sources = self._transform_newsapi_response(data["articles"])
                return sources

            except httpx.TimeoutException:
                logger.error("API request timeout")
                raise HTTPException(
                    status_code=503, detail="Service temporarily unavailable"
                )
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                return []

    def _transform_newsapi_response(
        self, articles: List[Dict[str, Any]]
    ) -> List[Source]:
        """
        Transform NewsAPI response to Source objects

        Args:
            articles: List of article dictionaries from NewsAPI

        Returns:
            List of Source objects
        """
        sources = []
        seen_urls = set()  # For deduplication

        for article in articles[:20]:  # Limit to 20 articles
            # Skip if missing required fields
            url = article.get("url")
            if not url or not self._is_valid_url(url):
                logger.debug(f"Skipping article with invalid URL: {url}")
                continue

            # Skip duplicates
            if url in seen_urls:
                logger.debug(f"Skipping duplicate article: {url}")
                continue
            seen_urls.add(url)

            # Get title or use fallback
            title = article.get("title")
            if not title:
                description = article.get("description", "")
                title = description[:100] if description else "Untitled"

            # Create Source object
            source = Source(
                url=url,
                title=title,
                isVerified=False,  # Always False for now as per requirements
                biasScore=None,  # Not implemented yet
            )
            sources.append(source)

        logger.info(f"Transformed {len(sources)} articles from API response")
        return sources

    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        if not url:
            return False
        return url.startswith("http://") or url.startswith("https://")


# FastAPI endpoint interface
retrieval_agent = RetrievalAgent()


async def fetch_articles(query: str) -> List[Dict[str, Any]]:
    """
    FastAPI endpoint function for fetching articles

    Args:
        query: Search query from orchestrator

    Returns:
        List of article dictionaries
    """
    sources = await retrieval_agent.fetch_articles(query)
    # Convert to dict for JSON serialization
    return [source.model_dump() for source in sources]
