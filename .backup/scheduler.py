"""
Smart SchedulerOrchestrates all bot operations with intelligent timing
ينظم جميع عمليات البوت بتوقيت ذكي
"""

import asyncio
from datetime import datetime, time
from typing import Callable
from config import settings
from utils.logger import logger, log_daily_summary
from src.database import Database


class SmartScheduler:
 """
 Smart scheduler for bot operations
 مجدول ذكي لعمليات البوت
 """

 def __init__(self, database: Database):
 """
 Initialize smart scheduler
 تهيئة المجدول الذكي

 Args:
 database: Database instance"""
 self.database = database
 self.is_running = False
 self.tasks = []

 def is_operating_hours(self) -> bool:
 """
 Check if current time is within operating hours
 التحقق من ساعات التشغيل

 Returns:
 True if within hours"""
 current_hour = datetime.now().hour
 return settings.COLLECTION_START_HOUR <= current_hour < settings.COLLECTION_END_HOUR

 def is_weekend(self) -> bool:
 """
 Check if today is weekend
 التحقق من عطلة نهاية الأسبوع

 Returns:
 True if weekend"""
 # Friday (4) and Saturday (5) in Python's weekday()
 return datetime.now().weekday() in [4, 5]

 async def run_cycle(
 self,
 collection_func: Callable,
 analysis_func: Callable,
 matching_func: Callable,
 processing_func: Callable,
 publishing_func: Callable
 ):
 """
 Run a complete bot cycle
 تشغيل دورة كاملة للبوت

 Args:
 collection_func: Collection functionanalysis_func: Analysis functionmatching_func: Matching functionprocessing_func: Processing functionpublishing_func: Publishing function"""
 logger.info("=" * 80)
 logger.info("🤖 Starting bot cycle")
 logger.info(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
 logger.info("=" * 80)

 cycle_stats = {
 'collected': 0,
 'analyzed': 0,
 'matched': 0,
 'processed': 0,
 'published': 0
 }

 try:
 # STEP 1: Collectionif self.is_operating_hours():
 logger.info("📥 Step 1: Collecting posts1: جمع المنشورات")
 cycle_stats['collected'] = await collection_func(self.database)
 await asyncio.sleep(5)
 else:
 logger.info("⏸️ Skipping collection (outside operating hours)(خارج ساعات العمل)")

 # STEP 2: Analysislogger.info("🔍 Step 2: Analyzing posts2: تحليل المنشورات")
 cycle_stats['analyzed'] = await analysis_func(self.database)
 await asyncio.sleep(5)

 # STEP 3: Matchinglogger.info("🔗 Step 3: Matching Trendyol links3: مطابقة روابط تريندول")
 cycle_stats['matched'] = await matching_func(self.database)
 await asyncio.sleep(5)

 # STEP 4: Processinglogger.info("⚙️ Step 4: Processing content4: معالجة المحتوى")
 cycle_stats['processed'] = await processing_func(self.database)
 await asyncio.sleep(5)

 # STEP 5: Publishingmax_posts = settings.MAX_POSTS_PER_DAY

 # Reduce posts on weekendif self.is_weekend():
 max_posts = int(max_posts * settings.WEEKEND_POST_REDUCTION)
 logger.info(f"📅 Weekend mode: Publishing max {max_posts} posts")

 logger.info("📤 Step 5: Publishing posts5: نشر المنشورات")
 cycle_stats['published'] = await publishing_func(self.database, max_posts)

 except Exception as e:
 logger.error(f"❌ Cycle error: {e}")
 await self.database.log_warning(
 "cycle_error",
 f"Bot cycle failed: {str(e)}",
 "SmartScheduler"
 )

 # Log cycle summarylogger.info("=" * 80)
 logger.info("📊 Cycle Summary:")
 logger.info(f" Collected: {cycle_stats['collected']}")
 logger.info(f" Analyzed: {cycle_stats['analyzed']}")
 logger.info(f" Matched: {cycle_stats['matched']}")
 logger.info(f" Processed: {cycle_stats['processed']}")
 logger.info(f" Published: {cycle_stats['published']}")
 logger.info("=" * 80)

 async def run_daily_report(self):
 """
 Generate and log daily report
 توليد وتسجيل التقرير اليومي
 """
 logger.info("=" * 80)
 logger.info("📊 DAILY REPORT")
 logger.info("=" * 80)

 # Get today's statsstats = await self.database.get_daily_stats()

 log_daily_summary(
 stats.get('collected', 0),
 stats.get('collected', 0), # Analyzed ~ collected
 stats.get('published', 0),
 stats.get('failed', 0)
 )

 # Check for warningswarnings = await self.database.get_active_warnings()

 if warnings:
 logger.warning(f"⚠️ Active warnings: {len(warnings)}")
 for warning in warnings[:5]: # Show first 5
 logger.warning(f" - {warning['warning_type']}: {warning['message']}")

 async def start(
 self,
 collection_func: Callable,
 analysis_func: Callable,
 matching_func: Callable,
 processing_func: Callable,
 publishing_func: Callable
 ):
 """
 Start the scheduler loop
 بدء حلقة المجدول

 Args:
 collection_func: Collection functionanalysis_func: Analysis functionmatching_func: Matching functionprocessing_func: Processing functionpublishing_func: Publishing function"""
 self.is_running = True

 logger.info("🚀 Smart Scheduler started")
 logger.info(f"⏰ Operating hours: {settings.COLLECTION_START_HOUR}:00 - {settings.COLLECTION_END_HOUR}:00")
 logger.info(f"🔄 Collection interval: Every {settings.COLLECTION_INTERVAL_HOURS} hours")
 logger.info(f"📊 Daily report time: {settings.DAILY_REPORT_HOUR}:00")

 last_cycle_hour = -1
 last_report_day = -1

 while self.is_running:
 try:
 current_time = datetime.now()
 current_hour = current_time.hour
 current_day = current_time.day

 # Run cycle every N hours during operating hours
 # تشغيل الدورة كل N ساعة خلال ساعات العمل
 if current_hour != last_cycle_hour and current_hour % settings.COLLECTION_INTERVAL_HOURS == 0:
 await self.run_cycle(
 collection_func,
 analysis_func,
 matching_func,
 processing_func,
 publishing_func
 )
 last_cycle_hour = current_hour

 # Run daily report at configured time
 # تشغيل التقرير اليومي في الوقت المحدد
 if current_hour == settings.DAILY_REPORT_HOUR and current_day != last_report_day:
 await self.run_daily_report()
 last_report_day = current_day

 # Sleep for 1 hourawait asyncio.sleep(3600)

 except KeyboardInterrupt:
 logger.info("⏹️ Scheduler stopped by user")
 self.is_running = False
 break

 except Exception as e:
 logger.error(f"❌ Scheduler error: {e}")
 await self.database.log_warning(
 "scheduler_error",
 f"Scheduler error: {str(e)}",
 "SmartScheduler"
 )
 # Wait before retryawait asyncio.sleep(300) # 5 minutes

 def stop(self):
 """Stop the scheduler"""
 logger.info("🛑 Stopping scheduler...")
 self.is_running = False
