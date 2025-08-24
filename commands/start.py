import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

# Import the loading system
from utils.loading import show_loading, show_static_loading

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with loading animation"""
    user = update.effective_user
    user_name = escape_markdown(user.first_name or "there", 2)
    
    # Determine if this is from a callback or direct message
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
    else:
        # For direct command, create initial message
        message = await update.message.reply_text(
            "🚀 **GitHub Explorer Bot**\n\n💡 **Tip:** Initializing...",
            parse_mode="Markdown"
        )
    
    # Show static loading first
    try:
        await show_static_loading(
            message,
            "🚀 **GitHub Explorer Bot**",
            "Initializing bot",
            preserve_content=True,
            animation_type="rocket",  # Rocket animation for start
        )
    except Exception as e:
        logger.debug(f"Static loading skipped: {e}")
    
    # Start animated loading
    loading_task = await show_loading(
        message,
        "🚀 **GitHub Explorer Bot**",
        "Preparing your experience",
        animation_type="rocket",
        preserve_content=True,
    )
    
    # Brief wait for effect
    await asyncio.sleep(1.0)
    
    # Stop loading animation gracefully
    if loading_task and not loading_task.done():
        loading_task.cancel()
        try:
            await loading_task
        except asyncio.CancelledError:
            pass
    
    # Prepare welcome text
    welcome_text = (
        f"👋 *Hello {user_name}\\!*\n\n"
        f"🚀 Welcome to **GitHub Explorer Bot**\n"
        f"_Your ultimate GitHub companion_\n\n"

        "🔥 *What I can do:*\n"
        "• 📊 View repository details\n"
        "• 👤 Show user profiles\n"
        "• 📈 Display trending repositories\n"
        "• 💻 Browse by programming language\n"
        "• 🔍 Search GitHub content\n\n"

        "⚡ *Quick Commands:*\n"
        "• `/help` \\- Get detailed help\n"
        "• `/trending` \\- See trending repos\n"
        "• `/user username` \\- View user profile\n\n"

        "💡 *Quick Start:*\n"
        "Just send me a repository name like `facebook/react` or a GitHub URL\\!"
    )

    keyboard = [
        [
            InlineKeyboardButton("📖 Help", callback_data="help"),
            InlineKeyboardButton("📈 Trending", callback_data="trending")
        ],
        [
            InlineKeyboardButton("ℹ️ About", callback_data="about")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Show the welcome message
    try:
        await message.edit_text(
            welcome_text,
            parse_mode="MarkdownV2",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Error showing start message: {e}")
        # Fallback if edit fails
        try:
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    welcome_text,
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
                    welcome_text,
                    parse_mode="MarkdownV2",
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
        except Exception as fallback_error:
            logger.error(f"Fallback error in start command: {fallback_error}")
            # Last resort - simple message
            simple_text = f"👋 Hello {user.first_name or 'there'}!\n\nWelcome to GitHub Explorer Bot!\n\nUse /help to get started."
            if update.callback_query:
                await update.callback_query.edit_message_text(simple_text)
            else:
                await update.message.reply_text(simple_text)

    # Clear any existing data
    context.user_data.clear()
    
    # Log successful start
    logger.info(f"User {user.id} ({user.username or 'No username'}) started the bot")


# Add handler for "Back to Start" callback
async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to start button"""
    if update.callback_query:
        # Reuse the start command
        await start_command(update, context)