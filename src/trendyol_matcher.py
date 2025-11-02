"""
Trendyol Link MatcherMatches posts with appropriate Trendyol affiliate links
يطابق المنشورات مع روابط تريندول التابعة المناسبة
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Dict, Optional
from config import settings
from utils.logger import logger, log_operation
from src.database import Database


class TrendyolMatcher:
 """
 Matches products with Trendyol links using AI
 يطابق المنتجات مع روابط تريندول باستخدام الذكاء الاصطناعي
 """

 def __init__(self, database: Database):
 """
 Initialize Trendyol matcher
 تهيئة مطابق تريندول

 Args:
 database: Database instance"""
 self.database = database
 self.links_cache: List[Dict] = []
 self.sheet_client = None

 def _connect_to_sheets(self):
 """
 Connect to Google Sheets
 الاتصال بـ Google Sheets
 """
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
 log_operation("Google Sheets ConnectionGoogle Sheets", True)

 except Exception as e:
 log_operation("Google Sheets ConnectionGoogle Sheets", False, str(e))
 raise

 async def load_trendyol_links(self) -> bool:
 """
 Load Trendyol links from Google Sheets
 تحميل روابط تريندول من Google Sheets

 Returns:
 Success status"""
 try:
 if not self.sheet_client:
 self._connect_to_sheets()

 # Open the sheetsheet = self.sheet_client.open_by_key(settings.TRENDYOL_LINKS_SHEET_ID)
 worksheet = sheet.get_worksheet(0) # First sheet# Get all recordsrecords = worksheet.get_all_records()

 self.links_cache = []

 for record in records:
 link_data = {
 'category': record.get('Category', record.get('الفئة', '')).strip(),
 'keywords': record.get('Keywords', record.get('الكلمات_المفتاحية', '')).strip(),
 'link': record.get('Link', record.get('الرابط', '')).strip(),
 'product_name': record.get('Product', record.get('المنتج', '')).strip(),
 }

 # Split keywordsif link_data['keywords']:
 link_data['keywords_list'] = [
 kw.strip() for kw in link_data['keywords'].split(',')
 ]
 else:
 link_data['keywords_list'] = []

 if link_data['link']: # Only add if link existsself.links_cache.append(link_data)

 logger.info(f"✅ Loaded {len(self.links_cache)} Trendyol links{len(self.links_cache)} رابط")
 return True

 except Exception as e:
 logger.error(f"❌ Failed to load Trendyol links: {e}")
 await self.database.log_warning(
 "trendyol_links_error",
 f"Failed to load links: {str(e)}",
 "TrendyolMatcher"
 )
 return False

 def _calculate_match_score(self, post_analysis: Dict, link_data: Dict) -> float:
 """
 Calculate matching score between post and link
 حساب درجة المطابقة بين المنشور والرابط

 Args:
 post_analysis: Post analysis resultslink_data: Trendyol link dataReturns:
 Match score (0.0 to 1.0)"""
 score = 0.0

 post_category = post_analysis.get('category', '').lower()
 post_keywords = [kw.lower() for kw in post_analysis.get('keywords', [])]
 post_product = post_analysis.get('product_name', '').lower()

 link_category = link_data['category'].lower()
 link_keywords = [kw.lower() for kw in link_data.get('keywords_list', [])]
 link_product = link_data.get('product_name', '').lower()

 # Category match (40% weight)if post_category and link_category:
 if post_category == link_category:
 score += 0.4
 elif post_category in link_category or link_category in post_category:
 score += 0.2

 # Keywords match (40% weight)if post_keywords and link_keywords:
 matches = sum(1 for pk in post_keywords if any(pk in lk or lk in pk for lk in link_keywords))
 keyword_score = min(matches / len(post_keywords), 1.0) * 0.4
 score += keyword_score

 # Product name match (20% weight)if post_product and link_product:
 if post_product in link_product or link_product in post_product:
 score += 0.2
 else:
 # Check for word overlappost_words = set(post_product.split())
 link_words = set(link_product.split())
 overlap = len(post_words & link_words)
 if overlap > 0:
 score += 0.1

 return min(score, 1.0)

 async def match_post(self, post_id: str, analysis: Dict) -> Optional[Dict]:
 """
 Match a post with the best Trendyol link
 مطابقة منشور مع أفضل رابط تريندول

 Args:
 post_id: Post IDanalysis: Post analysis resultsReturns:
 Match result with link and confidence"""
 if not self.links_cache:
 await self.load_trendyol_links()

 if not self.links_cache:
 logger.warning("⚠️ No Trendyol links available")
 return None

 best_match = None
 best_score = 0.0

 for link_data in self.links_cache:
 score = self._calculate_match_score(analysis, link_data)

 if score > best_score:
 best_score = score
 best_match = link_data

 # Only accept matches with score > 0.3> 0.3
 if best_score < 0.3:
 logger.warning(f"⚠️ No good match found for post {post_id}- Score: {best_score:.2f}")
 return None

 match_result = {
 'post_id': post_id,
 'trendyol_link': best_match['link'],
 'confidence_score': best_score,
 'matched_keywords': ', '.join(best_match.get('keywords_list', [])),
 'matched_category': best_match['category']
 }

 # Save match to databaseawait self.database.connection.execute("""
 INSERT OR REPLACE INTO trendyol_matches
 (post_id, trendyol_link, confidence_score, matched_keywords)
 VALUES (?, ?, ?, ?)
 """, (
 match_result['post_id'],
 match_result['trendyol_link'],
 match_result['confidence_score'],
 match_result['matched_keywords']
 ))
 await self.database.connection.commit()

 logger.info(f"✅ Matched {post_id}- Score: {best_score:.2f} - {best_match['category']}")

 return match_result

 async def match_batch(self, analyzed_posts: List[Dict]) -> List[Dict]:
 """
 Match multiple posts with Trendyol links
 مطابقة عدة منشورات مع روابط تريندول

 Args:
 analyzed_posts: List of analyzed postsReturns:
 List of match results"""
 logger.info(f"🔗 Matching {len(analyzed_posts)} posts with Trendyol links{len(analyzed_posts)} منشور")

 # Ensure links are loadedif not self.links_cache:
 await self.load_trendyol_links()

 matches = []

 for item in analyzed_posts:
 match = await self.match_post(item['post_id'], item['analysis'])
 if match:
 matches.append(match)

 success_rate = len(matches) / len(analyzed_posts) * 100 if analyzed_posts else 0
 logger.info(f"✅ Matching complete: {len(matches)}/{len(analyzed_posts)} ({success_rate:.1f}%)")

 return matches


# ============================================================================
# STANDALONE MATCHING FUNCTION# ============================================================================

async def run_matching_cycle(database: Database) -> int:
 """
 Run matching cycle on analyzed posts
 تشغيل دورة المطابقة على المنشورات المحللة

 Args:
 database: Database instanceReturns:
 Number of successful matches"""
 matcher = TrendyolMatcher(database)

 # Get analyzed posts without matchesasync with database.connection.execute("""
 SELECT ap.post_id, ap.product_name, ap.category, ap.keywords
 FROM analyzed_posts ap
 LEFT JOIN trendyol_matches tm ON ap.post_id = tm.post_id
 WHERE tm.post_id IS NULL AND ap.is_suitable = 1
 LIMIT 50
 """) as cursor:
 rows = await cursor.fetchall()
 posts = [dict(row) for row in rows]

 if not posts:
 logger.info("ℹ️ No posts to match")
 return 0

 # Convert to expected formatanalyzed_posts = []
 for post in posts:
 analyzed_posts.append({
 'post_id': post['post_id'],
 'analysis': {
 'product_name': post['product_name'],
 'category': post['category'],
 'keywords': post['keywords'].split(',') if post['keywords'] else []
 }
 })

 matches = await matcher.match_batch(analyzed_posts)
 return len(matches)
