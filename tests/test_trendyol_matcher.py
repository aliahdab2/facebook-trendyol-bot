"""
Tests for Trendyol link matcher
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.trendyol_matcher import TrendyolMatcher
from src.database import Database


@pytest.fixture
def matcher():
    """Create matcher instance"""
    return TrendyolMatcher()


@pytest.fixture
def sample_links():
    """Sample Trendyol links"""
    return [
        {
            'category': 'Electronics',
            'keywords': ['washer', 'samsung', 'washing machine'],
            'link': 'https://trendyol.com/samsung-washer',
            'product_name': 'Samsung Washer'
        },
        {
            'category': 'Clothing',
            'keywords': ['shirt', 'men', 'cotton'],
            'link': 'https://trendyol.com/cotton-shirt',
            'product_name': 'Cotton Shirt'
        },
        {
            'category': 'Home',
            'keywords': ['sofa', 'couch', 'living room'],
            'link': 'https://trendyol.com/grey-sofa',
            'product_name': 'Grey Sofa'
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
    
    assert score > 50.0  # High score for good match (out of 100)
    assert score <= 100.0


def test_calculate_match_score_category_only(matcher, sample_links):
    """Test matching with only category match"""
    analysis = {
        'category': 'Electronics',
        'keywords': ['phone', 'mobile'],
        'product_name': 'Mobile Phone'
    }
    
    score = matcher._calculate_match_score(analysis, sample_links[0])
    
    assert 30.0 <= score <= 50.0  # Moderate score for category-only match (out of 100)


def test_calculate_match_score_no_match(matcher, sample_links):
    """Test matching with no overlap"""
    analysis = {
        'category': 'Food',
        'keywords': ['chocolate', 'candy'],
        'product_name': 'Chocolate Bar'
    }
    
    score = matcher._calculate_match_score(analysis, sample_links[0])
    
    assert score == 0.0  # No score for no match


@pytest.mark.asyncio
async def test_load_trendyol_links(matcher):
    """Test loading links from Google Sheets"""
    # Mock settings attributes that don't exist yet
    with patch('src.trendyol_matcher.settings') as mock_settings:
        mock_settings.GOOGLE_SHEETS_NAME = 'Test Sheet'
        mock_settings.GOOGLE_SHEETS_TAB_NAME = 'Sheet1'
        
        with patch.object(matcher, '_connect_to_sheets'):
            mock_sheet = Mock()
            mock_worksheet = Mock()
            
            mock_worksheet.get_all_records.return_value = [
                {
                    'Category': 'Electronics',
                    'Keywords': 'washer, samsung',
                    'Link': 'https://trendyol.com/washer',
                    'Product Name': 'Samsung Washer'
                }
            ]
            
            mock_sheet.worksheet.return_value = mock_worksheet
            matcher.sheet_client = Mock()
            matcher.sheet_client.open.return_value = mock_sheet
            
            links = await matcher.load_trendyol_links()
            
            assert len(links) > 0
            assert links[0]['category'] == 'Electronics'
            assert links[0]['link'] == 'https://trendyol.com/washer'


@pytest.mark.asyncio
async def test_find_best_match(matcher, sample_links):
    """Test finding best matching link"""
    matcher.links_cache = sample_links
    
    analysis = {
        'category': 'Electronics',
        'keywords': ['samsung', 'washer'],
        'product_name': 'Samsung Washer 9KG'
    }
    
    match = await matcher.find_best_match(analysis)
    
    assert match is not None
    assert match['link'] == 'https://trendyol.com/samsung-washer'
    assert match['score'] > 50.0


@pytest.mark.asyncio
async def test_find_best_match_low_confidence(matcher, sample_links):
    """Test that low confidence matches are rejected"""
    matcher.links_cache = sample_links
    
    analysis = {
        'category': 'Food',  # No matching category
        'keywords': ['bread', 'bakery'],
        'product_name': 'Fresh Bread'
    }
    
    match = await matcher.find_best_match(analysis)
    
    # Should return None if score too low (< 30)
    assert match is None
