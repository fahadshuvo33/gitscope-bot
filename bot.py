import asyncio
import logging
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode
from dotenv import load_dotenv
import os

# Import the main router and handlers
from commands import command_router
from features.repository import repository_handler
from features.trending_repos import trending_handler
# Import README handlers for pagination
from handlers.readme import handle_readme_navigation, handle_readme_pages
import aiohttp

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")


# Configure clean logging
def setup_logging():
    """Setup clean logging configuration"""

    class CleanFormatter(logging.Formatter):
        def format(self, record):
            if record.levelno >= logging.WARNING:
                return f"⚠️  {record.levelname}: {record.getMessage()}"
            elif record.name == "__main__":
                return f"🤖 {record.getMessage()}"
            else:
                return f"ℹ️  {record.getMessage()}"

    # Setup root logger to catch all messages, but only output WARNING and above
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(CleanFormatter())

    # Your bot logger
    bot_logger = logging.getLogger(__name__)
    bot_logger.setLevel(logging.DEBUG)
    bot_logger.addHandler(console_handler)
    bot_logger.propagate = False

    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("telegram").setLevel(logging.ERROR)
    logging.getLogger("apscheduler").setLevel(logging.ERROR)
    logging.getLogger("asyncio").setLevel(logging.ERROR)
    logging.getLogger("aiohttp").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)

    return bot_logger


logger = setup_logging()


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (repo names, GitHub URLs, or usernames)"""
    text = update.message.text.strip()

    # Handle @username format (user profile)
    if text.startswith("@") and len(text) > 1:
        username = text[1:]
        context.args = [username]
        logger.info(f"User profile requested: @{username}")
        await command_router.handle_profile(update, context)
        return # Add return here to prevent further processing

    # Handle GitHub URLs
    if "github.com" in text:
        try:
            parts = text.split("github.com/")[-1].split("/")
            if len(parts) >= 2:
                repo = f"{parts[0]}/{parts[1]}"
                logger.info(f"Repository requested from URL: {repo}")
                loading_msg = await update.message.reply_text(
                    "🔄 Loading...", parse_mode=None
                )
                await repository_handler.show_repository_info(
                    loading_msg, repo, context
                )
                return # Add return here
        except Exception as e:
            logger.warning(f"Failed to parse GitHub URL: {text}")
            # If parsing fails, it might fall through. Should it return? For now, let it fall.

    # Handle direct repo names (owner/repo)
    if "/" in text and len(text.split("/")) == 2:
        logger.info(f"Repository requested: {text}")
        loading_msg = await update.message.reply_text("🔄 Loading...", parse_mode=None)
        await repository_handler.show_repository_info(loading_msg, text, context)
        return # Add return here

    # NEW: Better single word username validation
    if (
        " " not in text
        and len(text) > 0
        and not text.startswith("/")
        and
        # More strict validation
        3 <= len(text) <= 39  # GitHub username length limits
        and text.replace("-", "")
        .replace("_", "")
        .replace(".", "")
        .isalnum()  # Allow dots too
        and not text.isdigit()  # Don't treat pure numbers as usernames
        and not text.upper()
        == text  # Don't treat ALL CAPS as usernames (likely not usernames)
        and text.lower() != text.upper()
    ):  # Must have letters, not just symbols

        logger.info(f"Single word username requested: {text}")

        # Add a quick validation before processing
        if await is_likely_username(text):
            from profile.handler import profile_handler

            await profile_handler.show_profile(update, context, text)
            return

    # Help message for unknown input
    await update.message.reply_text(
        "🤔 I can help you with:\n\n"
        "📂 **Repository:** `owner/repository`\n"
        "👤 **User profile:** `username` or `@username`\n"
        "🔗 **GitHub URL:** Just paste it!\n\n"
        "💡 **Commands:**\n"
        "• `/help` - Detailed help\n"
        "• `/trending` - Trending repos\n"
        "• `/user username` - User profile\n\n"
        "Try sending:\n"
        "• `facebook/react` (repository)\n"
        "• `octocat` (username)\n"
        "• `@octocat` (username with @)",
        parse_mode="Markdown",
    )


async def is_likely_username(text):
    """Quick check if text is likely a GitHub username"""
    # Common non-username patterns to avoid
    non_username_patterns = [
        # Common words that aren't usernames
        "hello",
        "hi",
        "test",
        "help",
        "thanks",
        "ok",
        "yes",
        "no",
        # Technical terms
        "api",
        "url",
        "http",
        "https",
        "www",
        "com",
        "org",
        # Common exclamations
        "wow",
        "cool",
        "nice",
        "good",
        "bad",
        "error",
    ]

    # If it's a common word, probably not a username
    if text.lower() in non_username_patterns:
        return False

    # If it has multiple consecutive dots/hyphens, probably not a username
    if ".." in text or "--" in text or "__" in text:
        return False

    # If it starts/ends with special chars, probably not a username
    if text.startswith(("-", "_", ".")) or text.endswith(("-", "_", ".")):
        return False

    return True


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route button presses to appropriate handlers"""
    query = update.callback_query
    action = query.data

    try:
        # Command-related callbacks
        command_callbacks = [
            "back_to_start",
            "help",
            "trending",
            "about",
            "developer_profile",
            "source_code",
            "other_projects",
            "rate_bot",
        ]

        if action in command_callbacks:
            await command_router.handle_callback_query(update, context)
            return

        # Trending-related callbacks
        if action.startswith("trending_"):
            await command_router.handle_callback_query(update, context)
            return

        # User profile callbacks
        if (
            action.startswith("user_")
            or action.startswith("refresh_user_")
            or action.startswith("refresh_avatar_")
            or action == "back_to_profile"
            or action.startswith("show_avatar_")
        ):
            await command_router.handle_callback_query(update, context)
            return

        # README navigation callbacks
        if action == "readme_next" or action == "readme_prev" or action.startswith("readme_page_"):
            await handle_readme_navigation(update, context)
            return

        if action == "readme_pages":
            await handle_readme_pages(update, context)
            return

        # Repository callbacks (including regular readme)
        repo_callbacks = [
            "contributors",
            "readme",
            "prs",
            "issues",
            "languages",
            "releases",
            "refresh",
        ]

        if action in repo_callbacks:
            await repository_handler.handle_callback(update, context, action)
            return

        # If none of the above matched
        logger.warning(f"Unknown callback action: {action}")
        await query.answer("❌ Unknown action")

    except Exception as e:
        logger.error(f"Error handling callback {action}: {str(e)}")
        await query.answer("❌ Something went wrong. Please try again.")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Bot error: {str(context.error)}")

    # Try to inform user about the error
    if update and hasattr(update, "callback_query") and update.callback_query:
        try:
            await update.callback_query.answer(
                "❌ Something went wrong. Please try again."
            )
        except:
            pass
    elif update and hasattr(update, "message") and update.message:
        try:
            await update.message.reply_text(
                "❌ Something went wrong. Please try again."
            )
        except:
            pass


def main():
    """Start the bot"""
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not found in .env file!")
        return

    # Create application
    app = Application.builder().token(BOT_TOKEN).build()

    # Add error handler
    app.add_error_handler(error_handler)

    # Add command handlers
    app.add_handler(CommandHandler("start", command_router.handle_start))
    app.add_handler(CommandHandler("help", command_router.handle_help))
    app.add_handler(CommandHandler("trending", command_router.handle_trending))
    app.add_handler(CommandHandler("user", command_router.handle_profile))
    app.add_handler(
        CommandHandler("profile", command_router.handle_profile)
    )  # Alternative command

    # Add callback and message handlers
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Clean startup messages
    logger.info("GitHub Explorer Bot starting...")
    logger.info("Available commands: /start, /help, /trending, /user")
    logger.info("Bot is ready! Send /start to begin.")

    print("🚀 GitHub Explorer Bot v2.0 started!")
    print("📝 Commands: /start, /help, /trending, /user")
    print("💡 Try sending: facebook/react or @octocat")
    print("⏹️  Press Ctrl+C to stop")

    try:
        app.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {str(e)}")
        print(f"\n❌ Bot crashed: {str(e)}")
    finally:
        logger.info("Bot shutdown complete")
        print("👋 Bot shutdown complete")


if __name__ == "__main__":
    main()
