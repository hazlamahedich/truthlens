"""
Verification Agent for TruthLens
Handles authenticity verification of news sources with feature flag support
"""

import logging
import os
from typing import Any, Dict, List
from datetime import datetime

from fastapi import HTTPException
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Source(BaseModel):
    """Source model matching TypeScript interface"""
    
    url: str
    title: str
    isVerified: bool = False  # Default to False per NFR7
    biasScore: float = None  # Optional for future use


class VerificationAgent:
    """Agent for verifying authenticity of news sources"""
    
    def __init__(self):
        """Initialize the verification agent with feature flag configuration"""
        self._is_enabled = self._check_feature_flag()
        logger.info(f"Verification agent initialized - Real verification: {'enabled' if self._is_enabled else 'disabled'}")
    
    def _check_feature_flag(self) -> bool:
        """Check if real verification is enabled via environment variable"""
        flag_value = os.getenv("ENABLE_REAL_VERIFICATION", "false").lower()
        enabled = flag_value in ("true", "1", "yes", "on")
        logger.info(f"Real verification feature flag: {'enabled' if enabled else 'disabled'}")
        return enabled
    
    async def verify_articles(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Verify authenticity of news sources
        
        Args:
            sources: List of Source dictionaries from Retrieval agent
            
        Returns:
            List of Source dictionaries with isVerified field populated
            
        Raises:
            HTTPException: For various error conditions
        """
        logger.info(f"Starting verification for {len(sources)} sources")
        
        # Handle empty source list
        if not sources:
            logger.info("Empty source list provided - returning empty list")
            return []
        
        try:
            # Validate input format
            validated_sources = self._validate_sources(sources)
            
            if self._is_enabled:
                # Use real verification logic (future implementation)
                verified_sources = await self._perform_real_verification(validated_sources)
            else:
                # Use mock verification per NFR7
                verified_sources = self._perform_mock_verification(validated_sources)
            
            logger.info(f"Verification completed for {len(verified_sources)} sources")
            return verified_sources
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Verification agent error: {str(e)}")
            # Graceful fallback - return sources with isVerified=False
            return self._fallback_verification(sources)
    
    def _validate_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate Source objects structure
        
        Args:
            sources: Raw source list from orchestrator
            
        Returns:
            Validated source list
            
        Raises:
            HTTPException: For invalid source structures
        """
        validated_sources = []
        
        for i, source in enumerate(sources):
            # Check required fields
            if not isinstance(source, dict):
                logger.warning(f"Source {i} is not a dictionary - skipping")
                continue
                
            url = source.get("url")
            title = source.get("title")
            
            if not url or not isinstance(url, str):
                logger.warning(f"Source {i} missing or invalid URL - skipping")
                continue
                
            if not title or not isinstance(title, str):
                logger.warning(f"Source {i} missing or invalid title - skipping")
                continue
            
            # Create validated source
            validated_source = {
                "url": url,
                "title": title,
                "isVerified": source.get("isVerified", False),  # Preserve existing value if present
                "biasScore": source.get("biasScore")  # Optional field
            }
            
            validated_sources.append(validated_source)
        
        logger.info(f"Validated {len(validated_sources)} out of {len(sources)} sources")
        return validated_sources
    
    async def _perform_real_verification(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Perform real blockchain/external verification (future implementation)
        
        Args:
            sources: List of validated sources
            
        Returns:
            Sources with real verification status
        """
        # TODO: Implement real verification logic in future stories
        # This would connect to blockchain or external verification services
        
        logger.info("Real verification not yet implemented - using mock behavior")
        
        # For now, use mock verification even when enabled
        # Real implementation will be added in future stories
        return self._perform_mock_verification(sources)
    
    def _perform_mock_verification(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Perform mock verification per NFR7 requirement
        
        Args:
            sources: List of validated sources
            
        Returns:
            Sources with isVerified set to False per NFR7
        """
        logger.info("Performing mock verification - setting all sources to unverified per NFR7")
        
        verified_sources = []
        for source in sources:
            # Create verified source with isVerified=False per NFR7
            verified_source = {
                "url": source["url"],
                "title": source["title"], 
                "isVerified": False,  # Always False per NFR7 requirement
                "biasScore": source.get("biasScore")  # Preserve if present
            }
            verified_sources.append(verified_source)
        
        return verified_sources
    
    def _fallback_verification(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fallback verification on error - ensures isVerified=False for safety
        
        Args:
            sources: Original source list
            
        Returns:
            Sources with isVerified=False for safety
        """
        logger.warning("Using fallback verification due to error")
        
        fallback_sources = []
        for source in sources:
            # Ensure basic structure with isVerified=False
            fallback_source = {
                "url": source.get("url", ""),
                "title": source.get("title", "Unknown"),
                "isVerified": False,  # Safe fallback
                "biasScore": source.get("biasScore")
            }
            fallback_sources.append(fallback_source)
        
        return fallback_sources


# Create singleton instance
verification_agent = VerificationAgent()


async def verify_articles(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    FastAPI endpoint function for article verification
    
    Args:
        sources: List of Source dictionaries from Retrieval agent
        
    Returns:
        List of Source dictionaries with isVerified field populated
    """
    return await verification_agent.verify_articles(sources)