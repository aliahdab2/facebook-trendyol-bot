# Quick Start Guide

## Installation Complete ✅

All dependencies installed successfully!

---

## Next Steps

### 1. Configure Environment

Edit `.env` file:

```bash
nano .env
```

Required settings:

```env
# Facebook API - Get from developers.facebook.com
FACEBOOK_PAGE_ACCESS_TOKEN=your_token_here
FACEBOOK_PAGE_ID=your_page_id
FACEBOOK_GROUP_ID=your_group_id

# OpenAI API - Get from platform.openai.com
OPENAI_API_KEY=your_openai_key_here

# Google Sheets
TRENDYOL_LINKS_SHEET_ID=your_sheet_id_here
```

---

### 2. Setup Google Sheets

**Create sheet with columns:**

| Category | Keywords | Link | Product |
|----------|----------|------|---------|
| Electronics | washer, samsung | https://trendyol.com/... | Samsung Washer |
| Clothing | shirt, cotton | https://trendyol.com/... | Cotton Shirt |

**Setup credentials:**

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create project and enable Google Sheets API
3. Create Service Account credentials
4. Download JSON and save as: `config/google_credentials.json`
5. Share your sheet with service account email

---

### 3. Test Run

```bash
python main.py manual
```

This runs one collection cycle:
1. Collect posts from competitor pages
2. Analyze with GPT-3.5
3. Match Trendyol links
4. Process content
5. Publish to Facebook

---

### 4. Production Run

```bash
python main.py
```

Runs automatically with smart scheduling:
- Every 2 hours (8 AM - 10 PM)
- Best 4-6 posts per day
- Random delays and intervals
- Weekend reduction

---

## Configuration Tips

### Facebook Access Token

Get long-lived token:

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Create app with type "Business"
3. Add Facebook Login product
4. Generate User Access Token with permissions:
   - `pages_read_engagement`
   - `pages_manage_posts`
5. Exchange for long-lived token (60 days):

```bash
curl "https://graph.facebook.com/v18.0/oauth/access_token?\
grant_type=fb_exchange_token&\
client_id=YOUR_APP_ID&\
client_secret=YOUR_APP_SECRET&\
fb_exchange_token=SHORT_LIVED_TOKEN"
```

6. Get Page Access Token:

```bash
curl "https://graph.facebook.com/v18.0/me/accounts?\
access_token=LONG_LIVED_TOKEN"
```

### OpenAI Setup

1. Sign up at [platform.openai.com](https://platform.openai.com)
2. Add credits ($5-10 should last months)
3. Create API key
4. Add to `.env`

Cost: ~$0.002 per post analysis (very cheap!)

### Google Sheets Format

**Important columns:**

- **Category**: Product category (Electronics, Clothing, Home, Food)
- **Keywords**: Comma-separated keywords for matching
- **Link**: Your Trendyol affiliate link
- **Product**: Product description (optional)

**Example:**

```
Category     | Keywords                        | Link                      | Product
-------------|---------------------------------|---------------------------|------------------
Electronics  | washer, samsung, washing        | https://trendyol.com/... | Samsung Washer 9KG
Clothing     | shirt, men, cotton, blue        | https://trendyol.com/... | Men's Cotton Shirt
Home         | sofa, couch, living room, grey  | https://trendyol.com/... | Grey Sofa 3-Seater
```

---

## Monitoring

### View Logs

```bash
# Real-time logs
tail -f logs/bot.log

# Last 100 lines
tail -100 logs/bot.log

# Search for errors
grep ERROR logs/bot.log
```

### Check Database

```bash
# Install SQLite browser
brew install sqlite  # macOS
apt install sqlite3  # Linux

# Open database
sqlite3 data/facebook_bot.db

# View tables
.tables

# Count posts
SELECT COUNT(*) FROM collected_posts;
```

---

## Testing Tips

### Manual Mode

Test individual components:

```bash
# Run one cycle
python main.py manual
```

Check:
- ✅ Posts collected from competitor pages
- ✅ AI analysis working
- ✅ Trendyol links matched
- ✅ Content modified naturally
- ✅ Published to Facebook

### Gradual Rollout

**Week 1-2:** 2-3 posts/day
```python
# In config/settings.py
MAX_POSTS_PER_DAY = 3
```

**Week 3-4:** 4-5 posts/day
```python
MAX_POSTS_PER_DAY = 5
```

**Week 5+:** Full speed (6 posts/day)
```python
MAX_POSTS_PER_DAY = 6
```

---

## Troubleshooting

### "No module named 'config'"

```bash
# Activate venv
source .venv/bin/activate

# Reinstall
pip install -r requirements.txt
```

### "Facebook API error: Invalid token"

```bash
# Check token in .env
cat .env | grep FACEBOOK_PAGE_ACCESS_TOKEN

# Test token
curl "https://graph.facebook.com/v18.0/me?access_token=YOUR_TOKEN"
```

### "OpenAI API error: Insufficient credits"

1. Go to [platform.openai.com/account/billing](https://platform.openai.com/account/billing)
2. Add credits ($5-10)
3. Wait 5-10 minutes for activation

### "Google Sheets: Permission denied"

1. Open `config/google_credentials.json`
2. Find `client_email`
3. Share your Google Sheet with that email
4. Grant "Editor" permissions

---

## Safety Checklist

Before going live:

- [ ] All credentials configured in `.env`
- [ ] Google Sheet shared with service account
- [ ] Tested manual mode successfully
- [ ] Verified posts appear on Facebook
- [ ] Source attribution showing correctly
- [ ] Logs writing to `logs/bot.log`
- [ ] Starting with 2-3 posts/day
- [ ] Backup database configured
- [ ] Monitoring setup ready

---

## Getting Help

**Check logs first:**
```bash
tail -100 logs/bot.log
```

**Common log messages:**

- ✅ "SUCCESS - Database Connection" = Working
- ✅ "Post Activity - Analyzing" = AI working
- ✅ "SUCCESS - Published to Facebook" = Publishing works
- ⚠️ "Rate limit reached" = Too many requests (auto-handled)
- ❌ "FAILED - Invalid token" = Check credentials

---

## Next Steps

Once running smoothly:

1. **Monitor Daily**: Check logs and Facebook page health
2. **Optimize**: Adjust posting times based on engagement
3. **Scale**: Add more Trendyol links to Google Sheet
4. **Backup**: Regular database backups
5. **Maintain**: Keep credentials up to date

---

## Support

For detailed information, see:
- `README.md` - Full documentation
- `.github/copilot-instructions.md` - Development plan (bilingual)
- `config/settings.py` - All configuration options
- `logs/bot.log` - Runtime logs

Good luck! 🚀
