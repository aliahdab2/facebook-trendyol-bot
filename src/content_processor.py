"""
Content Processor - Modifies content 30-50% and generates promotional text
"""

import json
from typing import Dict, List, Optional
from openai import OpenAI
from config import settings
from utils.logger import logger


class ContentProcessor:
    """Processes and modifies post content using AI"""

    def __init__(self):
        """Initialize content processor"""
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-3.5-turbo"

    def _create_modification_prompt(self, original_text: str, product_name: str) -> str:
        """Create prompt for content modification"""
        prompt = f"""أنت خبير في إعادة صياغة المحتوى التسويقي.

النص الأصلي:
{original_text}

المنتج: {product_name}

قم بإعادة كتابة النص بحيث:
1. تغيير 30-50% من الكلمات باستخدام مرادفات
2. إعادة ترتيب الجمل
3. تغيير الإيموجي المستخدمة
4. الحفاظ على المعنى الأساسي
5. النص يجب أن يبدو طبيعياً ومختلفاً عن الأصل

أرجع النص المعدل فقط بدون أي تعليقات."""

        return prompt

    def _create_promotional_prompt(self, product_name: str, category: str) -> str:
        """Create prompt for Trendyol promotional text"""
        prompt = f"""أنشئ نصاً ترويجياً قصيراً (2-3 جمل) لمنتج "{product_name}" من فئة "{category}".

النص يجب أن:
1. يكون جذاباً ومختصراً
2. يشجع على الشراء من تريندول
3. يذكر ميزة أو اثنتين للمنتج
4. يحتوي على دعوة لاتخاذ إجراء
5. يستخدم إيموجي مناسبة

مثال: "🛍️ اطلب الآن من تريندول واحصل على أفضل الأسعار! توصيل سريع وضمان الجودة ✨"

أرجع النص الترويجي فقط بدون تعليقات."""

        return prompt

    def _generate_hashtags(self, product_name: str, category: str, source_page: str) -> List[str]:
        """Generate relevant hashtags"""
        hashtags = []

        # Source page hashtag
        store_hashtags = {
            "Al Othaim": ["#العثيم", "#AlOthaimMarkets"],
            "Al Saif": ["#السيف_غاليري", "#AlSaifGallery"],
            "Safaco": ["#صافكو", "#Safaco"],
            "Panda": ["#بنده", "#PandaStores"]
        }
        hashtags.extend(store_hashtags.get(source_page, []))

        # Trendyol hashtags
        hashtags.extend(["#تريندول", "#Trendyol", "#تسوق_اونلاين"])

        # Category hashtags
        category_hashtags = {
            "Electronics": ["#الكترونيات", "#Electronics"],
            "Fashion": ["#موضة", "#Fashion"],
            "Home": ["#منزل", "#HomeDecor"],
            "Beauty": ["#تجميل", "#Beauty"],
            "Kitchen": ["#مطبخ", "#Kitchen"],
            "Sports": ["#رياضة", "#Sports"]
        }
        hashtags.extend(category_hashtags.get(category, []))

        # Generic shopping hashtags
        hashtags.extend(["#عروض", "#تخفيضات", "#تسوق"])

        return hashtags[:12]  # Maximum 12 hashtags

    async def modify_content(self, original_text: str, product_name: str) -> Optional[str]:
        """Modify original content 30-50%"""
        try:
            prompt = self._create_modification_prompt(original_text, product_name)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert content writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            modified_text = response.choices[0].message.content.strip()
            logger.info(f"✅ Content modified for: {product_name}")
            return modified_text

        except Exception as e:
            logger.error(f"❌ Content modification failed: {e}")
            return None

    async def generate_promotional_text(self, product_name: str, category: str) -> Optional[str]:
        """Generate Trendyol promotional text"""
        try:
            prompt = self._create_promotional_prompt(product_name, category)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a marketing expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=200
            )

            promo_text = response.choices[0].message.content.strip()
            logger.info(f"✅ Promotional text generated for: {product_name}")
            return promo_text

        except Exception as e:
            logger.error(f"❌ Promotional text generation failed: {e}")
            return None

    async def process_post(
        self,
        post_data: Dict,
        analysis: Dict,
        trendyol_link: str,
        source_attribution: str
    ) -> Optional[Dict]:
        """Process complete post with all modifications"""
        try:
            product_name = analysis.get('product_name', 'Product')
            category = analysis.get('category', 'General')

            # Modify original content
            modified_text = await self.modify_content(post_data['text'], product_name)
            if not modified_text:
                return None

            # Generate promotional text
            promo_text = await self.generate_promotional_text(product_name, category)
            if not promo_text:
                return None

            # Generate hashtags
            hashtags = self._generate_hashtags(product_name, category, post_data['source_page'])

            # Combine everything
            final_text = f"""{modified_text}

━━━━━━━━━━━━━━━━

{promo_text}

🔗 رابط المنتج في تريندول:
{trendyol_link}

━━━━━━━━━━━━━━━━

📌 {source_attribution}

{' '.join(hashtags)}"""

            processed_data = {
                'post_id': post_data['post_id'],
                'modified_text': modified_text,
                'promotional_text': promo_text,
                'hashtags': hashtags,
                'final_text': final_text,
                'trendyol_link': trendyol_link,
                'source_attribution': source_attribution,
                'images': post_data.get('images', [])
            }

            logger.info(f"✅ Post processed: {post_data['post_id']}")
            return processed_data

        except Exception as e:
            logger.error(f"❌ Post processing failed: {e}")
            return None


async def process_single_post(
    post_data: Dict,
    analysis: Dict,
    trendyol_link: str,
    source_attribution: str
) -> Optional[Dict]:
    """Process a single post"""
    processor = ContentProcessor()
    return await processor.process_post(post_data, analysis, trendyol_link, source_attribution)
