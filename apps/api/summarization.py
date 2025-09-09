"""
Summarization Agent for TruthLens
Generates AI-powered summaries using LLM integration with feature flag support
Enhanced with multi-perspective debate format capability
"""

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import aiohttp
from fastapi import HTTPException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMConfig:
    """Configuration for LLM API integration"""
    
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.model = "gemini-1.5-flash"
        self.timeout = 12  # seconds (within 15s requirement)
        self.max_output_tokens = 2500  # Increased from 1500 for debate format
        self.temperature = 0.7
        
    def is_configured(self) -> bool:
        """Check if LLM API is properly configured"""
        return bool(self.gemini_api_key and self.gemini_api_key != "your_gemini_key_here")


class PromptTemplates:
    """Prompt templates for different summary formats"""
    
    @staticmethod
    def debate_format(query: str, articles: List[Dict], use_enhanced: bool = False) -> str:
        """Generate prompt for debate format summary"""
        articles_text = ""
        for i, article in enumerate(articles[:5], 1):  # Limit to 5 articles for token management
            articles_text += f"\n{i}. {article.get('title', 'No title')}\n"
            articles_text += f"   URL: {article.get('url', 'No URL')}\n"
            articles_text += f"   Content: {article.get('description', 'No description')[:200]}...\n"
        
        if use_enhanced:
            # Enhanced multi-perspective debate format
            return f"""
Analyze these news articles about "{query}" and create a multi-perspective debate summary.

Articles:
{articles_text}

Generate a JSON response with 2-3 distinct perspectives. Each perspective should represent a different viewpoint found in the articles.

EXACT FORMAT REQUIRED:
{{
  "topic": "{query}",
  "perspectives": [
    {{
      "viewpoint": "Name/label for this perspective (e.g., 'Economic Growth Advocates')",
      "position": "Main thesis in 100 chars",
      "support_level": 0.0,
      "arguments": [
        {{
          "point": "Specific argument under 150 chars",
          "source_indices": [0, 1],
          "strength": "strong"
        }}
      ]
    }}
  ],
  "consensus_points": [
    {{
      "point": "Area of agreement under 100 chars",
      "source_indices": [0, 1, 2]
    }}
  ],
  "disputed_points": [
    {{
      "point": "Area of disagreement under 100 chars",
      "perspectives_involved": ["Viewpoint A name", "Viewpoint B name"]
    }}
  ]
}}

Requirements:
- Find 2-3 distinct perspectives from the articles
- Each perspective needs 2-3 arguments with source attribution
- support_level should be 0.0 to 1.0 based on source count supporting this perspective
- strength should be "strong", "moderate", or "weak"
- Use source_indices (0-based) to reference the article list
- Identify at least 1 consensus point and 1 disputed point
- Keep all text concise (character limits specified)
- Return ONLY valid JSON, no additional text
"""
        else:
            # Original simple debate format for backward compatibility
            return f"""
Analyze the following news articles about "{query}" and create a balanced debate summary.

Articles:
{articles_text}

Please provide a JSON response in this exact format:
{{
    "statement": "Clear thesis statement about {query}",
    "for": [
        "Supporting argument 1 with specific reference to sources",
        "Supporting argument 2 with specific reference to sources",
        "Supporting argument 3 with specific reference to sources"
    ],
    "against": [
        "Counter-argument 1 with specific reference to sources", 
        "Counter-argument 2 with specific reference to sources",
        "Counter-argument 3 with specific reference to sources"
    ]
}}

Requirements:
- Reference specific articles in your arguments
- Be factual and balanced
- Provide 3 arguments for each side
- Keep each argument under 150 characters
- Return only valid JSON
"""
    
    @staticmethod
    def venn_diagram_format(query: str, articles: List[Dict]) -> str:
        """Generate prompt for venn diagram format summary"""
        articles_text = ""
        for i, article in enumerate(articles[:5], 1):
            articles_text += f"\n{i}. {article.get('title', 'No title')}\n"
            articles_text += f"   URL: {article.get('url', 'No URL')}\n"
            articles_text += f"   Content: {article.get('description', 'No description')[:200]}...\n"
        
        return f"""
Analyze the following news articles about "{query}" and create a comparison summary suitable for a Venn diagram visualization.

Articles:
{articles_text}

Please provide a JSON response in this exact format:
{{
    "topic_a": "First perspective or entity name",
    "topic_b": "Second perspective or entity name", 
    "unique_a": [
        "Point unique to topic A",
        "Another unique point for A",
        "Third unique point for A"
    ],
    "unique_b": [
        "Point unique to topic B",
        "Another unique point for B", 
        "Third unique point for B"
    ],
    "common": [
        "Shared point between both topics",
        "Another shared point",
        "Third shared point"
    ]
}}

Requirements:
- Find two main perspectives/entities to compare
- Identify what's unique to each and what they share
- Reference the articles in your analysis
- Keep each point under 100 characters
- Return only valid JSON
"""


class LLMClient:
    """HTTP client for LLM API calls with error handling and retries"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def close(self):
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup"""
        await self.close()
    
    async def call_llm(self, prompt: str, max_retries: int = 3) -> str:
        """
        Call Gemini LLM API with exponential backoff retry logic
        
        Args:
            prompt: The prompt to send to the LLM
            max_retries: Maximum number of retry attempts
            
        Returns:
            LLM response text
            
        Raises:
            HTTPException: On API errors, authentication issues, or timeouts
        """
        if not self.config.is_configured():
            raise HTTPException(
                status_code=500,
                detail="AI summarization service configuration error"
            )
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": self.config.temperature,
                "maxOutputTokens": self.config.max_output_tokens,
                "responseMimeType": "application/json"
            }
        }
        
        session = await self._get_session()
        
        # Construct URL with API key as query parameter (Gemini style)
        url = f"{self.config.gemini_base_url}/{self.config.model}:generateContent"
        params = {"key": self.config.gemini_api_key}
        
        for attempt in range(max_retries + 1):
            try:
                async with session.post(
                    url,
                    headers=headers,
                    json=payload,
                    params=params
                ) as response:
                    
                    if response.status == 401:
                        logger.error("LLM API authentication failed")
                        raise HTTPException(
                            status_code=500,
                            detail="AI summarization service configuration error"
                        )
                    
                    elif response.status == 429:
                        # Rate limit exceeded
                        retry_after = response.headers.get("retry-after", "60")
                        logger.warning(f"LLM API rate limit exceeded. Retry after: {retry_after}s")
                        
                        if attempt < max_retries:
                            # Exponential backoff with jitter
                            delay = min(2 ** attempt + (attempt * 0.1), 8)
                            logger.info(f"Retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            raise HTTPException(
                                status_code=503,
                                detail="AI service temporarily busy, please try again later",
                                headers={"Retry-After": retry_after}
                            )
                    
                    elif response.status >= 500:
                        # Server error
                        logger.error(f"LLM API server error: {response.status}")
                        if attempt < max_retries:
                            delay = min(2 ** attempt, 4)
                            await asyncio.sleep(delay)
                            continue
                        else:
                            raise HTTPException(
                                status_code=503,
                                detail="AI service temporarily unavailable"
                            )
                    
                    elif response.status == 400:
                        # Bad request - could be content filtering
                        error_data = await response.json()
                        error_type = error_data.get("error", {}).get("type", "")
                        
                        if "content_filter" in error_type or "policy" in error_type.lower():
                            logger.warning("Content filtering triggered by LLM API")
                            raise HTTPException(
                                status_code=400,
                                detail="Content cannot be summarized due to policy restrictions"
                            )
                        else:
                            logger.error(f"LLM API bad request: {error_data}")
                            raise HTTPException(
                                status_code=500,
                                detail="AI summarization request error"
                            )
                    
                    elif response.status == 200:
                        # Success - Parse Gemini response format
                        data = await response.json()
                        candidates = data.get("candidates", [])
                        if candidates and len(candidates) > 0:
                            content = candidates[0].get("content", {})
                            parts = content.get("parts", [])
                            if parts and len(parts) > 0:
                                return parts[0].get("text", "")
                        
                        logger.error(f"Unexpected Gemini response format: {data}")
                        raise HTTPException(
                            status_code=500,
                            detail="AI summarization response format error"
                        )
                    
                    else:
                        # Other HTTP errors
                        logger.error(f"Unexpected LLM API response: {response.status}")
                        raise HTTPException(
                            status_code=500,
                            detail="AI summarization service error"
                        )
                        
            except asyncio.TimeoutError:
                logger.error(f"LLM API timeout (attempt {attempt + 1})")
                if attempt < max_retries:
                    delay = min(2 ** attempt, 4)
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise HTTPException(
                        status_code=503,
                        detail="AI service timeout - please try again"
                    )
            
            except aiohttp.ClientError as e:
                logger.error(f"LLM API connection error: {str(e)}")
                if attempt < max_retries:
                    delay = min(2 ** attempt, 4)
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise HTTPException(
                        status_code=503,
                        detail="AI service connection error"
                    )


class SummarizationAgent:
    """Main summarization agent with LLM integration and feature flag support"""
    
    def __init__(self):
        self.config = LLMConfig()
        self.client = LLMClient(self.config)
        self.templates = PromptTemplates()
        self._is_enabled = self._check_feature_flag()
        self._debate_format_enabled = self._check_debate_format_flag()
    
    def _check_feature_flag(self) -> bool:
        """Check if real LLM summarization is enabled"""
        flag_value = os.getenv("ENABLE_REAL_SUMMARIZATION", "false").lower()
        enabled = flag_value in ("true", "1", "yes", "on")
        logger.info(f"Real summarization feature flag: {'enabled' if enabled else 'disabled'}")
        return enabled
    
    def _check_debate_format_flag(self) -> bool:
        """Check if enhanced debate format is enabled"""
        flag_value = os.getenv("ENABLE_DEBATE_FORMAT", "false").lower()
        enabled = flag_value in ("true", "1", "yes", "on")
        logger.info(f"Enhanced debate format feature flag: {'enabled' if enabled else 'disabled'}")
        return enabled
    
    def _validate_input(self, articles: List[Dict[str, Any]], format_type: str) -> None:
        """Validate input parameters for security"""
        # Validate articles structure
        if not isinstance(articles, list):
            raise HTTPException(status_code=400, detail="Articles must be a list")
        
        # Validate format type
        if format_type not in ["debate", "venn_diagram"]:
            raise HTTPException(status_code=400, detail="Invalid format type. Must be 'debate' or 'venn_diagram'")
        
        # Validate article structure and content
        for i, article in enumerate(articles):
            if not isinstance(article, dict):
                raise HTTPException(status_code=400, detail=f"Article {i} must be a dictionary")
            
            # Check for required fields and validate content
            title = article.get("title", "")
            url = article.get("url", "")
            description = article.get("description", "")
            
            # Basic input sanitization - check for excessive length
            if len(str(title)) > 500:
                raise HTTPException(status_code=400, detail=f"Article {i} title too long")
            if len(str(url)) > 1000:
                raise HTTPException(status_code=400, detail=f"Article {i} URL too long")
            if len(str(description)) > 5000:
                raise HTTPException(status_code=400, detail=f"Article {i} description too long")
    
    def _validate_output(self, content: Dict[str, Any], format_type: str) -> bool:
        """Validate output structure and content for security"""
        try:
            if format_type == "debate":
                if self._debate_format_enabled:
                    # Validate enhanced debate format
                    required_fields = ["topic", "perspectives", "consensus_points", "disputed_points"]
                    for field in required_fields:
                        if field not in content:
                            logger.warning(f"Missing required field in enhanced debate format: {field}")
                            return False
                    
                    # Validate perspectives structure
                    perspectives = content.get("perspectives", [])
                    if not isinstance(perspectives, list) or len(perspectives) < 1:
                        logger.warning("Invalid perspectives structure in enhanced debate format")
                        return False
                    
                    for perspective in perspectives:
                        if not isinstance(perspective, dict):
                            return False
                        required_perspective_fields = ["viewpoint", "position", "support_level", "arguments"]
                        for field in required_perspective_fields:
                            if field not in perspective:
                                return False
                else:
                    # Validate simple debate format
                    required_fields = ["statement", "for", "against"]
                    for field in required_fields:
                        if field not in content:
                            logger.warning(f"Missing required field in simple debate format: {field}")
                            return False
            
            elif format_type == "venn_diagram":
                required_fields = ["topic_a", "topic_b", "unique_a", "unique_b", "common"]
                for field in required_fields:
                    if field not in content:
                        logger.warning(f"Missing required field in venn diagram format: {field}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Output validation error: {e}")
            return False
    
    async def summarize_articles(
        self, 
        articles: List[Dict[str, Any]], 
        format_type: str = "debate"
    ) -> Dict[str, Any]:
        """
        Generate summary from articles using LLM or fallback to mock
        Enhanced with multi-perspective debate format capability
        
        Args:
            articles: List of article dictionaries with title, url, description
            format_type: 'debate' or 'venn_diagram'
            
        Returns:
            Summary dictionary matching the Summary data model
        """
        start_time = time.time()  # Performance monitoring
        logger.info(f"Summarizing {len(articles)} articles in {format_type} format")
        
        # Input validation for security
        self._validate_input(articles, format_type)
        
        # Handle empty articles
        if not articles:
            return {
                "format": format_type,
                "content": self._empty_content(format_type),
                "sources": []
            }
        
        # Convert articles to sources format
        sources = self._articles_to_sources(articles)
        
        try:
            if self._is_enabled and self.config.is_configured():
                # Use real LLM summarization
                content = await self._generate_llm_summary(articles, format_type)
            else:
                # Use mock summarization as fallback
                content = self._generate_mock_summary(articles, format_type)
            
            # Validate output structure
            if not self._validate_output(content, format_type):
                logger.warning("Output validation failed, falling back to mock")
                content = self._generate_mock_summary(articles, format_type)
            
            # Log performance metrics
            end_time = time.time()
            response_time = end_time - start_time
            logger.info(f"Summarization completed in {response_time:.2f}s for {len(articles)} articles")
            
            return {
                "format": format_type,
                "content": content,
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"Summarization error: {str(e)}")
            # Fallback to mock on any error
            end_time = time.time()
            response_time = end_time - start_time
            logger.info(f"Summarization fallback completed in {response_time:.2f}s")
            
            return {
                "format": format_type,
                "content": self._generate_mock_summary(articles, format_type),
                "sources": sources
            }
    
    async def _generate_llm_summary(self, articles: List[Dict], format_type: str) -> Dict[str, Any]:
        """Generate summary using real LLM API"""
        query = "news analysis"  # Default query - could be passed as parameter
        
        # TODO: Future caching implementation for Epic 3/4
        # Consider Redis or in-memory cache for common queries to improve response times
        # Cache key could be hash of articles + format_type + feature flags
        # Cache TTL should consider news freshness requirements
        
        # Generate appropriate prompt based on format and feature flags
        if format_type == "venn_diagram":
            prompt = self.templates.venn_diagram_format(query, articles)
        else:
            # Use enhanced debate format if flag is enabled
            use_enhanced = self._debate_format_enabled
            prompt = self.templates.debate_format(query, articles, use_enhanced)
        
        # Token counting for monitoring (basic estimate)
        prompt_token_estimate = len(prompt.split()) * 1.3  # Rough estimate
        logger.info(f"Estimated prompt tokens: {prompt_token_estimate:.0f}, max output: {self.config.max_output_tokens}")
        
        # Call LLM API with proper session management
        try:
            response_text = await self.client.call_llm(prompt)
            
            # Parse JSON response
            try:
                content = json.loads(response_text.strip())
                logger.info("Successfully parsed LLM response")
                return content
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM JSON response: {e}")
                logger.warning(f"Raw response: {response_text[:200]}...")
                
                # Attempt to extract JSON from text
                content = self._extract_json_from_text(response_text, format_type)
                if content:
                    return content
                
                # Fallback to mock if parsing completely fails
                logger.error("Could not parse LLM response, falling back to mock")
                return self._generate_mock_summary(articles, format_type)
                
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            # Ensure session is cleaned up on error
            await self.client.close()
            raise
    
    def _extract_json_from_text(self, text: str, format_type: str) -> Optional[Dict[str, Any]]:
        """Attempt to extract JSON from malformed LLM response"""
        try:
            # Look for JSON-like content between braces
            start = text.find("{")
            end = text.rfind("}") + 1
            
            if start != -1 and end > start:
                json_text = text[start:end]
                return json.loads(json_text)
                
        except Exception as e:
            logger.warning(f"JSON extraction failed: {e}")
        
        return None
    
    def _generate_mock_summary(self, articles: List[Dict], format_type: str) -> Dict[str, Any]:
        """Generate mock summary for fallback or when feature is disabled"""
        if format_type == "venn_diagram":
            return {
                "topic_a": "Perspective A",
                "topic_b": "Perspective B",
                "unique_a": [
                    "Point unique to first perspective",
                    "Another unique point for A", 
                    "Third unique point for A"
                ],
                "unique_b": [
                    "Point unique to second perspective",
                    "Another unique point for B",
                    "Third unique point for B"
                ],
                "common": [
                    "Shared point between perspectives",
                    "Common ground found",
                    "Mutual understanding area"
                ]
            }
        else:
            # Debate format - check if enhanced format is enabled
            if self._debate_format_enabled:
                # Enhanced multi-perspective mock format
                return {
                    "topic": f"Analysis of {len(articles)} news sources",
                    "perspectives": [
                        {
                            "viewpoint": "Supporting Perspective", 
                            "position": "Positive stance based on available sources",
                            "support_level": 0.6,
                            "arguments": [
                                {
                                    "point": "Evidence supports this viewpoint from multiple sources",
                                    "source_indices": list(range(min(len(articles), 3))),
                                    "strength": "strong"
                                },
                                {
                                    "point": "Additional supporting evidence found", 
                                    "source_indices": list(range(min(1, len(articles)), min(len(articles), 4))),
                                    "strength": "moderate"
                                }
                            ]
                        },
                        {
                            "viewpoint": "Alternative Perspective",
                            "position": "Different stance highlighting opposing views", 
                            "support_level": 0.4,
                            "arguments": [
                                {
                                    "point": "Counter-evidence presents different angle",
                                    "source_indices": list(range(min(2, len(articles)), min(len(articles), 5))),
                                    "strength": "moderate"
                                }
                            ]
                        }
                    ],
                    "consensus_points": [
                        {
                            "point": "General agreement on factual baseline",
                            "source_indices": list(range(min(len(articles), 3)))
                        }
                    ],
                    "disputed_points": [
                        {
                            "point": "Interpretation of implications varies",
                            "perspectives_involved": ["Supporting Perspective", "Alternative Perspective"]
                        }
                    ]
                }
            else:
                # Original simple debate format for backward compatibility
                return {
                    "statement": f"Analysis based on {len(articles)} news sources",
                    "for": [
                        "Supporting argument based on retrieved articles",
                        "Additional evidence from news sources",
                        "Further supporting perspective"
                    ],
                    "against": [
                        "Alternative viewpoint from articles", 
                        "Counter-evidence from sources",
                        "Contrasting perspective presented"
                    ]
                }
    
    def _empty_content(self, format_type: str) -> Dict[str, Any]:
        """Generate content structure for empty articles"""
        if format_type == "venn_diagram":
            return {
                "topic_a": "No data",
                "topic_b": "No data",
                "unique_a": ["No articles available"],
                "unique_b": ["No articles available"],
                "common": ["No common information available"]
            }
        else:
            # Debate format - handle both simple and enhanced
            if self._debate_format_enabled:
                # Enhanced multi-perspective format for empty articles
                return {
                    "topic": "No articles found for analysis",
                    "perspectives": [
                        {
                            "viewpoint": "No Data Available",
                            "position": "Cannot analyze without articles",
                            "support_level": 0.0,
                            "arguments": [
                                {
                                    "point": "No supporting information available",
                                    "source_indices": [],
                                    "strength": "weak"
                                }
                            ]
                        }
                    ],
                    "consensus_points": [
                        {
                            "point": "No consensus can be determined without sources",
                            "source_indices": []
                        }
                    ],
                    "disputed_points": [
                        {
                            "point": "No disputes identified without data",
                            "perspectives_involved": []
                        }
                    ]
                }
            else:
                # Original simple format
                return {
                    "statement": "No articles found for analysis",
                    "for": ["No supporting arguments available"],
                    "against": ["No opposing arguments available"]
                }
    
    def _articles_to_sources(self, articles: List[Dict]) -> List[Dict[str, Any]]:
        """Convert article format to Source data model format"""
        sources = []
        for article in articles:
            source = {
                "url": article.get("url", ""),
                "title": article.get("title", "No title"),
                "isVerified": False,  # Per story requirement - set to false for now
            }
            # Optional biasScore omitted as specified
            sources.append(source)
        return sources
    
    async def cleanup(self):
        """Clean up resources"""
        await self.client.close()


# Create singleton instance
summarization_agent = SummarizationAgent()


async def summarize_articles(articles: List[Dict[str, Any]], format_type: str = "debate") -> Dict[str, Any]:
    """
    FastAPI endpoint function for article summarization
    
    Args:
        articles: List of articles to summarize
        format_type: Summary format ('debate' or 'venn_diagram')
        
    Returns:
        Summary object with format, content, and sources
    """
    return await summarization_agent.summarize_articles(articles, format_type)