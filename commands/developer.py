# developer.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from templates import get_developer_info, get_error_message
from utils.loading import with_loading

logger = logging.getLogger(__name__)

@with_loading
async def developer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /developer command"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Back to Start", callback_data="start")]
    ])

    try:
        developer_text = get_developer_info()
        
        # Use the loading message from context
        message = context.user_data.get('_loading_message')
        if message:
            await message.edit_text(
                developer_text,
                parse_mode="MarkdownV2",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
        else:
            # Fallback
            if update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.message.edit_text(
                    developer_text,
                    parse_mode="MarkdownV2",
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )
            else:
                await update.message.reply_text(
                    developer_text,
                    parse_mode="MarkdownV2",
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )
    except Exception as e:
        logger.error(f"Error in developer command: {e}")
        error_text = get_error_message("Developer", str(e))
        
        message = context.user_data.get('_loading_message')
        if message:
            await message.edit_text(
                error_text,
                parse_mode="MarkdownV2",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )