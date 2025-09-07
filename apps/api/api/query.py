"""
Vercel serverless function for query processing
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from query import QueryRequest
from orchestrator import orchestrate_query

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/")
async def process_query(request: QueryRequest):
    """Process user query through agent pipeline"""
    try:
        result = await orchestrate_query(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Vercel handler
def handler(request):
    return app(request)