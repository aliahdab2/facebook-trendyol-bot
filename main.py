"""
Main ApplicationFacebook Trendyol Bot - Automated Affiliate Marketing System
بوت فيسبوك تريندول - نظام تسويق بالعمولة آلي
"""

import asyncio
import sys
from pathlib import Path

# Add project root to pathsys.path.insert(0, str(Path(__file__).parent))

from config import settings
from utils.logger import logger
from src.database import Database
from src.facebook_collector import run_collection_cycle
from src.content_analyzer import run_analysis_cycle
from src.trendyol_matcher import run_matching_cycle
from src.content_processor import run_processing_cycle
from src.publisher import run_publishing_cycle
from src.scheduler import SmartScheduler


async def initialize_system() -> Database:
 """
 Initialize the bot system
 تهيئة نظام البوت

 Returns:
 Initialized database"""
 logger.info("=" * 80)
 logger.info("🚀 FACEBOOK TRENDYOL BOT STARTING")
 logger.info("=" * 80)

 # Validate settingstry:
 settings.validate_settings()
 logger.info("✅ Settings validated")
 except ValueError as e:
 logger.error(f"❌ Configuration error: {e}")
 sys.exit(1)

 # Initialize databasedatabase = Database(settings.DATABASE_PATH)
 await database.connect()
 logger.info("✅ Database initialized")

 # Log configurationlogger.info("📋 Configuration:")
 logger.info(f" Operating hours: {settings.COLLECTION_START_HOUR}:00 - {settings.COLLECTION_END_HOUR}:00")
 logger.info(f" Collection interval: {settings.COLLECTION_INTERVAL_HOURS} hours")
 logger.info(f" Max posts/day: {settings.MAX_POSTS_PER_DAY}")
 logger.info(f" Source pages: {len(settings.SOURCE_PAGES)}")
 logger.info("=" * 80)

 return database


async def run_manual_cycle(database: Database):
 """
 Run a single manual cycle (for testing)
 تشغيل دورة يدوية واحدة (للاختبار)

 Args:
 database: Database instance"""
 logger.info("🔧 MANUAL CYCLE MODE")
 logger.info("Running one complete cycle......")

 scheduler = SmartScheduler(database)

 await scheduler.run_cycle(
 run_collection_cycle,
 run_analysis_cycle,
 run_matching_cycle,
 run_processing_cycle,
 run_publishing_cycle
 )

 logger.info("✅ Manual cycle complete")


async def run_automatic_mode(database: Database):
 """
 Run bot in automatic continuous mode
 تشغيل البوت في الوضع التلقائي المستمر

 Args:
 database: Database instance"""
 logger.info("🤖 AUTOMATIC MODE")
 logger.info("Bot will run continuously... Press Ctrl+C to stop... اضغط Ctrl+C للإيقاف")

 scheduler = SmartScheduler(database)

 try:
 await scheduler.start(
 run_collection_cycle,
 run_analysis_cycle,
 run_matching_cycle,
 run_processing_cycle,
 run_publishing_cycle
 )
 except KeyboardInterrupt:
 logger.info("⏹️ Shutdown requested")
 scheduler.stop()


async def main():
 """
 Main entry point
 نقطة الدخول الرئيسية
 """
 database = None

 try:
 # Initialize systemdatabase = await initialize_system()

 # Check command line argumentsmode = sys.argv[1] if len(sys.argv) > 1 else "auto"

 if mode == "manual":
 # Run single cycleawait run_manual_cycle(database)
 else:
 # Run automatic continuous modeawait run_automatic_mode(database)

 except Exception as e:
 logger.error(f"❌ Fatal error: {e}")
 sys.exit(1)

 finally:
 # Cleanupif database:
 await database.disconnect()
 logger.info("✅ Database disconnected")

 logger.info("=" * 80)
 logger.info("👋 BOT STOPPED")
 logger.info("=" * 80)


if __name__ == "__main__":
 """
 Entry point when script is run directly
 نقطة الدخول عند تشغيل السكريبت مباشرة

 Usage:
 python main.py # Automatic modepython main.py manual # Manual single cycle"""

 # Print bannerprint("=" * 80)
 print(" ______ ____ ____ _ __ ____ ____ ______")
 print("_____ \\ / __ \\|/ /_ \\ / __ \\____|")
 print("|__|_)' /|_)|__ ")
 print("___ <<_ <__")
 print("|_)|__. \\|_)|__")
 print(" |_|____/ \\____/|_|\\_\\ |____/ \\____/|_")
 print()
 print(" Facebook Trendyol Bot")
 print(" Automated Affiliate Marketing System")
 print(" نظام تسويق بالعمولة آلي")
 print("=" * 80)
 print()

 # Run main async functiontry:
 asyncio.run(main())
 except KeyboardInterrupt:
 print("\n👋 Goodbye!!")
