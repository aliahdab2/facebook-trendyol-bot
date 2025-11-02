"""
Logging Utility
Centralized logging configuration with colored console output and rotating file handler
"""

import logging
import colorlog
from logging.handlers import RotatingFileHandler
from pathlib import Path
from config import settings

def setup_logger(name: str = "FacebookTrendyolBot") -> logging.Logger:
    """Setup logging - both to console (with colors) and file"""
    # Using colorlog for nice colored output in terminal
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Ensure log directory exists
    log_file = Path(settings.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # ========================================================================
    # CONSOLE HANDLER (with colors)
    # ========================================================================
    
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # ========================================================================
    # FILE HANDLER (rotating)
    # ========================================================================
    
    file_handler = RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding='utf-8'  # Support for UTF-8 characters
    )
    file_handler.setLevel(logging.DEBUG)
    
    file_formatter = logging.Formatter(
        settings.LOG_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger


# ============================================================================
# GLOBAL LOGGER INSTANCE
# ============================================================================

logger = setup_logger()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def log_operation(operation: str, success: bool, details: str = ""):
    """
    Log an operation with consistent format
    
    Args:
        operation: Operation name
        success: Whether operation succeeded
        details: Additional details
    """
    
    status = "✅ SUCCESS" if success else "❌ FAILED"
    message = f"{status} - {operation}"
    
    if details:
        message += f" - {details}"
    
    if success:
        logger.info(message)
    else:
        logger.error(message)


def log_api_call(api_name: str, endpoint: str, status_code: int = None, duration: float = None):
    """
    Log API call with details
    
    Args:
        api_name: API name (Facebook, OpenAI, etc.)
        endpoint: API endpoint
        status_code: HTTP status code
        duration: Call duration in seconds
    """
    
    message = f"📡 API Call - {api_name} - {endpoint}"
    
    if status_code:
        message += f" - Status: {status_code}"
    
    if duration:
        message += f" - Duration: {duration:.2f}s"
    
    logger.debug(message)


def log_post_activity(activity: str, post_id: str = None, source: str = None):
    """
    Log post-related activity
    
    Args:
        activity: Activity description
        post_id: Post ID
        source: Source page
    """
    
    message = f"📝 Post Activity - {activity}"
    
    if post_id:
        message += f" - ID: {post_id}"
    
    if source:
        message += f" - Source: {source}"
    
    logger.info(message)


def log_warning_alert(warning_type: str, message: str):
    """
    Log warning that requires attention
    
    Args:
        warning_type: Type of warning
        message: Warning message
    """
    
    logger.warning(f"⚠️ ALERT - {warning_type} - {message}")


def log_daily_summary(collected: int, analyzed: int, published: int, failed: int):
    """
    Log daily summary report
    
    Args:
        collected: Posts collected
        analyzed: Posts analyzed
        published: Posts published
        failed: Posts failed
    """
    
    logger.info("=" * 80)
    logger.info("📊 DAILY SUMMARY")
    logger.info(f"   Collected: {collected}")
    logger.info(f"   Analyzed: {analyzed}")
    logger.info(f"   Published: {published}")
    logger.info(f"   Failed: {failed}")
    logger.info(f"   Success Rate: {(published / max(analyzed, 1)) * 100:.1f}%")
    logger.info("=" * 80)
