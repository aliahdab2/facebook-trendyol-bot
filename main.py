"""
Facebook Trendyol Bot - Main Entry Point
"""

import asyncio
import sys
from datetime import datetime
from config import settings
from utils.logger import logger
from src.database import Database
from src.facebook_collector import run_collection_cycle
from src.content_analyzer import run_analysis_cycle
from src.trendyol_matcher import TrendyolMatcher
from src.content_processor import ContentProcessor
from src.publisher import FacebookPublisher
from src.scheduler import SmartScheduler


def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║        🤖 Facebook Trendyol Affiliate Bot 🤖             ║
║                                                          ║
║  Automated affiliate marketing system for Trendyol      ║
║  Monitors competitor stores → Analyzes with AI →        ║
║  Matches products → Publishes with attribution          ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
    print(banner)
    logger.info("🚀 Bot starting up...")


async def initialize_system() -> Database:
    """Initialize database and systems"""
    logger.info("⚙️ Initializing system...")
    
    # Validate settings
    if not settings.validate():
        logger.error("❌ Configuration invalid. Please check .env file")
        sys.exit(1)
    
    # Initialize database
    db = Database(settings.DATABASE_PATH)
    await db.initialize()
    
    logger.info("✅ System initialized")
    return db


async def run_manual_cycle():
    """Run a single cycle manually"""
    print_banner()
    
    db = await initialize_system()
    
    try:
        logger.info("🔄 Running manual cycle...")
        
        # Step 1: Collect
        logger.info("📥 Step 1/5: Collecting posts from competitor pages...")
        collected = await run_collection_cycle(db)
        logger.info(f"✅ Collected {collected} posts")
        
        if collected == 0:
            logger.info("ℹ️ No new posts to process. Exiting.")
            return
        
        # Step 2: Analyze
        logger.info("🧠 Step 2/5: Analyzing content with AI...")
        await run_analysis_cycle(db)
        
        # Step 3: Match
        logger.info("🔗 Step 3/5: Matching with Trendyol links...")
        matcher = TrendyolMatcher()
        await matcher.load_trendyol_links()
        
        unprocessed = await db.get_unprocessed_posts()
        for post_data in unprocessed:
            post_id = post_data['post_id']
            
            # Get analysis
            analysis = post_data.get('analysis')
            if not analysis:
                continue
            
            # Find match
            match = await matcher.find_best_match(analysis)
            if match:
                await db.save_trendyol_match(
                    post_id=post_id,
                    trendyol_link=match['link'],
                    match_score=match['score']
                )
        
        # Step 4: Process
        logger.info("✏️ Step 4/5: Processing content...")
        processor = ContentProcessor()
        
        matched_posts = await db.get_unprocessed_posts()
        for post_data in matched_posts:
            if not post_data.get('trendyol_link'):
                continue
            
            # Get source attribution
            source_page = post_data['source_page']
            source_website = post_data['source_website']
            source_attribution = f"Source: {source_page} | {source_website}"
            
            # Process
            processed = await processor.process_post(
                post_data,
                post_data['analysis'],
                post_data['trendyol_link'],
                source_attribution
            )
            
            if processed:
                await db.save_processed_post(**processed)
        
        # Step 5: Publish
        logger.info("📤 Step 5/5: Publishing to Facebook...")
        publisher = FacebookPublisher(db)
        
        processed_posts = await db.get_recent_published_posts(limit=10)
        for processed_data in processed_posts:
            result = await publisher.publish_post(processed_data, wait_delay=False)
            logger.info(f"✅ Published: {result}")
        
        logger.info("✅ Manual cycle completed successfully!")
        
        # Show stats
        stats = await db.get_daily_stats()
        logger.info(f"""
📊 Daily Statistics:
   - Collected: {stats.get('collected', 0)}
   - Analyzed: {stats.get('analyzed', 0)}
   - Matched: {stats.get('matched', 0)}
   - Processed: {stats.get('processed', 0)}
   - Published: {stats.get('published', 0)}
""")
        
    except Exception as e:
        logger.error(f"❌ Manual cycle failed: {e}")
    finally:
        await db.close()


async def run_automatic_mode():
    """Run bot in automatic scheduled mode"""
    print_banner()
    
    db = await initialize_system()
    scheduler = SmartScheduler()
    
    try:
        # Define cycle functions
        async def collect():
            return await run_collection_cycle(db)
        
        async def analyze():
            return await run_analysis_cycle(db)
        
        async def match():
            matcher = TrendyolMatcher()
            await matcher.load_trendyol_links()
            unprocessed = await db.get_unprocessed_posts()
            
            for post_data in unprocessed:
                if not post_data.get('analysis'):
                    continue
                
                match_result = await matcher.find_best_match(post_data['analysis'])
                if match_result:
                    await db.save_trendyol_match(
                        post_id=post_data['post_id'],
                        trendyol_link=match_result['link'],
                        match_score=match_result['score']
                    )
        
        async def process():
            processor = ContentProcessor()
            matched_posts = await db.get_unprocessed_posts()
            
            for post_data in matched_posts:
                if not post_data.get('trendyol_link'):
                    continue
                
                source_attribution = f"Source: {post_data['source_page']} | {post_data['source_website']}"
                
                processed = await processor.process_post(
                    post_data,
                    post_data['analysis'],
                    post_data['trendyol_link'],
                    source_attribution
                )
                
                if processed:
                    await db.save_processed_post(**processed)
        
        async def publish():
            publisher = FacebookPublisher(db)
            processed_posts = await db.get_recent_published_posts(limit=5)
            
            for processed_data in processed_posts:
                await publisher.publish_post(processed_data, wait_delay=True)
        
        # Run scheduled
        logger.info("🚀 Starting automatic mode...")
        await scheduler.run_scheduled(
            collection_func=collect,
            analysis_func=analyze,
            matching_func=match,
            processing_func=process,
            publishing_func=publish,
            interval_hours=2
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Stopping bot...")
    except Exception as e:
        logger.error(f"❌ Automatic mode failed: {e}")
    finally:
        await db.close()


def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        asyncio.run(run_manual_cycle())
    else:
        asyncio.run(run_automatic_mode())


if __name__ == "__main__":
    main()
