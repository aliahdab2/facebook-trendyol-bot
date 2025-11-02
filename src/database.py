"""
Database LayerAsync SQLite database with proper schema for tracking posts
قاعدة بيانات SQLite غير متزامنة مع مخطط مناسب لتتبع المنشورات
"""

import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from utils.logger import logger, log_operation

class Database:
 """
 Async database manager for Facebook bot
 مدير قاعدة البيانات غير المتزامن لبوت فيسبوك
 """

 def __init__(self, db_path: str):
 """
 Initialize database connection
 تهيئة اتصال قاعدة البيانات

 Args:
 db_path: Path to SQLite database file"""
 self.db_path = db_path
 Path(db_path).parent.mkdir(parents=True, exist_ok=True)
 self.connection = None

 async def connect(self):
 """Establish database connection"""
 try:
 self.connection = await aiosqlite.connect(self.db_path)
 self.connection.row_factory = aiosqlite.Row
 await self._create_tables()
 log_operation("Database Connection", True, self.db_path)
 except Exception as e:
 log_operation("Database Connection", False, str(e))
 raise

 async def disconnect(self):
 """Close database connection"""
 if self.connection:
 await self.connection.close()
 log_operation("Database Disconnection", True)

 async def _create_tables(self):
 """
 Create database schema
 إنشاء مخطط قاعدة البيانات
 """

 # ====================================================================
 # COLLECTED POSTS TABLE# ====================================================================
 await self.connection.execute("""
 CREATE TABLE IF NOT EXISTS collected_posts (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 post_id TEXT UNIQUE NOT NULL,
 source_page TEXT NOT NULL,
 source_website TEXT,
 original_text TEXT,
 images TEXT,
 links TEXT,
 collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 is_processed BOOLEAN DEFAULT 0,
 INDEX idx_post_id (post_id),
 INDEX idx_source (source_page),
 INDEX idx_processed (is_processed)
 )
 """)

 # ====================================================================
 # ANALYZED POSTS TABLE# ====================================================================
 await self.connection.execute("""
 CREATE TABLE IF NOT EXISTS analyzed_posts (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 post_id TEXT UNIQUE NOT NULL,
 product_name TEXT,
 category TEXT,
 keywords TEXT,
 price TEXT,
 discount TEXT,
 is_suitable BOOLEAN DEFAULT 1,
 quality_score FLOAT,
 analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (post_id) REFERENCES collected_posts(post_id),
 INDEX idx_suitable (is_suitable),
 INDEX idx_quality (quality_score)
 )
 """)

 # ====================================================================
 # TRENDYOL MATCHES TABLE# ====================================================================
 await self.connection.execute("""
 CREATE TABLE IF NOT EXISTS trendyol_matches (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 post_id TEXT UNIQUE NOT NULL,
 trendyol_link TEXT,
 confidence_score FLOAT,
 matched_keywords TEXT,
 matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (post_id) REFERENCES analyzed_posts(post_id),
 INDEX idx_confidence (confidence_score)
 )
 """)

 # ====================================================================
 # PROCESSED POSTS TABLE# ====================================================================
 await self.connection.execute("""
 CREATE TABLE IF NOT EXISTS processed_posts (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 post_id TEXT UNIQUE NOT NULL,
 modified_text TEXT NOT NULL,
 promotional_text TEXT,
 hashtags TEXT,
 source_attribution TEXT,
 final_content TEXT,
 processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (post_id) REFERENCES analyzed_posts(post_id)
 )
 """)

 # ====================================================================
 # PUBLISHED POSTS TABLE# ====================================================================
 await self.connection.execute("""
 CREATE TABLE IF NOT EXISTS published_posts (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 post_id TEXT NOT NULL,
 published_to TEXT NOT NULL,
 facebook_post_id TEXT,
 published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 status TEXT DEFAULT 'success',
 error_message TEXT,
 engagement_count INTEGER DEFAULT 0,
 FOREIGN KEY (post_id) REFERENCES processed_posts(post_id),
 INDEX idx_status (status),
 INDEX idx_published_at (published_at)
 )
 """)

 # ====================================================================
 # SYSTEM LOGS TABLE# ====================================================================
 await self.connection.execute("""
 CREATE TABLE IF NOT EXISTS system_logs (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 log_type TEXT NOT NULL,
 message TEXT,
 details TEXT,
 severity TEXT DEFAULT 'info',
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 INDEX idx_severity (severity),
 INDEX idx_created_at (created_at)
 )
 """)

 # ====================================================================
 # WARNINGS TABLE# ====================================================================
 await self.connection.execute("""
 CREATE TABLE IF NOT EXISTS warnings (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 warning_type TEXT NOT NULL,
 message TEXT,
 source TEXT,
 is_resolved BOOLEAN DEFAULT 0,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 resolved_at TIMESTAMP,
 INDEX idx_resolved (is_resolved)
 )
 """)

 await self.connection.commit()
 logger.info("✅ Database schema created")

 # ========================================================================
 # COLLECTED POSTS METHODS# ========================================================================

 async def save_collected_post(self, post_data: Dict) -> bool:
 """
 Save a collected post
 حفظ منشور مجموع

 Args:
 post_data: Post informationReturns:
 Success status"""
 try:
 await self.connection.execute("""
 INSERT OR IGNORE INTO collected_posts
 (post_id, source_page, source_website, original_text, images, links)
 VALUES (?, ?, ?, ?, ?, ?)
 """, (
 post_data['post_id'],
 post_data['source_page'],
 post_data.get('source_website'),
 post_data.get('text'),
 ','.join(post_data.get('images', [])),
 ','.join(post_data.get('links', []))
 ))
 await self.connection.commit()
 return True
 except Exception as e:
 logger.error(f"Failed to save collected post: {e}")
 return False

 async def get_unprocessed_posts(self, limit: int = 50) -> List[Dict]:
 """
 Get posts that haven't been processed yet
 الحصول على المنشورات التي لم تتم معالجتها

 Args:
 limit: Maximum number of postsReturns:
 List of unprocessed posts"""
 async with self.connection.execute("""
 SELECT * FROM collected_posts
 WHERE is_processed = 0
 ORDER BY collected_at ASC
 LIMIT ?
 """, (limit,)) as cursor:
 rows = await cursor.fetchall()
 return [dict(row) for row in rows]

 async def mark_post_as_processed(self, post_id: str) -> bool:
 """
 Mark a post as processed
 تعليم منشور كمعالج
 """
 try:
 await self.connection.execute("""
 UPDATE collected_posts
 SET is_processed = 1
 WHERE post_id = ?
 """, (post_id,))
 await self.connection.commit()
 return True
 except Exception as e:
 logger.error(f"Failed to mark as processed: {e}")
 return False

 async def post_exists(self, post_id: str) -> bool:
 """
 Check if post already exists
 التحقق من وجود منشور
 """
 async with self.connection.execute("""
 SELECT COUNT(*) FROM collected_posts WHERE post_id = ?
 """, (post_id,)) as cursor:
 result = await cursor.fetchone()
 return result[0] > 0

 # ========================================================================
 # ANALYZED POSTS METHODS# ========================================================================

 async def save_analysis(self, post_id: str, analysis: Dict) -> bool:
 """Save post analysis results"""
 try:
 await self.connection.execute("""
 INSERT OR REPLACE INTO analyzed_posts
 (post_id, product_name, category, keywords, price, discount,
 is_suitable, quality_score)
 VALUES (?, ?, ?, ?, ?, ?, ?, ?)
 """, (
 post_id,
 analysis.get('product_name'),
 analysis.get('category'),
 ','.join(analysis.get('keywords', [])),
 analysis.get('price'),
 analysis.get('discount'),
 analysis.get('is_suitable', True),
 analysis.get('quality_score', 0.0)
 ))
 await self.connection.commit()
 return True
 except Exception as e:
 logger.error(f"Failed to save analysis: {e}")
 return False

 # ========================================================================
 # STATISTICS METHODS# ========================================================================

 async def get_daily_stats(self, date: str = None) -> Dict:
 """
 Get statistics for a specific date
 الحصول على إحصائيات لتاريخ معين

 Args:
 date: Date in YYYY-MM-DD formatYYYY-MM-DD

 Returns:
 Statistics dictionary"""
 if not date:
 date = datetime.now().strftime("%Y-%m-%d")

 stats = {}

 # Collected postsasync with self.connection.execute("""
 SELECT COUNT(*) FROM collected_posts
 WHERE DATE(collected_at) = ?
 """, (date,)) as cursor:
 result = await cursor.fetchone()
 stats['collected'] = result[0]

 # Published postsasync with self.connection.execute("""
 SELECT COUNT(*) FROM published_posts
 WHERE DATE(published_at) = ? AND status = 'success'
 """, (date,)) as cursor:
 result = await cursor.fetchone()
 stats['published'] = result[0]

 # Failed postsasync with self.connection.execute("""
 SELECT COUNT(*) FROM published_posts
 WHERE DATE(published_at) = ? AND status = 'failed'
 """, (date,)) as cursor:
 result = await cursor.fetchone()
 stats['failed'] = result[0]

 return stats

 async def log_warning(self, warning_type: str, message: str, source: str = None):
 """Log a system warning"""
 await self.connection.execute("""
 INSERT INTO warnings (warning_type, message, source)
 VALUES (?, ?, ?)
 """, (warning_type, message, source))
 await self.connection.commit()

 async def get_active_warnings(self) -> List[Dict]:
 """Get unresolved warnings"""
 async with self.connection.execute("""
 SELECT * FROM warnings
 WHERE is_resolved = 0
 ORDER BY created_at DESC
 """, ) as cursor:
 rows = await cursor.fetchall()
 return [dict(row) for row in rows]
