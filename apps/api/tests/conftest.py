"""
Pytest configuration and fixtures
"""

import os
import sys

import pytest

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_api_key():
    """Mock API key for testing"""
    return "test_api_key_12345"


@pytest.fixture
def sample_query():
    """Sample query for testing"""
    return "artificial intelligence news"
