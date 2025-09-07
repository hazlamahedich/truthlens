"""
Main FastAPI application for TruthLens API
Vercel-compatible serverless deployment
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import os

# Import our agents
from query import QueryRequest
from orchestrator import orchestrate_query

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TruthLens API",
    description="AI-powered news analysis and fact verification system",
    version="1.7.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str

@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {"message": "TruthLens API is running", "version": "1.7.0"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    return HealthResponse(
        status="healthy",
        version="1.7.0",
        environment=os.getenv("NODE_ENV", "development")
    )

@app.post("/query")
async def query_endpoint(request: QueryRequest):
    """
    Main query endpoint - processes user queries through the agent pipeline
    
    Args:
        request: QueryRequest with user's search query
        
    Returns:
        Summary response with sources and verification status
    """
    try:
        logger.info(f"Processing query: {request.query}")
        
        # Process through orchestrator
        result = await orchestrate_query(request.query)
        
        logger.info(f"Query processed successfully, returning {len(result.get('sources', []))} sources")
        return result
        
    except Exception as e:
        logger.error(f"Query processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)