"""
Facebook Post Collector - Fetches new posts from competitor pages using Graph API
"""

import aiohttp
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from config import settings
from utils.logger import logger, log_api_call, log_post_activity
from src.database import Database


class FacebookCollector:
    """Collects posts from monitored Facebook pages"""

    def __init__(self, database: Database):
        """Initialize Facebook collector"""
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
        """Check if we're within rate limits"""
        # Reset counter every hour
        if datetime.now() - self.last_reset > timedelta(hours=1):
            self.api_calls_this_hour = 0
            self.last_reset = datetime.now()

        if self.api_calls_this_hour >= settings.MAX_API_CALLS_PER_HOUR:
            logger.warning(f"⚠️ Rate limit reached: {self.api_calls_this_hour} calls/hour")
            return False

        return True

    async def _make_api_call(self, url: str, params: Dict) -> Optional[Dict]:
        """Make Facebook Graph API call with rate limiting"""
        if not self._check_rate_limit():
            await asyncio.sleep(3600)  # Wait 1 hour
            return None

        start_time = datetime.now()

        try:
            async with self.session.get(url, params=params) as response:
                self.api_calls_this_hour += 1
                duration = (datetime.now() - start_time).total_seconds()

                log_api_call("Facebook", url, response.status, duration)

                if response.status == 200:
                    return await response.json()
                elif response.status == 429:  # Too Many Requests
                    logger.warning("⚠️ Rate limited by Facebook")
                    await self.database.log_warning(
                        "rate_limit",
                        "Facebook API rate limit hit",
                        "FacebookCollector"
                    )
                    return None
                else:
                    error_data = await response.text()
                    logger.error(f"❌ API Error {response.status}: {error_data}")
                    return None

        except Exception as e:
            logger.error(f"❌ API call failed: {e}")
            return None

    async def collect_from_page(self, page_info: Dict) -> List[Dict]:
        """Collect posts from a single page"""
        page_id = page_info['id']
        page_name = page_info['name']

        logger.info(f"📥 Collecting from {page_name}")

        url = f"{self.base_url}/{page_id}/posts"
        params = {
            'access_token': self.access_token,
            'fields': 'id,message,created_time,full_picture,permalink_url',
            'limit': 25
        }

        data = await self._make_api_call(url, params)

        if not data or 'data' not in data:
            logger.warning(f"⚠️ No data received from {page_name}")
            return []

        posts = []
        for post in data['data']:
            post_id = post.get('id')
            
            # Check if already collected
            if await self.database.post_exists(post_id):
                continue

            post_data = {
                'post_id': post_id,
                'source_page': page_name,
                'source_website': page_info.get('website'),
                'text': post.get('message', ''),
                'images': [post['full_picture']] if post.get('full_picture') else [],
                'links': [post['permalink_url']] if post.get('permalink_url') else []
            }

            # Save to database
            await self.database.save_collected_post(**post_data)
            posts.append(post_data)
            
            log_post_activity("Collected", post_id, page_name)

        logger.info(f"✅ Collected {len(posts)} new posts from {page_name}")
        return posts

    async def collect_all(self) -> int:
        """Collect from all configured pages"""
        total_collected = 0

        for page_info in settings.SOURCE_PAGES:
            posts = await self.collect_from_page(page_info)
            total_collected += len(posts)
            await asyncio.sleep(2)  # Small delay between pages

        logger.info(f"📊 Total collected: {total_collected} posts")
        return total_collected


async def run_collection_cycle(database: Database) -> int:
    """Run collection cycle"""
    async with FacebookCollector(database) as collector:
        return await collector.collect_all()
