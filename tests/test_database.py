"""
Tests for database module
"""

import pytest
import asyncio
from pathlib import Path
from src.database import Database


@pytest.fixture
async def test_db():
    """Create a test database"""
    db_path = "data/test_bot.db"
    db = Database(db_path)
    await db.connect()
    yield db
    await db.disconnect()
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_database_connection():
    """Test database connection"""
    db = Database("data/test_connection.db")
    await db.connect()
    assert db.connection is not None
    await db.disconnect()
    Path("data/test_connection.db").unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_save_collected_post(test_db):
    """Test saving a collected post"""
    post_data = {
        'post_id': 'test_123',
        'source_page': 'Test Store',
        'source_website': 'https://test.com',
        'text': 'Test product post',
        'images': '["https://test.com/img.jpg"]',
        'links': '["https://test.com"]'
    }
    
    await test_db.save_collected_post(**post_data)
    
    # Verify post was saved
    posts = await test_db.get_unprocessed_posts(limit=10)
    assert len(posts) > 0
    assert posts[0]['post_id'] == 'test_123'


@pytest.mark.asyncio
async def test_save_analysis(test_db):
    """Test saving analysis results"""
    # First save a post
    await test_db.save_collected_post(
        post_id='test_456',
        source_page='Test',
        text='Test'
    )
    
    analysis = {
        'product_name': 'Test Product',
        'category': 'Electronics',
        'keywords': ['test', 'product'],
        'is_suitable': True,
        'quality_score': 0.85
    }
    
    await test_db.save_analysis('test_456', analysis)
    
    # Verify analysis was saved
    cursor = await test_db.connection.execute(
        "SELECT * FROM analyzed_posts WHERE post_id = ?",
        ('test_456',)
    )
    row = await cursor.fetchone()
    assert row is not None
    assert row['product_name'] == 'Test Product'
    assert row['quality_score'] == 0.85


@pytest.mark.asyncio
async def test_duplicate_post_prevention(test_db):
    """Test that duplicate posts are prevented"""
    post_data = {
        'post_id': 'duplicate_123',
        'source_page': 'Test',
        'text': 'Duplicate test'
    }
    
    # Save once
    await test_db.save_collected_post(**post_data)
    
    # Try to save again - should not raise error
    await test_db.save_collected_post(**post_data)
    
    # Verify only one post exists
    cursor = await test_db.connection.execute(
        "SELECT COUNT(*) as count FROM collected_posts WHERE post_id = ?",
        ('duplicate_123',)
    )
    row = await cursor.fetchone()
    assert row['count'] == 1


@pytest.mark.asyncio
async def test_log_warning(test_db):
    """Test logging warnings"""
    await test_db.log_warning(
        warning_type='test_warning',
        message='This is a test warning',
        source='test_module'
    )
    
    cursor = await test_db.connection.execute(
        "SELECT * FROM warnings WHERE warning_type = ?",
        ('test_warning',)
    )
    row = await cursor.fetchone()
    assert row is not None
    assert row['message'] == 'This is a test warning'
