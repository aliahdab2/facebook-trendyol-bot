"""
Tests for Facebook publisher module
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from src.publisher import FacebookPublisher
from src.database import Database


@pytest.fixture
async def mock_db():
    """Create mock database"""
    db = Mock(spec=Database)
    db.save_published_post = AsyncMock()
    db.log_warning = AsyncMock()
    db.get_recent_published_posts = AsyncMock(return_value=[])
    return db


@pytest.fixture
def publisher(mock_db):
    """Create publisher with mock database"""
    return FacebookPublisher(mock_db)


@pytest.mark.asyncio
async def test_check_posting_limits_within_limits(publisher):
    """Test posting limits when within allowed range"""
    publisher.posts_this_hour = 3
    publisher.posts_today = 4
    
    result = await publisher._check_posting_limits()
    
    assert result is True


@pytest.mark.asyncio
async def test_check_posting_limits_hourly_exceeded(publisher):
    """Test posting limits when hourly limit exceeded"""
    publisher.posts_this_hour = 5
    publisher.posts_today = 4
    
    result = await publisher._check_posting_limits()
    
    assert result is False


@pytest.mark.asyncio
async def test_check_posting_limits_daily_exceeded(publisher):
    """Test posting limits when daily limit exceeded"""
    publisher.posts_this_hour = 3
    publisher.posts_today = 6
    
    result = await publisher._check_posting_limits()
    
    assert result is False


@pytest.mark.asyncio
@patch('aiohttp.ClientSession.post')
async def test_publish_to_page_success(mock_post, publisher, mock_db):
    """Test successful publishing to page"""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={'id': 'page_post_123'})
    mock_post.return_value.__aenter__.return_value = mock_response
    
    publisher.session = Mock()
    publisher.session.post = mock_post
    
    content = "Test post content"
    images = ["https://test.com/image.jpg"]
    
    result = await publisher._publish_to_page('test_post_123', content, images)
    
    assert result is True
    assert mock_db.save_published_post.called


@pytest.mark.asyncio
async def test_calculate_delay_after_original(publisher):
    """Test delay calculation after original post"""
    original_time = datetime.now() - timedelta(minutes=10)
    
    delay = await publisher._calculate_delay_after_original(original_time)
    
    # Should wait at least 30 minutes total, so 20 more minutes
    assert delay >= 20 * 60
    assert delay <= 120 * 60


@pytest.mark.asyncio
async def test_calculate_next_post_interval(publisher):
    """Test interval calculation between posts"""
    interval = await publisher._calculate_next_post_interval()
    
    # Should be between 2-5 hours in seconds
    assert interval >= 2 * 3600
    assert interval <= 5 * 3600


def test_create_post_content(publisher):
    """Test post content creation"""
    processed_data = {
        'modified_text': 'Check out this amazing product!',
        'promotional_text': 'Shop on Trendyol for best prices',
        'hashtags': '#deals #shopping #trendyol',
        'source_attribution': 'Source: Test Store | https://test.com',
        'images': '["https://test.com/img.jpg"]'
    }
    
    content = publisher._create_post_content(processed_data)
    
    assert 'amazing product' in content
    assert 'Trendyol' in content
    assert '#deals' in content
    assert 'Source: Test Store' in content
