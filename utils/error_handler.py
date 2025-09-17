from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import NetworkError, TimedOut, BadRequest, Forbidden
import logging
import aiohttp
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class GitHubErrorHandler:
    """Minimal GitHub error handler"""
    
    def get_error_message(self, error_type, context="operation"):
        """Get simple error message"""
        messages = {
            "not_found": f"❌ {context.title()} not found",
            "rate_limit": "⏳ Rate limit exceeded\\. Please try again later",
            "network": "🌐 Network error\\. Please try again",
            "timeout": "⏰ Request timed out\\. Please try again",
            "forbidden": "🚫 Access denied",
            "server_error": "🔧 Server error\\. Please try again later",
            "profile_error": "❌ Unable to load profile\\. Please check the username and try again",
            "parse_error": "❌ Unable to process the request\\. Please try again"
        }
        return messages.get(error_type, f"❌ Error in {context}")
    
    async def handle_error(self, message, error, context="operation"):
        """Handle error with simple message"""
        # Classify error and get appropriate message
        error_type = self.classify_error(error)
        
        # Special handling for profile errors
        if "profile" in context.lower():
            error_type = "profile_error"
        elif "parse" in str(error).lower() or "markdown" in str(error).lower():
            error_type = "parse_error"
            
        error_msg = self.get_error_message(error_type, context)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Retry", callback_data=f"retry_{context}")],
            [InlineKeyboardButton("🏠 Back to Start", callback_data="start")]
        ])
        
        try:
            await message.edit_text(error_msg, reply_markup=keyboard, parse_mode="MarkdownV2")
        except:
            # Fallback without markdown
            try:
                await message.edit_text(error_msg.replace("\\", ""), reply_markup=keyboard)
            except:
                pass
    
    def classify_error(self, error):
        """Classify error type"""
        if isinstance(error, (NetworkError, aiohttp.ClientError)):
            return "network"
        elif isinstance(error, TimedOut):
            return "timeout"
        elif isinstance(error, Forbidden):
            return "forbidden"
        elif isinstance(error, BadRequest):
            return "bad_request"
        else:
            return "server_error"
