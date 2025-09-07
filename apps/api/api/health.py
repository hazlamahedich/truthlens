"""
Vercel serverless function for health checks
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "version": "1.7.0",
        "environment": os.getenv("NODE_ENV", "development")
    }

# Vercel handler
def handler(request):
    return app(request)