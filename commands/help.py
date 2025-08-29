import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Import the loading animation functions
from utils.loading import show_loading, show_static_loading

logger = logging.getLogger(__name__)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command with loading animation"""

    # Determine if this is from a callback or direct message
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
    else:
        # For direct command, create initial message
        message = await update.message.reply_text(
            "📖 *GitScope Bot Help*\n\n💡 **Tip:** Loading help information...",
            parse_mode="Markdown",
        )

    # Only show loading if not already showing help content
    if message and not ("🎯 *Commands:*" in message.text):
        # Show static loading first to preserve the window
        try:
            await show_static_loading(
                message,
                "📖 **GitScope Bot Help**",
                "Loading help information",
                preserve_content=True,
                animation_type="stars",  # Stars animation for help
            )
        except Exception as e:
            logger.debug(f"Static loading skipped: {e}")

        # Start animated loading (without duration parameter)
        loading_task = await show_loading(
            message,
            "📖 **GitScope Bot Help**",
            "Loading help information",
            animation_type="stars",
            preserve_content=True,
        )

        # Wait a bit for animation effect
        await asyncio.sleep(1.5)

        # Stop loading animation gracefully
        if loading_task and not loading_task.done():
            loading_task.cancel()
            try:
                await loading_task
            except asyncio.CancelledError:
                pass

    # Prepare the help text (with properly escaped characters)
    help_text = (
        "📖 *GitScope Bot Help*\n\n"
        "🎯 *Commands:*\n"
        "• `/start` \\- Show welcome message\n"
        "• `/help` \\- Show this help\n"
        "• `/trending` \\- View trending repositories\n"
        "• `/user <username>` \\- View GitHub user profile\n\n"
        "🔍 *Quick Search:*\n"
        "Send me any of these formats:\n"
        "• `facebook/react` \\- Repository name\n"
        "• `https://github.com/microsoft/vscode` \\- Full URL\n"
        "• `@octocat` \\- User profile with @\n"
        "• `octocat` \\- Only GitHub username\n\n"
        "📊 *Repository Features:*\n"
        "• View statistics & info\n"
        "• Browse contributors\n"
        "• Check open issues & PRs\n"
        "• See programming languages\n"
        "• View latest releases\n"
        "• Read README preview\n\n"
        "👤 *User Profile Features:*\n"
        "• View user information\n"
        "• Browse user repositories\n"
        "• See contribution stats\n"
        "• Check followers/following\n\n"
        "📈 *Trending Features:*\n"
        "• Filter by programming language\n"
        "• View daily/weekly/monthly trends\n"
        "• Discover new repositories\n\n"
        "💡 *Tips:*\n"
        "• All data is fetched in real\\-time\n"
        "• Only public repositories are supported\n"
        "• Use buttons for easy navigation\n\n"
        "Need help\\? Just ask\\! 😊"
    )

    # Show the help content
    try:
        if update.callback_query:
            keyboard = [
                [InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await message.edit_text(
                help_text,
                parse_mode="MarkdownV2",
                reply_markup=reply_markup,
                disable_web_page_preview=True,
            )
        else:
            # For direct command, just edit the message
            await message.edit_text(
                help_text, parse_mode="MarkdownV2", disable_web_page_preview=True
            )
    except Exception as e:
        logger.error(f"Error showing help content: {e}")
        # Fallback if there's an error
        error_text = "❌ Error displaying help\\. Please try again\\."

        try:
            if update.callback_query:
                keyboard = [
                    [InlineKeyboardButton("🔄 Try Again", callback_data="help")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await message.edit_text(
                    error_text, parse_mode="MarkdownV2", reply_markup=reply_markup
                )
            else:
                await message.edit_text(error_text, parse_mode="MarkdownV2")
        except Exception as fallback_error:
            logger.error(f"Fallback error: {fallback_error}")
