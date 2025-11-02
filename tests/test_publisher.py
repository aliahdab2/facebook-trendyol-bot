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


def test_check_post_rate_limit_within_limits(publisher):
    """Test posting limits when within allowed range"""
    publisher.posts_this_hour = 3
    
    result = publisher._check_post_rate_limit()
    
    assert result is True


def test_check_post_rate_limit_hourly_exceeded(publisher):
    """Test posting limits when hourly limit exceeded"""
    publisher.posts_this_hour = 5
    
    result = publisher._check_post_rate_limit()
    
    assert result is False


@pytest.mark.asyncio
async def test_wait_random_delay(publisher):
    """Test random delay calculation"""
    import time
    start = time.time()
    
    # Use minimal delay for testing
    with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        await publisher._wait_random_delay(min_minutes=1, max_minutes=2)
        
        # Verify sleep was called with time in seconds (60-120)
        mock_sleep.assert_called_once()
        delay_seconds = mock_sleep.call_args[0][0]
        assert 60 <= delay_seconds <= 120


@pytest.mark.asyncio
async def test_publish_to_page_success(publisher, mock_db):
    """Test successful publishing to page"""
    mock_response = Mock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={'id': 'page_post_123'})
    
    # Create proper async context manager
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_response
    mock_context.__aexit__.return_value = None
    
    mock_session = Mock()
    mock_session.post = Mock(return_value=mock_context)
    
    publisher.session = mock_session
    publisher.posts_this_hour = 0
    
    page_id = "test_page_123"
    message = "Test post content"
    images = ["https://test.com/image.jpg"]
    
    result = await publisher._publish_to_page(page_id, message, images)
    
    assert result == 'page_post_123'
    assert publisher.posts_this_hour == 1


@pytest.mark.asyncio
async def test_publish_post_structure(publisher):
    """Test publish_post method structure"""
    processed_data = {
        'post_id': 'test_123',
        'final_text': 'Test content',
        'images': ['https://test.com/img.jpg']
    }
    
    with patch.object(publisher, '_wait_random_delay', new_callable=AsyncMock):
        with patch.object(publisher, '_publish_to_page', new_callable=AsyncMock, return_value='page_123'):
            with patch.object(publisher, '_publish_to_group', new_callable=AsyncMock, return_value='group_123'):
                with patch('asyncio.sleep', new_callable=AsyncMock):
                    result = await publisher.publish_post(processed_data, wait_delay=False)
                    
                    assert result is not None
                    assert 'success' in result
                    assert result.get('page_post_id') or result.get('group_post_id')


@pytest.mark.asyncio
async def test_publish_to_group_success(publisher):
    """Test successful publishing to group"""
    mock_response = Mock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={'id': 'group_post_456'})
    
    # Create proper async context manager
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_response
    mock_context.__aexit__.return_value = None
    
    mock_session = Mock()
    mock_session.post = Mock(return_value=mock_context)
    
    publisher.session = mock_session
    publisher.posts_this_hour = 0
    
    group_id = "test_group_456"
    message = "Test group post"
    images = []
    
    result = await publisher._publish_to_group(group_id, message, images)
    
    assert result == 'group_post_456'
    assert publisher.posts_this_hour == 1
