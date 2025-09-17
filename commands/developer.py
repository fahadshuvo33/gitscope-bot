from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from templates import get_developer_info, get_error_message

logger = logging.getLogger(__name__)


async def developer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /developer command"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Back to Start", callback_data="start")]
    ])

    try:
        developer_text = get_developer_info()
        
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
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
        
        if update.callback_query:
            await update.callback_query.message.edit_text(error_text, reply_markup=keyboard)
        else:
            await update.message.reply_text(error_text, reply_markup=keyboard)
