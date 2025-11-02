"""
Tests for content analyzer module
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.content_analyzer import ContentAnalyzer
from src.database import Database


@pytest.fixture
async def mock_db():
    """Create a mock database"""
    db = Mock(spec=Database)
    db.save_analysis = AsyncMock()
    db.log_warning = AsyncMock()
    return db


@pytest.fixture
def analyzer(mock_db):
    """Create content analyzer with mock database"""
    return ContentAnalyzer(mock_db)


def test_create_analysis_prompt(analyzer):
    """Test prompt creation"""
    prompt = analyzer._create_analysis_prompt("Test product text", "Test Store")
    
    assert "Test Store" in prompt
    assert "Test product text" in prompt
    assert "JSON" in prompt
    assert "product_name" in prompt
    assert "category" in prompt


@pytest.mark.asyncio
async def test_analyze_post_too_short(analyzer, mock_db):
    """Test that short posts are rejected"""
    result = await analyzer.analyze_post(
        post_id='short_123',
        text='Too short',
        source='Test'
    )
    
    assert result is None


@pytest.mark.asyncio
@patch('openai.ChatCompletion.create')
async def test_analyze_post_success(mock_openai, analyzer, mock_db):
    """Test successful post analysis"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = '''
    {
        "product_name": "Samsung Washer",
        "category": "Electronics",
        "keywords": ["washer", "samsung", "appliance"],
        "price": "2000 SAR",
        "discount": "20%",
        "is_suitable": true,
        "quality_score": 0.9,
        "reason": "Clear product description"
    }
    '''
    mock_openai.return_value = mock_response
    
    result = await analyzer.analyze_post(
        post_id='test_789',
        text='Samsung washer on sale for 2000 SAR with 20% discount!',
        source='Test Store'
    )
    
    assert result is not None
    assert result['product_name'] == 'Samsung Washer'
    assert result['category'] == 'Electronics'
    assert result['is_suitable'] is True
    assert result['quality_score'] == 0.9
    assert mock_db.save_analysis.called


@pytest.mark.asyncio
async def test_select_best_posts(analyzer):
    """Test selecting best posts by quality score"""
    analyzed_posts = [
        {'post_id': '1', 'analysis': {'is_suitable': True, 'quality_score': 0.7}},
        {'post_id': '2', 'analysis': {'is_suitable': True, 'quality_score': 0.9}},
        {'post_id': '3', 'analysis': {'is_suitable': False, 'quality_score': 0.8}},
        {'post_id': '4', 'analysis': {'is_suitable': True, 'quality_score': 0.6}},
        {'post_id': '5', 'analysis': {'is_suitable': True, 'quality_score': 0.85}},
    ]
    
    best = await analyzer.select_best_posts(analyzed_posts, max_count=3)
    
    assert len(best) == 3
    assert best[0]['analysis']['quality_score'] == 0.9  # Highest
    assert best[1]['analysis']['quality_score'] == 0.85
    assert best[2]['analysis']['quality_score'] == 0.7
    # Post 3 should be excluded (not suitable)
    assert '3' not in [p['post_id'] for p in best]
