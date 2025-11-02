"""
Configuration Settings
All configurable parameters in one place for easy modification
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# FACEBOOK API CONFIGURATION
# ============================================================================

FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
FACEBOOK_GROUP_ID = os.getenv("FACEBOOK_GROUP_ID")
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")

# Source pages to monitor
SOURCE_PAGES = [
    {"name": "Al Othaim", "id": "Othaim.Market", "website": "www.othaim.com.sa"},
    {"name": "Al Saif", "id": "alsaifgallery", "website": "www.alsaifgallery.com"},
    {"name": "Safaco", "id": "safacoltd1", "website": "www.safaco.com"},
    {"name": "Panda", "id": "PandaSaudi", "website": "www.panda.com.sa"},
]

# ============================================================================
# OPENAI API CONFIGURATION
# ============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# ============================================================================
# GOOGLE SHEETS CONFIGURATION
# ============================================================================

GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv(
    "GOOGLE_SHEETS_CREDENTIALS_FILE",
    "config/google_credentials.json"
)
TRENDYOL_LINKS_SHEET_ID = os.getenv("TRENDYOL_LINKS_SHEET_ID")

# ============================================================================
# COLLECTION SCHEDULE
# ============================================================================

# Check pages every N hours
COLLECTION_INTERVAL_HOURS = 2

# Operating hours (24-hour format)
COLLECTION_START_HOUR = 8   # 8 AM
COLLECTION_END_HOUR = 22    # 10 PM

# ============================================================================
# POSTING CONFIGURATION
# ============================================================================

# Maximum posts per day
MAX_POSTS_PER_DAY = 6
MIN_POSTS_PER_DAY = 4

# Delay after original post (minutes)
MIN_DELAY_AFTER_ORIGINAL = 30
MAX_DELAY_AFTER_ORIGINAL = 120

# Interval between our posts (hours)
MIN_POSTING_INTERVAL_HOURS = 2
MAX_POSTING_INTERVAL_HOURS = 5

# Reduce posting on weekends (0.5 = 50% fewer posts)
WEEKEND_POST_REDUCTION = 0.5

# ============================================================================
# CONTENT MODIFICATION
# ============================================================================

# Text modification percentage (30-50% of original text)
MIN_MODIFICATION_PERCENT = 30
MAX_MODIFICATION_PERCENT = 50

# Hashtag count per post
MIN_HASHTAGS = 5
MAX_HASHTAGS = 7

# ============================================================================
# SAFETY & RATE LIMITING
# ============================================================================

# Facebook API rate limits
MAX_API_CALLS_PER_HOUR = 200
MAX_POSTS_PER_HOUR = 5

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
EXPONENTIAL_BACKOFF = True

# Auto-stop on warnings
AUTO_STOP_ON_WARNING = True
MAX_WARNINGS_ALLOWED = 3

# ============================================================================
# DATABASE
# ============================================================================

DATABASE_PATH = os.getenv("DATABASE_PATH", "data/facebook_bot.db")

# ============================================================================
# LOGGING
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/bot.log")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# ============================================================================
# MONITORING & ALERTS
# ============================================================================

# Daily report time (24-hour format)
DAILY_REPORT_HOUR = 23  # 11 PM

# Alert thresholds
ALERT_ON_ERROR_COUNT = 5  # Alert if 5+ errors in an hour
ALERT_ON_LOW_SUCCESS_RATE = 0.7  # Alert if success rate < 70%

# ============================================================================
# PROXY CONFIGURATION (OPTIONAL)
# ============================================================================

USE_PROXY = os.getenv("USE_PROXY", "false").lower() == "true"
PROXY_LIST = os.getenv("PROXY_LIST", "").split(",") if os.getenv("PROXY_LIST") else []

# ============================================================================
# USER AGENTS | User Agents
# ============================================================================

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
]

# ============================================================================
# FEATURE FLAGS
# ============================================================================

ENABLE_IMAGE_METADATA_MODIFICATION = True
ENABLE_SOURCE_ATTRIBUTION = True
ENABLE_TRENDYOL_LINKS = True
ENABLE_MONITORING = True
ENABLE_DAILY_REPORTS = True

# ============================================================================
# VALIDATION
# ============================================================================

def validate():
    """Validate that all required settings are configured"""
    required_settings = [
        ("FACEBOOK_PAGE_ACCESS_TOKEN", FACEBOOK_PAGE_ACCESS_TOKEN),
        ("FACEBOOK_PAGE_ID", FACEBOOK_PAGE_ID),
        ("OPENAI_API_KEY", OPENAI_API_KEY),
        ("TRENDYOL_LINKS_SHEET_ID", TRENDYOL_LINKS_SHEET_ID),
    ]
    
    missing = [name for name, value in required_settings if not value]
    
    if missing:
        raise ValueError(
            f"Missing required settings: {', '.join(missing)}\n"
            f"Please check your .env file"
        )
    
    return True
