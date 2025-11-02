"""
Integration tests for the complete bot workflow
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from src.database import Database
from src.scheduler import SmartScheduler


@pytest.fixture
async def integration_db():
    """Create integration test database"""
    db_path = "data/test_integration.db"
    db = Database(db_path)
    await db.connect()
    yield db
    await db.disconnect()
    Path(db_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_complete_post_workflow(integration_db):
    """Test complete workflow from collection to publishing"""
    
    # Step 1: Collect a post
    await integration_db.save_collected_post(
        post_id='workflow_123',
        source_page='Test Store',
        source_website='https://test.com',
        text='Amazing Samsung washer on sale!',
        images=['https://test.com/washer.jpg'],
        links=['https://test.com/product']
    )
    
    # Step 2: Save analysis
    analysis = {
        'product_name': 'Samsung Washer',
        'category': 'Electronics',
        'keywords': ['washer', 'samsung', 'sale'],
        'is_suitable': True,
        'quality_score': 0.9
    }
    await integration_db.save_analysis('workflow_123', analysis)
    
    # Step 3: Save Trendyol match
    await integration_db.save_trendyol_match(
        post_id='workflow_123',
        trendyol_link='https://trendyol.com/samsung-washer',
        confidence_score=0.85,
        matched_keywords='samsung, washer'
    )
    
    # Step 4: Save processed content
    await integration_db.save_processed_post(
        post_id='workflow_123',
        modified_text='Check out this Samsung washer!',
        promotional_text='Shop on Trendyol',
        hashtags='#samsung #washer #deals',
        source_attribution='Source: Test Store | https://test.com',
        final_content='Complete post content with all components'
    )
    
    # Step 5: Save published record
    await integration_db.save_published_post(
        post_id='workflow_123',
        published_to='page',
        facebook_post_id='fb_page_789',
        status='success'
    )
    
    # Verify complete workflow
    cursor = await integration_db.connection.execute(
        """
        SELECT 
            c.post_id,
            a.quality_score,
            t.confidence_score,
            pr.modified_text,
            pu.facebook_post_id
        FROM collected_posts c
        LEFT JOIN analyzed_posts a ON c.post_id = a.post_id
        LEFT JOIN trendyol_matches t ON c.post_id = t.post_id
        LEFT JOIN processed_posts pr ON c.post_id = pr.post_id
        LEFT JOIN published_posts pu ON c.post_id = pu.post_id
        WHERE c.post_id = ?
        """,
        ('workflow_123',)
    )
    
    row = await cursor.fetchone()
    assert row is not None
    assert row['post_id'] == 'workflow_123'
    assert row['quality_score'] == 0.9
    assert row['confidence_score'] == 0.85
    assert row['facebook_post_id'] is not None


@pytest.mark.asyncio
async def test_scheduler_operating_hours():
    """Test scheduler operating hours logic"""
    from datetime import time
    
    scheduler = SmartScheduler()
    
    # Test scheduler has correct operating hours
    assert scheduler.operating_start == time(8, 0)
    assert scheduler.operating_end == time(22, 0)
    
    # Test time checking works
    result = scheduler.is_operating_hours()
    assert isinstance(result, bool)
    
    # Test weekend checking
    is_weekend = scheduler.is_weekend()
    assert isinstance(is_weekend, bool)


@pytest.mark.asyncio
async def test_error_recovery(integration_db):
    """Test that system can recover from errors"""
    
    # Save a post
    await integration_db.save_collected_post(
        post_id='error_123',
        source_page='Test',
        text='Test'
    )
    
    # Log an error
    await integration_db.log_warning(
        warning_type='test_error',
        message='Test error occurred',
        source='test'
    )
    
    # Verify error was logged
    cursor = await integration_db.connection.execute(
        "SELECT COUNT(*) as count FROM warnings WHERE warning_type = ?",
        ('test_error',)
    )
    row = await cursor.fetchone()
    assert row['count'] == 1
    
    # System should continue operating after error logging
    posts = await integration_db.get_unprocessed_posts()
    assert len(posts) > 0
