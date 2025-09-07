import logging
from typing import Optional

from fastapi import FastAPI, HTTPException

# Import orchestrator
from orchestrator import orchestrate_query
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    queryText: str


class Source(BaseModel):
    url: str
    title: str
    isVerified: bool
    biasScore: Optional[int] = None


class Summary(BaseModel):
    format: str
    content: dict
    sources: list[Source]


app = FastAPI()


@app.post("/api/query")
async def handle_query(query: QueryRequest):
    """
    Main API endpoint that processes user queries
    Now integrated with real Retrieval agent via Orchestrator
    """
    try:
        logger.info(f"Received query: {query.queryText}")

        # Call orchestrator which coordinates all agents
        result = await orchestrate_query(query.queryText)

        return result

    except HTTPException as e:
        # Pass through HTTP exceptions
        raise e
    except Exception as e:
        logger.error(f"Query endpoint error: {str(e)}")
        # Fallback to mocked response on error
        return {
            "format": "debate",
            "content": {
                "statement": "Error processing query: " + query.queryText,
                "for": ["Service temporarily unavailable.", "Please try again later."],
                "against": ["Check your query and try again."],
            },
            "sources": [
                {
                    "url": "https://example.com/error",
                    "title": "Error retrieving sources",
                    "isVerified": False,
                }
            ],
        }
