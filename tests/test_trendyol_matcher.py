"""
Tests for Trendyol link matcher
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.trendyol_matcher import TrendyolMatcher
from src.database import Database


@pytest.fixture
async def mock_db():
    """Create mock database"""
    db = Mock(spec=Database)
    db.save_trendyol_match = AsyncMock()
    return db


@pytest.fixture
def matcher(mock_db):
    """Create matcher with mock database"""
    return TrendyolMatcher(mock_db)


@pytest.fixture
def sample_links():
    """Sample Trendyol links"""
    return [
        {
            'category': 'Electronics',
            'keywords': 'washer, samsung, washing machine',
            'link': 'https://trendyol.com/samsung-washer',
            'product': 'Samsung Washer'
        },
        {
            'category': 'Clothing',
            'keywords': 'shirt, men, cotton',
            'link': 'https://trendyol.com/cotton-shirt',
            'product': 'Cotton Shirt'
        },
        {
            'category': 'Home',
            'keywords': 'sofa, couch, living room',
            'link': 'https://trendyol.com/grey-sofa',
            'product': 'Grey Sofa'
        }
    ]


def test_calculate_match_score_perfect_match(matcher, sample_links):
    """Test matching with perfect category and keyword match"""
    analysis = {
        'category': 'Electronics',
        'keywords': ['samsung', 'washer', 'washing'],
        'product_name': 'Samsung Washing Machine'
    }
    
    score = matcher._calculate_match_score(analysis, sample_links[0])
    
    assert score > 0.7  # High score for good match
    assert score <= 1.0


def test_calculate_match_score_category_only(matcher, sample_links):
    """Test matching with only category match"""
    analysis = {
        'category': 'Electronics',
        'keywords': ['phone', 'mobile'],
        'product_name': 'Mobile Phone'
    }
    
    score = matcher._calculate_match_score(analysis, sample_links[0])
    
    assert 0.3 < score < 0.6  # Moderate score for category-only match


def test_calculate_match_score_no_match(matcher, sample_links):
    """Test matching with no overlap"""
    analysis = {
        'category': 'Food',
        'keywords': ['chocolate', 'candy'],
        'product_name': 'Chocolate Bar'
    }
    
    score = matcher._calculate_match_score(analysis, sample_links[0])
    
    assert score < 0.3  # Low score for no match


@pytest.mark.asyncio
@patch('gspread.authorize')
async def test_fetch_trendyol_links(mock_gspread, matcher):
    """Test fetching links from Google Sheets"""
    mock_client = Mock()
    mock_sheet = Mock()
    mock_worksheet = Mock()
    
    mock_worksheet.get_all_records.return_value = [
        {
            'Category': 'Electronics',
            'Keywords': 'washer, samsung',
            'Link': 'https://trendyol.com/washer',
            'Product': 'Samsung Washer'
        }
    ]
    
    mock_sheet.sheet1 = mock_worksheet
    mock_client.open_by_key.return_value = mock_sheet
    mock_gspread.return_value = mock_client
    
    links = await matcher._fetch_trendyol_links()
    
    assert len(links) > 0
    assert links[0]['category'] == 'Electronics'


@pytest.mark.asyncio
async def test_find_best_match(matcher, sample_links):
    """Test finding best matching link"""
    matcher.trendyol_links = sample_links
    
    analysis = {
        'category': 'Electronics',
        'keywords': ['samsung', 'washer'],
        'product_name': 'Samsung Washer 9KG'
    }
    
    match = await matcher.find_best_match('test_123', analysis)
    
    assert match is not None
    assert match['link'] == 'https://trendyol.com/samsung-washer'
    assert match['confidence_score'] > 0.5


@pytest.mark.asyncio
async def test_find_best_match_low_confidence(matcher, sample_links):
    """Test that low confidence matches are rejected"""
    matcher.trendyol_links = sample_links
    
    analysis = {
        'category': 'Food',  # No matching category
        'keywords': ['bread', 'bakery'],
        'product_name': 'Fresh Bread'
    }
    
    match = await matcher.find_best_match('test_456', analysis)
    
    # Should return None if confidence too low
    assert match is None or match['confidence_score'] < 0.3
