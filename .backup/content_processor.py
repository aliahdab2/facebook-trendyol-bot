"""
Content ProcessorModifies original content and generates promotional texts
يعدل المحتوى الأصلي ويولد النصوص الترويجية
"""

import openai
import random
from typing import Dict, List, Optional
from config import settings
from utils.logger import logger, log_api_call
from src.database import Database


class ContentProcessor:
 """
 Processes and modifies post content with AI
 يعالج ويعدل محتوى المنشور بالذكاء الاصطناعي
 """

 def __init__(self, database: Database):
 """
 Initialize content processor
 تهيئة معالج المحتوى

 Args:
 database: Database instance"""
 self.database = database
 openai.api_key = settings.OPENAI_API_KEY
 self.model = settings.OPENAI_MODEL

 def _create_modification_prompt(self, original_text: str, modification_level: int = 40) -> str:
 """
 Create prompt for text modification
 إنشاء طلب لتعديل النص

 Args:
 original_text: Original post textmodification_level: Modification percentageReturns:
 GPT promptGPT
 """
 return f"""أنت كاتب محتوى محترف. قم بإعادة صياغة النص التالي بنسبة تعديل {modification_level}%.

النص الأصلي:
{original_text}

متطلبات إعادة الصياغة:
1. احتفظ بجميع المعلومات المهمة (اسم المنتج، السعر، التخفيض)
2. غيّر الإيموجي إلى إيموجي مختلفة ومناسبة
3. أعد ترتيب الجمل
4. استخدم مرادفات ومصطلحات مختلفة
5. غيّر أسلوب الكتابة قليلاً (من رسمي لودود أو العكس)
6. احذف أي أرقام هواتف أو عناوين محددة

ملاحظة: لا تضف روابط أو معلومات جديدة. فقط أعد صياغة النص الموجود.

النص المعدل:"""

 def _create_promotional_prompt(self, product_name: str, category: str, trendyol_link: str) -> str:
 """
 Create prompt for Trendyol promotional text
 إنشاء طلب للنص الترويجي لتريندول

 Args:
 product_name: Product namecategory: Product categorytrendyol_link: Trendyol affiliate linkReturns:
 GPT promptGPT
 """
 templates = [
 "مقارنة أسعار تريندول",
 "عروض تريندول الحصرية",
 "توصيل مجاني من تريندول",
 "تسوق أونلاين من تريندول"
 ]

 template_choice = random.choice(templates)

 return f"""اكتب نص ترويجي قصير (2-3 أسطر فقط) لتشجيع الناس على مقارنة الأسعار في تريندول.

المنتج: {product_name}
الفئة: {category}
الرابط: {trendyol_link}
الأسلوب: {template_choice}

المتطلبات:
1. نص قصير وجذاب
2. يشجع على المقارنة (ليس إلزام شراء)
3. يذكر ميزة (مثل: توصيل مجاني، أسعار منافسة، تشكيلة واسعة)
4. يحتوي إيموجي واحد أو اثنين مناسبين
5. لا تذكر أسعار محددة

النص الترويجي:"""

 def _generate_hashtags(self, source: str, category: str, product_name: str) -> str:
 """
 Generate smart hashtags
 توليد هاشتاقات ذكية

 Args:
 source: Source store namecategory: Product categoryproduct_name: Product nameReturns:
 Hashtags string"""
 hashtags = []

 # Source store hashtagssource_tags = {
 "Al Othaim": ["#العثيم", "#عروض_العثيم"],
 "Al Saif": ["#السيف_غاليري", "#السيف"],
 "Safaco": ["#صافكو", "#Safaco"],
 "Panda": ["#بنده", "#Panda"]
 }

 if source in source_tags:
 hashtags.extend(source_tags[source])

 # Trendyol hashtagshashtags.extend(["#تريندول", "#Trendyol"])

 # Category hashtagscategory_tags = {
 "إلكترونيات": ["#إلكترونيات", "#تقنية"],
 "ملابس": ["#ملابس", "#أزياء"],
 "منزل": ["#منزل", "#ديكور"],
 "طعام": ["#طعام", "#مأكولات"],
 "أجهزة": ["#أجهزة", "#إلكترونيات"]
 }

 for key, tags in category_tags.items():
 if key in category:
 hashtags.extend(tags[:1]) # Add one category tag
 break

 # General hashtagsgeneral = ["#عروض", "#تخفيضات", "#السعودية", "#توفير", "#تسوق_اونلاين"]
 hashtags.extend(random.sample(general, 2))

 # Limit to configured rangecount = random.randint(settings.MIN_HASHTAGS, settings.MAX_HASHTAGS)
 selected = hashtags[:count]

 return " ".join(selected)

 async def process_post(
 self,
 post_id: str,
 original_text: str,
 source_page: str,
 source_website: str,
 analysis: Dict,
 trendyol_match: Dict
 ) -> Optional[Dict]:
 """
 Process a complete post with modifications and promotional content
 معالجة منشور كامل مع التعديلات والمحتوى الترويجي

 Args:
 post_id: Post IDoriginal_text: Original post textsource_page: Source page namesource_website: Source website URLanalysis: Post analysis resultstrendyol_match: Trendyol match dataReturns:
 Processed post data"""
 logger.info(f"⚙️ Processing post: {post_id}")

 try:
 # ================================================================
 # STEP 1: Modify original text# ================================================================

 modification_level = random.randint(
 settings.MIN_MODIFICATION_PERCENT,
 settings.MAX_MODIFICATION_PERCENT
 )

 modification_prompt = self._create_modification_prompt(original_text, modification_level)

 modification_response = openai.ChatCompletion.create(
 model=self.model,
 messages=[
 {"role": "system", "content": "أنت كاتب محتوى محترف متخصص في إعادة الصياغة."},
 {"role": "user", "content": modification_prompt}
 ],
 temperature=0.7,
 max_tokens=300
 )

 modified_text = modification_response.choices[0].message.content.strip()
 log_api_call("OpenAI", "text_modification", 200)

 # ================================================================
 # STEP 2: Generate promotional text# ================================================================

 promotional_prompt = self._create_promotional_prompt(
 analysis.get('product_name', ''),
 analysis.get('category', ''),
 trendyol_match.get('trendyol_link', '')
 )

 promo_response = openai.ChatCompletion.create(
 model=self.model,
 messages=[
 {"role": "system", "content": "أنت كاتب محتوى تسويقي محترف."},
 {"role": "user", "content": promotional_prompt}
 ],
 temperature=0.8,
 max_tokens=150
 )

 promotional_text = promo_response.choices[0].message.content.strip()
 log_api_call("OpenAI", "promotional_generation", 200)

 # ================================================================
 # STEP 3: Generate hashtags# ================================================================

 hashtags = self._generate_hashtags(
 source_page,
 analysis.get('category', ''),
 analysis.get('product_name', '')
 )

 # ================================================================
 # STEP 4: Create source attribution# ================================================================

 source_attribution = f"📍 المصدر: {source_page}"
 if source_website:
 source_attribution += f"{source_website}"

 # ================================================================
 # STEP 5: Combine all parts# ================================================================

 final_content = f"""{modified_text}

---
{promotional_text}
🔗 {trendyol_match.get('trendyol_link', '')}

{source_attribution}

{hashtags}"""

 # ================================================================
 # STEP 6: Save to database# ================================================================

 await self.database.connection.execute("""
 INSERT OR REPLACE INTO processed_posts
 (post_id, modified_text, promotional_text, hashtags, source_attribution, final_content)
 VALUES (?, ?, ?, ?, ?, ?)
 """, (
 post_id,
 modified_text,
 promotional_text,
 hashtags,
 source_attribution,
 final_content
 ))
 await self.database.connection.commit()

 logger.info(f"✅ Processed successfully: {post_id}")

 return {
 'post_id': post_id,
 'modified_text': modified_text,
 'promotional_text': promotional_text,
 'hashtags': hashtags,
 'source_attribution': source_attribution,
 'final_content': final_content,
 'trendyol_link': trendyol_match.get('trendyol_link', '')
 }

 except Exception as e:
 logger.error(f"❌ Processing failed: {e}")
 await self.database.log_warning(
 "processing_error",
 f"Failed to process post {post_id}: {str(e)}",
 "ContentProcessor"
 )
 return None


# ============================================================================
# STANDALONE PROCESSING FUNCTION# ============================================================================

async def run_processing_cycle(database: Database) -> int:
 """
 Process posts that have been analyzed and matched
 معالجة المنشورات التي تم تحليلها ومطابقتها

 Args:
 database: Database instanceReturns:
 Number of posts processed"""
 processor = ContentProcessor(database)

 # Get posts ready for processingasync with database.connection.execute("""
 SELECT
 cp.post_id, cp.original_text, cp.source_page, cp.source_website,
 ap.product_name, ap.category, ap.keywords,
 tm.trendyol_link, tm.confidence_score
 FROM collected_posts cp
 JOIN analyzed_posts ap ON cp.post_id = ap.post_id
 JOIN trendyol_matches tm ON cp.post_id = tm.post_id
 LEFT JOIN processed_posts pp ON cp.post_id = pp.post_id
 WHERE pp.post_id IS NULL AND ap.is_suitable = 1
 LIMIT 20
 """) as cursor:
 rows = await cursor.fetchall()
 posts = [dict(row) for row in rows]

 if not posts:
 logger.info("ℹ️ No posts to process")
 return 0

 logger.info(f"⚙️ Processing {len(posts)} posts{len(posts)} منشور")

 processed_count = 0

 for post in posts:
 analysis = {
 'product_name': post['product_name'],
 'category': post['category'],
 'keywords': post['keywords']
 }

 trendyol_match = {
 'trendyol_link': post['trendyol_link'],
 'confidence_score': post['confidence_score']
 }

 result = await processor.process_post(
 post['post_id'],
 post['original_text'],
 post['source_page'],
 post['source_website'],
 analysis,
 trendyol_match
 )

 if result:
 processed_count += 1

 logger.info(f"✅ Processing complete: {processed_count}/{len(posts)}")
 return processed_count
