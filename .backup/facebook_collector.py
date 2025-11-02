"""
Facebook Post CollectorFetches new posts from competitor pages using Graph API
جلب المنشورات الجديدة من صفحات المنافسين عبر Graph API
"""

import aiohttp
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from config import settings
from utils.logger import logger, log_api_call, log_post_activity
from src.database import Database


class FacebookCollector:
 """
 Collects posts from monitored Facebook pages
 يجمع المنشورات من صفحات فيسبوك المراقبة
 """

 def __init__(self, database: Database):
 """
 Initialize Facebook collector
 تهيئة جامع فيسبوك

 Args:
 database: Database instance"""
 self.database = database
 self.access_token = settings.FACEBOOK_PAGE_ACCESS_TOKEN
 self.base_url = "https://graph.facebook.com/v18.0"
 self.session: Optional[aiohttp.ClientSession] = None
 self.api_calls_this_hour = 0
 self.last_reset = datetime.now()

 async def __aenter__(self):
 """Context manager entry"""
 self.session = aiohttp.ClientSession()
 return self

 async def __aexit__(self, exc_type, exc_val, exc_tb):
 """Context manager exit"""
 if self.session:
 await self.session.close()

 def _check_rate_limit(self) -> bool:
 """
 Check if we're within rate limits
 التحقق من حدود المعدل

 Returns:
 True if within limits"""
 # Reset counter every hourif datetime.now() - self.last_reset > timedelta(hours=1):
 self.api_calls_this_hour = 0
 self.last_reset = datetime.now()

 if self.api_calls_this_hour >= settings.MAX_API_CALLS_PER_HOUR:
 logger.warning(f"⚠️ Rate limit reached: {self.api_calls_this_hour} calls/hour")
 return False

 return True

 async def _make_api_call(self, url: str, params: Dict) -> Optional[Dict]:
 """
 Make Facebook Graph API call with rate limiting
 طلب API مع احترام حدود المعدل

 Args:
 url: API endpointparams: Query parametersReturns:
 API responseAPI
 """
 if not self._check_rate_limit():
 await asyncio.sleep(3600) # Wait 1 hourreturn None

 start_time = datetime.now()

 try:
 async with self.session.get(url, params=params) as response:
 self.api_calls_this_hour += 1
 duration = (datetime.now() - start_time).total_seconds()

 log_api_call("Facebook", url, response.status, duration)

 if response.status == 200:
 return await response.json()
 elif response.status == 429: # Too Many Requests
 logger.warning("⚠️ Rate limited by Facebook")
 await self.database.log_warning(
 "rate_limit",
 "Facebook API rate limit hit",
 "FacebookCollector"
 )
 return None
 else:
 error_data = await response.text()
 logger.error(f"❌ API Error {response.status}API: {error_data}")
 return None

 except Exception as e:
 logger.error(f"❌ API call failedAPI: {e}")
 return None

 async def collect_from_page(self, page_info: Dict) -> List[Dict]:
 """
 Collect posts from a specific Facebook page
 جمع المنشورات من صفحة فيسبوك محددة

 Args:
 page_info: Page information from settingsReturns:
 List of collected posts"""
 page_id = page_info['id']
 page_name = page_info['name']
 page_website = page_info['website']

 logger.info(f"📥 Collecting from: {page_name} ({page_id})")

 # Calculate time range (last 2 hours + buffer)since = int((datetime.now() - timedelta(hours=settings.COLLECTION_INTERVAL_HOURS + 1)).timestamp())

 url = f"{self.base_url}/{page_id}/posts"
 params = {
 'access_token': self.access_token,
 'fields': 'id,message,full_picture,attachments{media,url},created_time,permalink_url',
 'since': since,
 'limit': 25
 }

 data = await self._make_api_call(url, params)

 if not data or 'data' not in data:
 logger.warning(f"⚠️ No data from {page_name}{page_name}")
 return []

 posts = []
 new_count = 0

 for post in data['data']:
 post_id = post.get('id')

 # Skip if already collectedif await self.database.post_exists(post_id):
 continue

 # Extract post datapost_data = {
 'post_id': post_id,
 'source_page': page_name,
 'source_website': page_website,
 'text': post.get('message', ''),
 'created_time': post.get('created_time'),
 'permalink_url': post.get('permalink_url'),
 'images': [],
 'links': []
 }

 # Extract imagesif 'full_picture' in post:
 post_data['images'].append(post['full_picture'])

 # Extract attachmentsif 'attachments' in post and 'data' in post['attachments']:
 for attachment in post['attachments']['data']:
 if 'media' in attachment and 'image' in attachment['media']:
 post_data['images'].append(attachment['media']['image']['src'])
 if 'url' in attachment:
 post_data['links'].append(attachment['url'])

 # Save to databaseif await self.database.save_collected_post(post_data):
 posts.append(post_data)
 new_count += 1
 log_post_activity("Collected", post_id, page_name)

 logger.info(f"✅ Collected {new_count} new posts from {page_name}{new_count} منشور جديد من {page_name}")
 return posts

 async def collect_all(self) -> List[Dict]:
 """
 Collect posts from all monitored pages
 جمع المنشورات من جميع الصفحات المراقبة

 Returns:
 All collected posts"""
 logger.info("=" * 80)
 logger.info("🚀 Starting collection cycle")
 logger.info("=" * 80)

 all_posts = []

 for page_info in settings.SOURCE_PAGES:
 try:
 posts = await self.collect_from_page(page_info)
 all_posts.extend(posts)

 # Small delay between pagesawait asyncio.sleep(2)

 except Exception as e:
 logger.error(f"❌ Failed to collect from {page_info['name']}: {e}")
 await self.database.log_warning(
 "collection_error",
 f"Failed to collect from {page_info['name']}: {str(e)}",
 "FacebookCollector"
 )

 logger.info("=" * 80)
 logger.info(f"✅ Collection complete: {len(all_posts)} total posts")
 logger.info("=" * 80)

 return all_posts

 def should_collect_now(self) -> bool:
 """
 Check if we should collect posts now based on schedule
 التحقق من ضرورة الجمع الآن حسب الجدول

 Returns:
 True if within operating hours"""
 current_hour = datetime.now().hour

 if current_hour < settings.COLLECTION_START_HOUR or current_hour >= settings.COLLECTION_END_HOUR:
 logger.info(f"⏸️ Outside operating hours: {current_hour}:00")
 return False

 return True


# ============================================================================
# STANDALONE COLLECTION FUNCTION# ============================================================================

async def run_collection_cycle(database: Database) -> int:
 """
 Run a single collection cycle
 تشغيل دورة جمع واحدة

 Args:
 database: Database instanceReturns:
 Number of posts collected"""
 async with FacebookCollector(database) as collector:
 if not collector.should_collect_now():
 return 0

 posts = await collector.collect_all()
 return len(posts)
