# about.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
import asyncio
from templates import get_about_info, get_error_message
from utils.loading import with_loading, update_with_animation

logger = logging.getLogger(__name__)

# Method 1: Using the simplified decorator
@with_loading  # Animation runs for 1.5 seconds, then your function runs
async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /about command"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Back to Start", callback_data="start")]
    ])

    try:
        # Get the about information
        about_text = get_about_info()
        
        # Get the loading message from context
        message = context.user_data.get('_loading_message')
        
        if message:
            # The animation has already stopped, just update
            await message.edit_text(
                about_text,
                parse_mode="MarkdownV2",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )

    except Exception as e:
        logger.error(f"Error in about command: {e}", exc_info=True)
        
        message = context.user_data.get('_loading_message')
        if message:
            error_text = get_error_message("About", str(e))
            await message.edit_text(
                error_text,
                parse_mode="MarkdownV2",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )


# Method 2: Using update_with_animation (more control)
# async def about_command_alternative(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Alternative without decorator"""
#     keyboard = InlineKeyboardMarkup([
#         [InlineKeyboardButton("🏠 Back to Start", callback_data="start")]
#     ])
    
#     # Get or create message
#     if update.callback_query:
#         await update.callback_query.answer()
#         message = update.callback_query.message
#     else:
#         message = await update.message.reply_text(".")
    
#     # Get about text
#     about_text = get_about_info()
    
#     # Show animation then update
#     await update_with_animation(
#         message=message,
#         final_text=about_text,
#         loading_text="Loading about information",
#         keyboard=keyboard,
#         animation_duration=2.0
#     )