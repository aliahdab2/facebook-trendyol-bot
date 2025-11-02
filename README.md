# Facebook Trendyol Bot

Automated affiliate marketing system that monitors competitor store pages, analyzes posts using AI, modifies content slightly, adds Trendyol affiliate links with source attribution, and publishes to Facebook page/group with smart scheduling and safety layers.

---

## Features

- ✅ **Automated Collection**: Monitors 4 competitor pages every 2 hours (8 AM - 10 PM)
- 🤖 **AI-Powered Analysis**: GPT-3.5 analyzes posts and extracts product information
- 🔗 **Smart Matching**: Automatically matches products with appropriate Trendyol links
- ✍️ **Content Modification**: Slight text modifications (30-50%) to avoid detection
- 📱 **Dual Publishing**: Posts to both Facebook page and group
- ⏰ **Smart Scheduling**: Random delays and natural posting patterns
- 🛡️ **Safety Layers**: Rate limiting, error handling, and monitoring
- 📊 **Daily Reports**: Comprehensive statistics and warnings

---

## Requirements

- Python 3.10+
- Facebook Developer Account (Page Access Token)
- OpenAI API Key (GPT-3.5)
- Google Sheets API Credentials
- Trendyol Affiliate Partnership

---

## Quick Start

### 1. Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your credentials:

```bash
cp .env.example .env
```

Required settings:
- Facebook Page Access Token, Page ID, Group ID
- OpenAI API Key
- Google Sheets ID and credentials

### 3. Setup Google Sheets

Create a sheet with columns: `Category`, `Keywords`, `Link`, `Product`

Save service account credentials as `config/google_credentials.json`

### 4. Run

**Test mode:**
```bash
python main.py manual
```

**Production mode:**
```bash
python main.py
```

---

## Configuration

All settings in `config/settings.py`:

**Collection:**
- Check pages every 2 hours (8 AM - 10 PM)
- Operating hours prevent night-time activity

**Posting:**
- Max 4-6 posts per day
- Random delay 30-120 min after original post
- 2-5 hours between our posts
- 50% fewer posts on weekends

**Safety:**
- Max 200 API calls/hour
- Max 5 posts/hour
- Auto-stop on warnings (3 max)

---

## Architecture

```
src/
├── database.py           # Async SQLite database
├── facebook_collector.py # Fetch competitor posts
├── content_analyzer.py   # GPT-3.5 analysis
├── trendyol_matcher.py   # Match affiliate links
├── content_processor.py  # Modify content
├── publisher.py          # Publish to Facebook
└── scheduler.py          # Orchestration

utils/
└── logger.py            # Colored logging

config/
├── settings.py          # Configuration
└── google_credentials.json

main.py                  # Entry point
```

---

## Database

SQLite database with 7 tables:
- `collected_posts` - Raw posts from competitors
- `analyzed_posts` - AI analysis results
- `trendyol_matches` - Matched links
- `processed_posts` - Modified content
- `published_posts` - Published records
- `system_logs` - Operation logs
- `warnings` - API warnings

---

## Safety Features

### Rate Limiting
- Facebook API: 200 calls/hour
- Posts: Max 5/hour, 6/day
- Automatic retry with exponential backoff

### Randomization
- Variable delays (30-120 min)
- Variable intervals (2-5 hours)
- Variable modification (30-50%)

### Monitoring
- Real-time API response tracking
- Warning detection
- Daily summary reports
- Auto-stop on suspicious activity

### Source Attribution
Every post includes:
```
Source: [Store Name] | [Website]
```

Prevents copyright issues and maintains transparency.

---

## Monitoring

**View logs:**
```bash
tail -f logs/bot.log
```

**Daily reports:**
- Generated automatically at 11 PM
- Includes: collected, analyzed, published, failed, success rate

---

## Troubleshooting

**Facebook API Errors:**
- Rate limit: Auto-waits 1 hour
- Invalid token: Regenerate and update `.env`
- Permission denied: Check token permissions

**OpenAI Errors:**
- Insufficient credits: Add credits at platform.openai.com
- Rate limit: Reduce posting frequency

**Google Sheets:**
- Permission denied: Share sheet with service account
- Not found: Verify sheet ID in `.env`

---

## Best Practices

### Starting
1. Test manual mode first
2. Start with 2-3 posts/day
3. Monitor closely for 2 weeks
4. Gradually increase to 4-6/day

### Content
- Always attribute source
- Use quality images
- Verify link validity
- Check modifications are natural

### Safety
- Don't exceed limits
- Monitor warnings
- Keep database backups
- Have backup page ready

---

## Risk Assessment

**Level:** Low-Medium (3.5/10)  
**Expected Lifespan:** 6-12 months with precautions

**Mitigation:**
- Source attribution (copyright)
- Rate limiting (API bans)
- Content modification (duplicates)
- Random delays (human-like)
- Weekend reduction (natural)

---

## License

MIT License

---

## Disclaimer

Designed for legitimate affiliate marketing as official Trendyol partner. Always:
- Respect Facebook TOS
- Attribute sources clearly
- Comply with affiliate rules
- Monitor warnings promptly

Use responsibly at your own risk.
