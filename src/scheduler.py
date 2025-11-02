"""
Smart Scheduler - Orchestrates bot operations with timing intelligence
"""

import asyncio
from datetime import datetime, time
from typing import Callable
from config import settings
from utils.logger import logger


class SmartScheduler:
    """Manages bot scheduling and timing"""

    def __init__(self):
        """Initialize scheduler"""
        self.operating_start = time(8, 0)  # 8 AM
        self.operating_end = time(22, 0)   # 10 PM

    def is_operating_hours(self) -> bool:
        """Check if current time is within operating hours"""
        current_time = datetime.now().time()
        return self.operating_start <= current_time <= self.operating_end

    def is_weekend(self) -> bool:
        """Check if today is weekend"""
        return datetime.now().weekday() >= 5  # Saturday = 5, Sunday = 6

    async def wait_until_operating_hours(self):
        """Wait until operating hours start"""
        while not self.is_operating_hours():
            logger.info("⏸️ Outside operating hours, waiting...")
            await asyncio.sleep(1800)  # Check every 30 minutes

    async def run_cycle(
        self,
        collection_func: Callable,
        analysis_func: Callable,
        matching_func: Callable,
        processing_func: Callable,
        publishing_func: Callable
    ):
        """Run complete bot cycle"""
        try:
            logger.info("🔄 Starting bot cycle...")

            # Step 1: Collect posts
            logger.info("📥 Step 1: Collecting posts...")
            collected_count = await collection_func()
            logger.info(f"✅ Collected {collected_count} posts")

            if collected_count == 0:
                logger.info("ℹ️ No new posts to process")
                return

            # Step 2: Analyze content
            logger.info("🧠 Step 2: Analyzing content...")
            await analysis_func()

            # Step 3: Match Trendyol links
            logger.info("🔗 Step 3: Matching Trendyol links...")
            await matching_func()

            # Step 4: Process content
            logger.info("✏️ Step 4: Processing content...")
            await processing_func()

            # Step 5: Publish
            logger.info("📤 Step 5: Publishing...")
            await publishing_func()

            logger.info("✅ Cycle completed successfully")

        except Exception as e:
            logger.error(f"❌ Cycle failed: {e}")

    async def run_scheduled(
        self,
        collection_func: Callable,
        analysis_func: Callable,
        matching_func: Callable,
        processing_func: Callable,
        publishing_func: Callable,
        interval_hours: int = 2
    ):
        """Run cycles on schedule"""
        logger.info(f"🚀 Starting scheduled mode (every {interval_hours} hours)")

        while True:
            try:
                # Wait for operating hours
                await self.wait_until_operating_hours()

                # Skip on weekends if configured
                if settings.SKIP_WEEKENDS and self.is_weekend():
                    logger.info("⏭️ Skipping weekend, waiting...")
                    await asyncio.sleep(3600)  # Check every hour
                    continue

                # Run cycle
                await self.run_cycle(
                    collection_func,
                    analysis_func,
                    matching_func,
                    processing_func,
                    publishing_func
                )

                # Wait for next cycle
                wait_seconds = interval_hours * 3600
                logger.info(f"⏳ Waiting {interval_hours} hours for next cycle...")
                await asyncio.sleep(wait_seconds)

            except Exception as e:
                logger.error(f"❌ Scheduled run failed: {e}")
                await asyncio.sleep(600)  # Wait 10 minutes on error
