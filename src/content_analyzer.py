"""
Content Analyzer - Analyzes posts using GPT-3.5 to extract product information
"""

import openai
import json
from typing import Dict, Optional
from config import settings
from utils.logger import logger, log_api_call, log_post_activity
from src.database import Database


class ContentAnalyzer:
    """Analyzes post content using AI"""

    def __init__(self, database: Database):
        """
        Initialize content analyzer
        
        Args:
            database: Database instance
        """
        self.database = database
        openai.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL

    def _create_analysis_prompt(self, text: str, source: str) -> str:
        """
        Create analysis prompt for GPT - prompt in Arabic for better results with Arabic content
        
        Args:
            text: Post text
            source: Source page name
            
        Returns:
            Formatted prompt
        """
        return f"""أنت محلل محتوى متخصص في المنشورات الإعلانية للمتاجر السعودية.

قم بتحليل المنشور التالي من متجر {source} واستخرج المعلومات بصيغة JSON:

النص:
{text}

يجب أن يحتوي الرد على JSON فقط بهذا الشكل:
{{
 "product_name": "اسم المنتج بالعربية",
 "category": "الفئة (إلكترونيات، ملابس، منزل، طعام، إلخ)",
 "keywords": ["كلمة1", "كلمة2", "كلمة3"],
 "price": "السعر إن وجد",
 "discount": "نسبة التخفيض إن وجدت",
 "is_suitable": true/false,
 "quality_score": 0.0-1.0,
 "reason": "سبب قصير للتقييم"
}}

ملاحظات:
- is_suitable = true إذا كان المنشور يعرض منتج واضح ومناسب للنشر
- is_suitable = false إذا كان المنشور غير مناسب (تهنئة، إعلان وظيفة، إلخ)
- quality_score = تقييم جودة المنشور من 0 إلى 1
- keywords = كلمات مفتاحية مهمة للبحث والمطابقة"""

    async def analyze_post(self, post_id: str, text: str, source: str) -> Optional[Dict]:
        """
        Analyze a single post
        
        Args:
            post_id: Post ID
            text: Post text
            source: Source page
            
        Returns:
            Analysis results
        """
        if not text or len(text.strip()) < 10:
            logger.warning(f"⚠️ Post too short to analyze: {post_id}")
            return None

        log_post_activity("Analyzing", post_id, source)

        try:
            prompt = self._create_analysis_prompt(text, source)

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "أنت محلل محتوى خبير. أجب بصيغة JSON فقط."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            log_api_call("OpenAI", "chat/completions", 200)

            # Parse response
            content = response.choices[0].message.content.strip()

            # Sometimes GPT wraps JSON in code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            analysis = json.loads(content)

            # Save analysis to database
            await self.database.save_analysis(post_id, analysis)

            # Log result
            suitable = "✅ Suitable" if analysis.get('is_suitable') else "❌ Not suitable"
            logger.info(f"{suitable} - {analysis.get('product_name', 'Unknown')} - Score: {analysis.get('quality_score', 0):.2f}")

            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON: {e}")
            logger.error(f"Response content: {content}")
            return None

        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            await self.database.log_warning(
                "analysis_error",
                f"Failed to analyze post {post_id}: {str(e)}",
                "ContentAnalyzer"
            )
            return None

    async def analyze_batch(self, posts: list) -> list:
        """
        Analyze multiple posts
        
        Args:
            posts: List of posts to analyze
            
        Returns:
            List of analysis results
        """
        logger.info(f"🔍 Analyzing {len(posts)} posts")

        results = []

        for post in posts:
            analysis = await self.analyze_post(
                post['post_id'],
                post.get('text', ''),
                post['source_page']
            )

            if analysis:
                results.append({
                    'post_id': post['post_id'],
                    'analysis': analysis
                })

        # Filter suitable posts
        suitable = [r for r in results if r['analysis'].get('is_suitable', False)]

        logger.info(f"✅ Analysis complete: {len(suitable)}/{len(results)} suitable")

        return results

    async def select_best_posts(self, analyzed_posts: list, max_count: int = None) -> list:
        """
        Select best posts based on quality score
        
        Args:
            analyzed_posts: List of analyzed posts
            max_count: Maximum posts to select
            
        Returns:
            Selected best posts
        """
        if max_count is None:
            max_count = settings.MAX_POSTS_PER_DAY

        # Filter suitable posts
        suitable = [p for p in analyzed_posts if p['analysis'].get('is_suitable', False)]

        # Sort by quality score
        sorted_posts = sorted(
            suitable,
            key=lambda x: x['analysis'].get('quality_score', 0),
            reverse=True
        )

        # Select top posts
        selected = sorted_posts[:max_count]

        logger.info(f"🎯 Selected {len(selected)} best posts")

        return selected


# Standalone analysis function
async def run_analysis_cycle(database: Database) -> int:
    """
    Run analysis on unprocessed posts
    
    Args:
        database: Database instance
        
    Returns:
        Number of posts analyzed
    """
    analyzer = ContentAnalyzer(database)

    # Get unprocessed posts
    posts = await database.get_unprocessed_posts(limit=50)

    if not posts:
        logger.info("ℹ️ No posts to analyze")
        return 0

    # Analyze posts
    results = await analyzer.analyze_batch(posts)

    # Mark as processed
    for post in posts:
        await database.mark_post_as_processed(post['post_id'])

    return len(results)
