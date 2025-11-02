"""
Trendyol Link Matcher - Matches products with affiliate links from Google Sheets
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import Dict, List, Optional
from config import settings
from utils.logger import logger


class TrendyolMatcher:
    """Matches analyzed posts with Trendyol affiliate links"""

    def __init__(self):
        """Initialize matcher"""
        self.sheet_client = None
        self.links_cache: List[Dict] = []
        self.cache_timestamp = None

    def _connect_to_sheets(self):
        """Connect to Google Sheets"""
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]

            creds = ServiceAccountCredentials.from_json_keyfile_name(
                settings.GOOGLE_SHEETS_CREDENTIALS_FILE,
                scope
            )

            self.sheet_client = gspread.authorize(creds)
            logger.info("✅ Connected to Google Sheets")

        except Exception as e:
            logger.error(f"❌ Google Sheets connection failed: {e}")
            raise

    async def load_trendyol_links(self) -> List[Dict]:
        """Load Trendyol links from Google Sheets"""
        try:
            if not self.sheet_client:
                self._connect_to_sheets()

            # Open the sheet
            sheet = self.sheet_client.open(settings.GOOGLE_SHEETS_NAME)
            worksheet = sheet.worksheet(settings.GOOGLE_SHEETS_TAB_NAME)

            # Get all records
            records = worksheet.get_all_records()

            # Parse into structured format
            links = []
            for record in records:
                link_data = {
                    'category': record.get('Category', '').strip(),
                    'keywords': [k.strip() for k in record.get('Keywords', '').split(',')],
                    'link': record.get('Link', '').strip(),
                    'product_name': record.get('Product Name', '').strip()
                }

                if link_data['link'] and link_data['category']:
                    links.append(link_data)

            self.links_cache = links
            logger.info(f"✅ Loaded {len(links)} Trendyol links")
            return links

        except Exception as e:
            logger.error(f"❌ Failed to load Trendyol links: {e}")
            return []

    def _calculate_match_score(
        self,
        analysis: Dict,
        link_data: Dict
    ) -> float:
        """Calculate match score between post and link"""
        score = 0.0

        # Category match (40 points)
        if analysis.get('category', '').lower() == link_data['category'].lower():
            score += 40.0

        # Keywords match (40 points)
        analysis_keywords = set(k.lower() for k in analysis.get('keywords', []))
        link_keywords = set(k.lower() for k in link_data['keywords'])

        if analysis_keywords and link_keywords:
            common_keywords = analysis_keywords.intersection(link_keywords)
            keyword_score = (len(common_keywords) / len(link_keywords)) * 40.0
            score += keyword_score

        # Product name similarity (20 points)
        product_name = analysis.get('product_name', '').lower()
        link_product = link_data.get('product_name', '').lower()

        if product_name and link_product:
            if product_name in link_product or link_product in product_name:
                score += 20.0
            else:
                common_words = set(product_name.split()).intersection(set(link_product.split()))
                if common_words:
                    score += len(common_words) * 5.0

        return min(score, 100.0)

    async def find_best_match(self, analysis: Dict) -> Optional[Dict]:
        """Find best matching Trendyol link"""
        try:
            # Load links if cache is empty
            if not self.links_cache:
                await self.load_trendyol_links()

            if not self.links_cache:
                logger.warning("⚠️ No Trendyol links available")
                return None

            # Calculate scores for all links
            matches = []
            for link_data in self.links_cache:
                score = self._calculate_match_score(analysis, link_data)
                if score > 0:
                    matches.append({
                        'link': link_data['link'],
                        'score': score,
                        'category': link_data['category'],
                        'product_name': link_data.get('product_name', '')
                    })

            if not matches:
                logger.warning(f"⚠️ No match found for: {analysis.get('product_name')}")
                return None

            # Sort by score and return best match
            matches.sort(key=lambda x: x['score'], reverse=True)
            best_match = matches[0]

            # Only accept matches with score >= 30
            if best_match['score'] < 30:
                logger.warning(f"⚠️ Low match score ({best_match['score']}) for: {analysis.get('product_name')}")
                return None

            logger.info(f"✅ Match found (score: {best_match['score']:.1f}): {best_match['product_name']}")
            return best_match

        except Exception as e:
            logger.error(f"❌ Matching failed: {e}")
            return None


async def match_single_post(analysis: Dict) -> Optional[Dict]:
    """Match a single analyzed post"""
    matcher = TrendyolMatcher()
    return await matcher.find_best_match(analysis)
