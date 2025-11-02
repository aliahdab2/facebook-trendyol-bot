"""
PublisherPublishes processed posts to Facebook page and group
ينشر المنشورات المعالجة على صفحة ومجموعة فيسبوك
"""

import aiohttp
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random
from config import settings
from utils.logger import logger, log_api_call, log_post_activity
from src.database import Database


class FacebookPublisher:
 """
 Publishes posts to Facebook with smart scheduling
 ينشر المنشورات على فيسبوك بجدولة ذكية
 """

 def __init__(self, database: Database):
 """
 Initialize Facebook publisher
 تهيئة ناشر فيسبوك

 Args:
 database: Database instance"""
 self.database = database
 self.access_token = settings.FACEBOOK_PAGE_ACCESS_TOKEN
 self.page_id = settings.FACEBOOK_PAGE_ID
 self.group_id = settings.FACEBOOK_GROUP_ID
 self.base_url = "https://graph.facebook.com/v18.0"
 self.session: Optional[aiohttp.ClientSession] = None
 self.posts_this_hour = 0
 self.last_reset = datetime.now()

 async def __aenter__(self):
 """Context manager entry"""
 self.session = aiohttp.ClientSession()
 return self

 async def __aexit__(self, exc_type, exc_val, exc_tb):
 """Context manager exit"""
 if self.session:
 await self.session.close()

 def _check_post_rate_limit(self) -> bool:
 """
 Check posting rate limits
 التحقق من حدود معدل النشر

 Returns:
 True if can post"""
 # Reset counter every hourif datetime.now() - self.last_reset > timedelta(hours=1):
 self.posts_this_hour = 0
 self.last_reset = datetime.now()

 if self.posts_this_hour >= settings.MAX_POSTS_PER_HOUR:
 logger.warning(f"⚠️ Post rate limit reached: {self.posts_this_hour} posts/hour")
 return False

 return True

 async def _publish_to_page(self, content: str, image_urls: List[str] = None) -> Optional[str]:
 """
 Publish to Facebook page
 النشر على صفحة فيسبوك

 Args:
 content: Post contentimage_urls: List of image URLsReturns:
 Facebook post ID"""
 url = f"{self.base_url}/{self.page_id}/feed"

 data = {
 'access_token': self.access_token,
 'message': content
 }

 # Add first image if availableif image_urls and len(image_urls) > 0:
 data['link'] = image_urls[0]

 try:
 async with self.session.post(url, data=data) as response:
 log_api_call("Facebook", "page/feed", response.status)

 if response.status == 200:
 result = await response.json()
 return result.get('id')
 else:
 error_data = await response.text()
 logger.error(f"❌ Page publish failed: {error_data}")
 return None

 except Exception as e:
 logger.error(f"❌ Page publish error: {e}")
 return None

 async def _publish_to_group(self, content: str, image_urls: List[str] = None) -> Optional[str]:
 """
 Publish to Facebook group
 النشر على مجموعة فيسبوك

 Args:
 content: Post contentimage_urls: List of image URLsReturns:
 Facebook post ID"""
 if not self.group_id:
 logger.warning("⚠️ No group ID configured")
 return None

 url = f"{self.base_url}/{self.group_id}/feed"

 data = {
 'access_token': self.access_token,
 'message': content
 }

 # Add first image if availableif image_urls and len(image_urls) > 0:
 data['link'] = image_urls[0]

 try:
 async with self.session.post(url, data=data) as response:
 log_api_call("Facebook", "group/feed", response.status)

 if response.status == 200:
 result = await response.json()
 return result.get('id')
 else:
 error_data = await response.text()
 logger.error(f"❌ Group publish failed: {error_data}")
 return None

 except Exception as e:
 logger.error(f"❌ Group publish error: {e}")
 return None

 async def publish_post(
 self,
 post_id: str,
 final_content: str,
 image_urls: List[str] = None,
 wait_before_publish: bool = True
 ) -> Dict:
 """
 Publish a post to both page and group
 نشر منشور على الصفحة والمجموعة

 Args:
 post_id: Internal post IDfinal_content: Final processed contentimage_urls: Image URLswait_before_publish: Wait random delayReturns:
 Publishing results"""
 log_post_activity("Publishing", post_id)

 # Check rate limitsif not self._check_post_rate_limit():
 logger.warning(f"⚠️ Skipping post due to rate limit")
 return {'status': 'rate_limited', 'post_id': post_id}

 # Random delay before publishingif wait_before_publish:
 delay = random.randint(
 settings.MIN_DELAY_AFTER_ORIGINAL,
 settings.MAX_DELAY_AFTER_ORIGINAL
 )
 logger.info(f"⏳ Waiting {delay} minutes before publishing{delay} دقيقة")
 await asyncio.sleep(delay * 60)

 results = {'post_id': post_id, 'page': None, 'group': None, 'status': 'success'}

 # Publish to pagetry:
 page_post_id = await self._publish_to_page(final_content, image_urls)

 if page_post_id:
 results['page'] = page_post_id
 logger.info(f"✅ Published to page: {page_post_id}")

 # Save to databaseawait self.database.connection.execute("""
 INSERT INTO published_posts
 (post_id, published_to, facebook_post_id, status)
 VALUES (?, ?, ?, ?)
 """, (post_id, 'page', page_post_id, 'success'))

 self.posts_this_hour += 1
 else:
 results['status'] = 'partial_failure'
 await self.database.connection.execute("""
 INSERT INTO published_posts
 (post_id, published_to, status, error_message)
 VALUES (?, ?, ?, ?)
 """, (post_id, 'page', 'failed', 'Failed to publish to page'))

 except Exception as e:
 logger.error(f"❌ Page publishing error: {e}")
 results['status'] = 'partial_failure'

 # Small delay between page and groupawait asyncio.sleep(random.randint(30, 90))

 # Publish to grouptry:
 group_post_id = await self._publish_to_group(final_content, image_urls)

 if group_post_id:
 results['group'] = group_post_id
 logger.info(f"✅ Published to group: {group_post_id}")

 await self.database.connection.execute("""
 INSERT INTO published_posts
 (post_id, published_to, facebook_post_id, status)
 VALUES (?, ?, ?, ?)
 """, (post_id, 'group', group_post_id, 'success'))

 self.posts_this_hour += 1
 else:
 if results['status'] != 'partial_failure':
 results['status'] = 'partial_failure'

 await self.database.connection.execute("""
 INSERT INTO published_posts
 (post_id, published_to, status, error_message)
 VALUES (?, ?, ?, ?)
 """, (post_id, 'group', 'failed', 'Failed to publish to group'))

 except Exception as e:
 logger.error(f"❌ Group publishing error: {e}")
 if results['page']:
 results['status'] = 'partial_failure'
 else:
 results['status'] = 'failed'

 await self.database.connection.commit()

 return results


# ============================================================================
# STANDALONE PUBLISHING FUNCTION# ============================================================================

async def run_publishing_cycle(database: Database, max_posts: int = None) -> int:
 """
 Publish processed posts that are ready
 نشر المنشورات المعالجة الجاهزة

 Args:
 database: Database instancemax_posts: Maximum posts to publishReturns:
 Number of posts published"""
 if max_posts is None:
 max_posts = settings.MAX_POSTS_PER_DAY

 # Get posts ready for publishingasync with database.connection.execute("""
 SELECT pp.post_id, pp.final_content, cp.images
 FROM processed_posts pp
 JOIN collected_posts cp ON pp.post_id = cp.post_id
 LEFT JOIN published_posts pub ON pp.post_id = pub.post_id AND pub.published_to = 'page'
 WHERE pub.post_id IS NULL
 ORDER BY pp.processed_at ASC
 LIMIT ?
 """, (max_posts,)) as cursor:
 rows = await cursor.fetchall()
 posts = [dict(row) for row in rows]

 if not posts:
 logger.info("ℹ️ No posts ready for publishing")
 return 0

 logger.info(f"📤 Publishing {len(posts)} posts{len(posts)} منشور")

 published_count = 0

 async with FacebookPublisher(database) as publisher:
 for i, post in enumerate(posts):
 # Parse image URLsimage_urls = post['images'].split(',') if post['images'] else []

 # Publish postresult = await publisher.publish_post(
 post['post_id'],
 post['final_content'],
 image_urls,
 wait_before_publish=(i == 0) # Only wait for first post
 )

 if result['status'] in ['success', 'partial_failure']:
 published_count += 1

 # Random interval between postsif i < len(posts) - 1:
 interval_hours = random.uniform(
 settings.MIN_POSTING_INTERVAL_HOURS,
 settings.MAX_POSTING_INTERVAL_HOURS
 )
 logger.info(f"⏳ Waiting {interval_hours:.1f} hours before next post")
 await asyncio.sleep(interval_hours * 3600)

 logger.info(f"✅ Publishing complete: {published_count}/{len(posts)}")
 return published_count
