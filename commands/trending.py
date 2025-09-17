import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

# Import the loading system
# from utils.loading import withLoading
from utils.db_logger import log_activity

# Set up logger
logger = logging.getLogger(__name__)


# @withLoading(style='fire', duration=1.0)
async def trending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /trending command with loading animation"""
    
    user = update.effective_user
    user_id = user.username or f"user_{user.id}"
    log_activity("INFO", "Trending menu accessed", user_id=user_id, command="trending")
    
    # Determine if this is from a callback or direct message
    if update.callback_query:
        query = update.callback_query
        message = query.message
    else:
        # For direct command, create initial message
        message = await update.message.reply_text(
            "📈 **Trending Repositories**\n\n💡 **Tip:** Loading trending options...",
            parse_mode="Markdown"
        )

    # Language selection keyboard
    languages = [
        ("🐍 Python", "python"),
        ("☕ JavaScript", "javascript"),
        ("⚡ TypeScript", "typescript"),
        ("☕ Java", "java"),
        ("🔧 C++", "cpp"),
        ("🐹 Go", "go"),
        ("🦀 Rust", "rust"),
        ("💎 Ruby", "ruby"),
        ("🐘 PHP", "php"),
        ("🍎 Swift", "swift"),
        ("🟣 Kotlin", "kotlin"),
        ("All Languages", "all"),
    ]

    keyboard = []
    for i in range(0, len(languages), 2):
        row = []
        for j in range(2):
            if i + j < len(languages):
                lang_name, lang_code = languages[i + j]
                row.append(
                    InlineKeyboardButton(
                        lang_name, callback_data=f"trending_lang_{lang_code}"
                    )
                )
        keyboard.append(row)

    # Add back button if it's a callback
    if update.callback_query:
        keyboard.append(
            [InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)

    trending_text = (
        "📈 *Trending Repositories*\n\n"
        "🔥 Discover the hottest repositories on GitHub\\!\n\n"
        "Choose a programming language to see trending repositories:\n\n"
        "💡 *Tip:* These are the most starred repositories from the past week\\."
    )

    try:
        await message.edit_text(
            trending_text, 
            parse_mode="MarkdownV2", 
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Error showing trending menu: {e}")
        # Fallback if edit fails
        try:
            if update.callback_query:
                await query.edit_message_text(
                    trending_text, 
                    parse_mode="MarkdownV2", 
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
            else:
                # Delete the loading message and send new one
                try:
                    await message.delete()
                except:
                    pass
                await update.message.reply_text(
                    trending_text, 
                    parse_mode="MarkdownV2", 
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
        except Exception as fallback_error:
            logger.error(f"Fallback error in trending command: {fallback_error}")
            # Last resort - simple message
            simple_text = "📈 Trending Repositories\n\nPlease select a programming language to see trending repos."
            
            # Create simple keyboard
            simple_keyboard = [[InlineKeyboardButton("🐍 Python", callback_data="trending_python"),
                              InlineKeyboardButton("☕ JavaScript", callback_data="trending_javascript")]]
            simple_markup = InlineKeyboardMarkup(simple_keyboard)
            
            if update.callback_query:
                await query.edit_message_text(simple_text, reply_markup=simple_markup)
            else:
                await update.message.reply_text(simple_text, reply_markup=simple_markup)
    
    # Log trending command usage
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username or 'No username'}) accessed trending menu")