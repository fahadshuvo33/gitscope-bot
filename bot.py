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
from trending import register_trending_handlers 
from dotenv import load_dotenv
import os

# Load environment
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Import utils - FIX: Import the actual utils instance
from utils.manager import utils
from admin.activity import log_activity
from utils.input_parser import InputParser
from commands import about_command,start_command,developer_command,help_command,trending_command,handle_repository
from admin import is_admin_github, is_admin_telegram
from admin.handlers import report_command, handle_admin_callbacks
from profile import profile_handler
# Import templates
from templates import (
    get_invalid_input_message,
)

def setup_logging():
    """Setup clean logging configuration"""
    
    # Set up basic config first
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Get logger
    logger = logging.getLogger(__name__)
    
    # Suppress noisy loggers
    for logger_name in ["httpx", "telegram", "apscheduler", "asyncio", "aiohttp", "urllib3"]:
        logging.getLogger(logger_name).setLevel(logging.ERROR)
    
    return logger

logger = setup_logging()

async def profile_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route profile-related callback queries to ProfileHandler with action string."""
    if not update.callback_query:
        return
    data = update.callback_query.data
    await profile_handler.handle_profile_callback(update, context, data)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages - parse GitHub profiles and repositories"""
    try:
        text = update.message.text.strip()
        user = update.effective_user
        user_id = user.username or f"user_{user.id}"
        
        # FIX: Pass user.username instead of user object
        is_telegram_admin = is_admin_telegram(user_id) if user_id else False
        
        logger.info(f"Text received from {user_id}: {text}")
        
        parsed = InputParser.parse_input(text)

        if parsed['type'] == 'command':
            command = parsed['command']
            if command == 'start':
                await start_command(update, context)
            elif command == 'help':
                await help_command(update, context)
            elif command == 'trending':
                await trending_command(update, context)
            elif command == 'developer':
                await developer_command(update, context)
            elif command == 'about':
                await about_command(update, context)
            elif command == 'report':
                await report_command(update, context)
            return
        
        elif parsed['type'] == 'profile':
            is_github_admin = is_admin_github(parsed['username']) if parsed['username'] else False
            await profile_handler.show_profile(update, context, parsed['username'], is_github_admin)

        elif parsed['type'] == 'repository':
            is_github_admin = is_admin_github(parsed['repo_owner']) if parsed['repo_owner'] else False
            await handle_repository(update,parsed['repo_owner'],parsed['repo_name'],is_github_admin)
                
        elif parsed['type'] == 'invalid':
            # Create a keyboard with a help button
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🆘 Help Menu", callback_data="help_menu")]
            ])
            
            # Show the error message with help button
            await update.message.reply_text(
                parsed['message'],
                parse_mode="MarkdownV2",
                reply_markup=keyboard
            )
        
        else:
            # Handle other invalid inputs with help button
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🆘 Help Menu", callback_data="help_menu")]
            ])
            
            await update.message.reply_text(
                parsed.get('message', get_invalid_input_message()),
                parse_mode="MarkdownV2",
                reply_markup=keyboard
            )
            
    except Exception as e:
        logger.error(f"Error in handle_text: {e}", exc_info=True)
        await update.message.reply_text("❌ An error occurred. Please try again.")

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries"""
    if not update.callback_query:
        return
    
    query = update.callback_query
    data = query.data
    
    logger.info(f"Callback query received: {data}")
    
    try:
        await query.answer()
        
        # Route to different handlers based on callback data
        if data == "start" or data == "back_to_start":
            await start_command(update, context)
        elif data == "help_menu":
            await help_command(update, context)
        elif data == "about_info":
            await about_command(update, context)
        elif data == "developer_info":
            await developer_command(update, context)
        elif data == "trending_menu":
            await trending_command(update, context)
        elif data in ("show_logs", "show_reports") or data.startswith("logs_page_") or data.startswith("reports_"):
            # Delegate to admin handlers (they will enforce admin checks)
            await handle_admin_callbacks(update, context)
        else:
            # Fallback: show coming soon for unknown callbacks not matched by specific handlers
            await query.message.edit_text("🚧 Feature coming soon!", parse_mode="Markdown")
            
    except Exception as e:
        logger.error(f"Error handling callback {data}: {e}", exc_info=True)
        try:
            await query.message.edit_text("❌ An error occurred. Please try again.")
        except:
            pass


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}", exc_info=True)

def main():
    """Start the bot"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables")
        return
    
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("trending", trending_command))
        application.add_handler(CommandHandler("developer", developer_command))
        application.add_handler(CommandHandler("about", about_command))
        application.add_handler(CommandHandler("report", report_command))
        
        # Callback query handlers (register specific patterns BEFORE the generic fallback)
        register_trending_handlers(application)

        # Admin callbacks (logs, reports). Use a single handler and let it route internally
        application.add_handler(CallbackQueryHandler(handle_admin_callbacks, pattern=r"^(show_logs|logs_page_\d+|show_reports|reports_page_\d+)$"))

        # Profile actions (show avatar, repos, starred, followers, following, stats, refresh, back)
        application.add_handler(CallbackQueryHandler(
            profile_callback_router,
            pattern=r"^(user_repos_|user_starred_|user_followers_|user_following_|user_stats_|show_avatar_|refresh_user_|refresh_avatar_|back_to_profile)"
        ))

        # Profile pagination like: user_repos_<username>_page_<n>
        application.add_handler(CallbackQueryHandler(
            profile_callback_router,
            pattern=r"^.*_page_\d+$"
        ))

        # Generic fallback callback handler
        application.add_handler(CallbackQueryHandler(handle_callback_query))
        
        # Text message handler
        application.add_handler(MessageHandler(filters.TEXT, handle_text))
        
        # Error handler
        application.add_error_handler(error_handler)
        
        logger.info("Bot handlers registered successfully")
        
        # Run the bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        # application.run_polling(drop_pending_updates=True)
        # application.run_polling()

    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)

if __name__ == "__main__":
    main()