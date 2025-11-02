"""
Facebook Publisher - Posts content to Facebook page and group
"""

import aiohttp
import asyncio
import random
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from config import settings
from utils.logger import logger, log_api_call, log_post_activity
from src.database import Database


class FacebookPublisher:
    """Publishes processed content to Facebook"""

    def __init__(self, database: Database):
        """Initialize publisher"""
        self.database = database
        self.page_access_token = settings.FACEBOOK_PAGE_ACCESS_TOKEN
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
        """Check posting rate limit"""
        if datetime.now() - self.last_reset > timedelta(hours=1):
            self.posts_this_hour = 0
            self.last_reset = datetime.now()

        if self.posts_this_hour >= 5:  # Max 5 posts per hour
            logger.warning(f"⚠️ Post rate limit reached: {self.posts_this_hour}/hour")
            return False

        return True

    async def _wait_random_delay(self, min_minutes: int = 30, max_minutes: int = 120):
        """Wait random delay after original post"""
        delay_minutes = random.randint(min_minutes, max_minutes)
        delay_seconds = delay_minutes * 60
        
        logger.info(f"⏳ Waiting {delay_minutes} minutes before posting...")
        await asyncio.sleep(delay_seconds)

    async def _publish_to_page(
        self,
        page_id: str,
        message: str,
        image_urls: List[str]
    ) -> Optional[str]:
        """Publish post to Facebook page"""
        if not self._check_post_rate_limit():
            return None

        url = f"{self.base_url}/{page_id}/feed"
        
        data = {
            'message': message,
            'access_token': self.page_access_token
        }

        # Add first image if available
        if image_urls and len(image_urls) > 0:
            data['link'] = image_urls[0]

        start_time = datetime.now()

        try:
            async with self.session.post(url, data=data) as response:
                self.posts_this_hour += 1
                duration = (datetime.now() - start_time).total_seconds()

                log_api_call("Facebook Post", url, response.status, duration)

                if response.status == 200:
                    result = await response.json()
                    post_id = result.get('id')
                    logger.info(f"✅ Published to page: {post_id}")
                    return post_id
                else:
                    error_data = await response.text()
                    logger.error(f"❌ Post failed {response.status}: {error_data}")
                    
                    if response.status == 429:
                        await self.database.log_warning(
                            "rate_limit",
                            "Facebook posting rate limit hit",
                            "FacebookPublisher"
                        )
                    
                    return None

        except Exception as e:
            logger.error(f"❌ Publishing failed: {e}")
            return None

    async def _publish_to_group(
        self,
        group_id: str,
        message: str,
        image_urls: List[str]
    ) -> Optional[str]:
        """Publish post to Facebook group"""
        if not self._check_post_rate_limit():
            return None

        url = f"{self.base_url}/{group_id}/feed"
        
        data = {
            'message': message,
            'access_token': self.page_access_token
        }

        # Add first image if available
        if image_urls and len(image_urls) > 0:
            data['link'] = image_urls[0]

        start_time = datetime.now()

        try:
            async with self.session.post(url, data=data) as response:
                self.posts_this_hour += 1
                duration = (datetime.now() - start_time).total_seconds()

                log_api_call("Facebook Group Post", url, response.status, duration)

                if response.status == 200:
                    result = await response.json()
                    post_id = result.get('id')
                    logger.info(f"✅ Published to group: {post_id}")
                    return post_id
                else:
                    error_data = await response.text()
                    logger.error(f"❌ Group post failed {response.status}: {error_data}")
                    return None

        except Exception as e:
            logger.error(f"❌ Group publishing failed: {e}")
            return None

    async def publish_post(
        self,
        processed_data: Dict,
        wait_delay: bool = True
    ) -> Dict:
        """Publish to both page and group"""
        try:
            # Wait random delay if requested
            if wait_delay:
                await self._wait_random_delay()

            original_post_id = processed_data['post_id']
            message = processed_data['final_text']
            image_urls = processed_data.get('images', [])

            results = {
                'original_post_id': original_post_id,
                'page_post_id': None,
                'group_post_id': None,
                'success': False
            }

            # Publish to page
            page_post_id = await self._publish_to_page(
                settings.FACEBOOK_PAGE_ID,
                message,
                image_urls
            )

            if page_post_id:
                results['page_post_id'] = page_post_id
                log_post_activity("Published to Page", page_post_id)

            # Wait between page and group posts
            await asyncio.sleep(random.randint(60, 180))

            # Publish to group
            if settings.FACEBOOK_GROUP_ID:
                group_post_id = await self._publish_to_group(
                    settings.FACEBOOK_GROUP_ID,
                    message,
                    image_urls
                )

                if group_post_id:
                    results['group_post_id'] = group_post_id
                    log_post_activity("Published to Group", group_post_id)

            # Mark as success if at least one published
            results['success'] = bool(page_post_id or results['group_post_id'])

            # Save to database
            if results['success']:
                await self.database.save_published_post(
                    original_post_id=original_post_id,
                    page_post_id=page_post_id,
                    group_post_id=results['group_post_id'],
                    final_text=message,
                    images=image_urls
                )

            return results

        except Exception as e:
            logger.error(f"❌ Publishing process failed: {e}")
            return {'success': False, 'error': str(e)}


async def publish_single_post(
    database: Database,
    processed_data: Dict,
    wait_delay: bool = True
) -> Dict:
    """Publish a single processed post"""
    async with FacebookPublisher(database) as publisher:
        return await publisher.publish_post(processed_data, wait_delay)
