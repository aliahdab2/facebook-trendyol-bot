"""
Pytest configuration and shared fixtures
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Setup test environment variables"""
    monkeypatch.setenv("FACEBOOK_PAGE_ACCESS_TOKEN", "test_token")
    monkeypatch.setenv("FACEBOOK_PAGE_ID", "test_page_id")
    monkeypatch.setenv("FACEBOOK_GROUP_ID", "test_group_id")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
    monkeypatch.setenv("TRENDYOL_LINKS_SHEET_ID", "test_sheet_id")
