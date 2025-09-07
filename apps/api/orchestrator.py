"""
Orchestrator Agent for TruthLens
Coordinates between Retrieval, Verification, and Summarization agents
"""

import logging
from typing import Any, Dict, List

from fastapi import HTTPException
# BaseModel not used directly in this module

# Import the retrieval agent
from retrieval import fetch_articles

# Import the verification agent
from verification import verify_articles

# Import the summarization agent
from summarization import summarize_articles

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """Main orchestrator that coordinates all agents"""

    async def process_query(self, query_text: str) -> Dict[str, Any]:
        """
        Process a user query through the agent pipeline

        Args:
            query_text: The user's search query

        Returns:
            Summary object with sources and content
        """
        logger.info(f"Processing query: {query_text}")

        try:
            # Step 1: Call Retrieval Agent
            logger.info("Fetching articles from Retrieval agent")
            sources = await fetch_articles(query_text)

            # Step 2: Call Verification Agent
            logger.info("Calling Verification agent for source authenticity verification")
            verified_sources = await verify_articles(sources)

            # Step 3: Call Summarization Agent (Real LLM with feature flag support)
            logger.info("Calling Summarization agent for real LLM summary generation")
            
            # Convert verified sources back to articles format for summarization
            articles = self._sources_to_articles(verified_sources)
            summary_response = await summarize_articles(articles, format_type="debate")
            
            # Use the complete summary response
            response = summary_response

            logger.info(f"Query processed successfully with {len(verified_sources)} verified sources")
            return response

        except HTTPException:
            # Re-raise HTTP exceptions from agents
            raise
        except Exception as e:
            logger.error(f"Orchestrator error: {str(e)}")
            # Fallback to mock summarization on any orchestrator error
            return {
                "format": "debate",
                "content": {
                    "statement": f"Error processing query: {query_text}",
                    "for": ["Unable to retrieve articles at this time"],
                    "against": ["Please try again later"],
                },
                "sources": [],
            }
    
    def _sources_to_articles(self, sources: List[Dict]) -> List[Dict[str, Any]]:
        """
        Convert Source objects back to articles format for summarization
        
        Args:
            sources: List of Source dictionaries
            
        Returns:
            List of articles in expected format
        """
        articles = []
        for source in sources:
            article = {
                "title": source.get("title", "No title"),
                "url": source.get("url", ""),
                "description": source.get("description", "No description available"),
                # Add any other fields that might be available
            }
            articles.append(article)
        return articles

    def _generate_mock_summary(self, query: str, sources: List[Dict]) -> Dict[str, Any]:
        """
        Generate a mocked summary (Summarization agent is mocked per AC 3)

        Args:
            query: Original query text
            sources: List of retrieved sources

        Returns:
            Mock summary content in debate format
        """
        # Generate mock content based on actual retrieved sources
        source_count = len(sources)

        if source_count == 0:
            return {
                "statement": f"No articles found for: {query}",
                "for": ["No supporting arguments available"],
                "against": ["No opposing arguments available"],
            }

        # Create mock arguments referencing actual sources
        for_arguments = []
        against_arguments = []

        for i, source in enumerate(sources[:3]):  # Use first 3 sources for 'for'
            for_arguments.append(
                f"According to '{source.get('title', 'Source')}': Supporting perspective on {query}"
            )

        if source_count > 3:
            for source in sources[3:5]:  # Use next 2 sources for 'against'
                against_arguments.append(
                    f"Per '{source.get('title', 'Source')}': Alternative view on {query}"
                )

        # Ensure at least one argument each
        if not for_arguments:
            for_arguments = [f"General support for query: {query}"]
        if not against_arguments:
            against_arguments = [f"Potential concerns about: {query}"]

        return {
            "statement": f"Analysis of '{query}' based on {source_count} sources",
            "for": for_arguments,
            "against": against_arguments,
        }


# Create singleton instance
orchestrator = OrchestratorAgent()


async def orchestrate_query(query_text: str) -> Dict[str, Any]:
    """
    FastAPI endpoint function for orchestrating query processing

    Args:
        query_text: User's search query

    Returns:
        Complete summary with sources
    """
    return await orchestrator.process_query(query_text)
