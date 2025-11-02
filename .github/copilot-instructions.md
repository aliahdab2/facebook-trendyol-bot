# Project Instructions - Facebook Trendyol Bot | تعليمات المشروع - بوت فيسبوك تريندول

## Project Overview | نظرة عامة على المشروع

**English:**
Automated affiliate marketing system that monitors competitor store pages (Al Othaim, Al Saif, Safaco, Panda), analyzes posts using AI, slightly modifies content, adds Trendyol affiliate links with source attribution, and publishes to Facebook page/group with smart scheduling and safety layers.

**العربية:**
نظام تسويق بالعمولة آلي يراقب صفحات المتاجر المنافسة (العثيم، السيف، صافكو، بنده)، يحلل المنشورات بالذكاء الاصطناعي، يعدل المحتوى تعديلاً طفيفاً، يضيف روابط تريندول مع ذكر المصدر، وينشر على الصفحة والمجموعة بجدولة ذكية وطبقات حماية.

---

## Key Requirements | المتطلبات الأساسية

- Python 3.10+
- Facebook Graph API integration | تكامل مع Facebook Graph API
- OpenAI GPT-3.5 for content modification | OpenAI GPT-3.5 لتعديل المحتوى
- SQLite async database | قاعدة بيانات SQLite غير متزامنة
- Google Sheets for Trendyol links | Google Sheets لروابط تريندول
- Safety & monitoring layers | طبقات الحماية والمراقبة
- Modular & maintainable code | كود معياري وسهل الصيانة

---

## Improved Development Plan | الخطة التطويرية المحسّنة

### Module 1: Facebook Post Collector | الوحدة 1: جامع المنشورات

**English:**
- Monitor 4 competitor pages every 2 hours (8 AM - 10 PM only)
- Fetch new posts via Graph API with proper rate limiting
- Save post ID, text, images, links, source page, timestamp
- Avoid duplicates using post_id tracking
- Stop completely during night hours

**العربية:**
- مراقبة 4 صفحات منافسة كل ساعتين (8 صباحاً - 10 مساءً فقط)
- جلب المنشورات الجديدة عبر Graph API مع احترام حدود الطلبات
- حفظ معرّف المنشور، النص، الصور، الروابط، المصدر، الوقت
- تجنب التكرار بتتبع معرفات المنشورات
- إيقاف كامل خلال ساعات الليل

---

### Module 2: AI Content Analyzer | الوحدة 2: محلل المحتوى بالذكاء الاصطناعي

**English:**
- Use GPT-3.5 to extract product name, category, keywords
- Determine if post is suitable for publishing (quality check)
- Filter inappropriate or non-product posts
- Extract price and discount information if available
- Select only best 4-6 posts per day

**العربية:**
- استخدام GPT-3.5 لاستخراج اسم المنتج، الفئة، الكلمات المفتاحية
- تحديد إذا كان المنشور مناسب للنشر (فحص جودة)
- فلترة المنشورات غير المناسبة أو التي لا تحتوي منتجات
- استخراج معلومات السعر والتخفيض إن وُجدت
- اختيار أفضل 4-6 منشورات يومياً فقط

---

### Module 3: Trendyol Link Matcher | الوحدة 3: مطابق روابط تريندول

**English:**
- Read Trendyol links from Google Sheets (Category, Keywords, Link columns)
- AI automatically matches post product with appropriate Trendyol link
- Use semantic matching based on keywords and categories
- Log matching confidence score
- Handle cases where no suitable link is found

**العربية:**
- قراءة روابط تريندول من Google Sheets (أعمدة: الفئة، الكلمات المفتاحية، الرابط)
- الذكاء الاصطناعي يطابق المنتج تلقائياً مع رابط تريندول المناسب
- استخدام المطابقة الدلالية بناءً على الكلمات والفئات
- تسجيل درجة ثقة المطابقة
- معالجة الحالات التي لا يوجد فيها رابط مناسب

---

### Module 4: Content Processor | الوحدة 4: معالج المحتوى

**English:**
- GPT-3.5 slightly modifies original text (30-50% rewording)
- Change emoji, rearrange sentences, use synonyms
- Generate unique Trendyol promotional text for each post
- Add source attribution: "Source: Al Othaim | www.othaim.com.sa"
- Generate smart hashtags (store + Trendyol + general)
- Keep images unchanged (only modify metadata)

**العربية:**
- GPT-3.5 يعدل النص الأصلي تعديلاً طفيفاً (30-50% إعادة صياغة)
- تغيير الإيموجي، إعادة ترتيب الجمل، استخدام مرادفات
- توليد نص ترويجي فريد لتريندول لكل منشور
- إضافة مصدر واضح: "المصدر: العثيم | www.othaim.com.sa"
- توليد هاشتاقات ذكية (متجر + تريندول + عامة)
- الصور تبقى كما هي (تعديل metadata فقط)

---

### Module 5: Smart Publisher | الوحدة 5: الناشر الذكي

**English:**
- Wait random delay (30-120 minutes) after original post
- Post to Facebook page and group via Graph API
- Add random intervals between posts (2-5 hours)
- Respect Facebook rate limits and API quotas
- Log all publishing actions with timestamps

**العربية:**
- انتظار تأخير عشوائي (30-120 دقيقة) بعد المنشور الأصلي
- النشر على الصفحة والمجموعة عبر Graph API
- إضافة فواصل عشوائية بين المنشورات (2-5 ساعات)
- احترام حدود فيسبوك وحصص الـ API
- تسجيل كل إجراءات النشر مع الطوابع الزمنية

---

### Module 6: Safety & Protection | الوحدة 6: الأمان والحماية

**English:**
- Use rotating proxies for API calls (optional)
- Vary user agents and request headers
- Implement exponential backoff on errors
- Track Facebook warnings and rate limits
- Auto-stop on suspicious activity detection

**العربية:**
- استخدام بروكسيات متناوبة لطلبات الـ API (اختياري)
- تنويع user agents ورؤوس الطلبات
- تطبيق تأخير تصاعدي عند الأخطاء
- تتبع تحذيرات فيسبوك وحدود الطلبات
- إيقاف تلقائي عند اكتشاف نشاط مريب

---

### Module 7: Monitoring & Alerts | الوحدة 7: المراقبة والإنذارات

**English:**
- Real-time monitoring of Facebook API responses
- Detect warnings, restrictions, or errors
- Daily reports (posts collected, published, failed)
- Alert system for critical issues
- Performance metrics tracking

**العربية:**
- مراقبة فورية لاستجابات Facebook API
- كشف التحذيرات، القيود، أو الأخطاء
- تقارير يومية (منشورات مجمعة، منشورة، فاشلة)
- نظام إنذار للمشاكل الحرجة
- تتبع مقاييس الأداء

---

## System Architecture | معمارية النظام

```
src/
├── database.py          # قاعدة البيانات | Database layer
├── facebook_collector.py # جامع المنشورات | Post collector
├── content_analyzer.py   # محلل المحتوى | Content analyzer
├── trendyol_matcher.py   # مطابق الروابط | Link matcher
├── content_processor.py  # معالج المحتوى | Content processor
├── publisher.py          # الناشر | Publisher
└── scheduler.py          # المجدول | Scheduler

utils/
├── logger.py            # السجلات | Logger
├── safety.py            # الأمان | Safety utilities
└── monitor.py           # المراقبة | Monitoring

config/
└── settings.py          # الإعدادات | Configuration

main.py                  # التطبيق الرئيسي | Main application
```

---

## Safety Notes | ملاحظات الأمان

**English:**
- Risk Level: Low to Medium (3.5/10)
- Expected Lifespan: 6-12 months with proper precautions
- Always mention source to avoid copyright issues
- Start slow (2-3 posts/day for first 2 weeks)
- Prepare backup account in advance

**العربية:**
- مستوى المخاطر: منخفض إلى متوسط (3.5/10)
- العمر المتوقع: 6-12 شهر مع الاحتياطات المناسبة
- دائماً اذكر المصدر لتجنب مشاكل حقوق النشر
- ابدأ ببطء (2-3 منشورات/يوم لأول أسبوعين)
- جهّز حساب احتياطي مسبقاً
