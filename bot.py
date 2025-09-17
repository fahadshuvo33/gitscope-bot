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
from dotenv import load_dotenv
import os

# Load environment
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_TELEGRAM_USERNAME = os.getenv("ADMIN_TELEGRAM_USERNAME", "").lower()

# Import utils - FIX: Import the actual utils instance
from utils.manager import utils
from utils.db_logger import log_activity
from utils.input_parser import InputParser
# from utils.loading import update_content_with_loading
# from utils.loading import withLoading
from commands import about_command,start_command,developer_command,help_command,trending_command,handle_profile,handle_repository
from admin import logs_command, handle_logs_callback, is_admin
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

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages - parse GitHub profiles and repositories"""
    try:
        text = update.message.text.strip()
        user = update.effective_user
        user_id = user.username or f"user_{user.id}"
        
        # FIX: Pass user.username instead of user object
        user_is_admin = is_admin(user.username) if user.username else False
        
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
            elif command == 'logs':
                await logs_command(update, context)
            return
        
        elif parsed['type'] == 'profile':
            await handle_profile(update, parsed['username'], user_is_admin)
        
        elif parsed['type'] == 'repository':
            await handle_repository(update,parsed['repo_owner'],parsed['repo_name'],user_is_admin)
                
        elif parsed['type'] == 'invalid':
            # Just show the message that InputParser provides
            await update.message.reply_text(
                parsed['message'],
                parse_mode="MarkdownV2"
            )
        else:
            # Handle other invalid inputs
            await update.message.reply_text(
                parsed.get('message', get_invalid_input_message()),
                parse_mode="Markdown"
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
        if data == "start":
            await start_command(update, context)
        elif data == "help_menu":
            await help_command(update, context)
        elif data == "about_info":
            await about_command(update, context)
        elif data == "developer_info":
            await developer_command(update, context)
        elif data == "trending_menu":
            await trending_command(update, context)
        elif data == "show_logs" and is_admin(query.from_user.username if query.from_user.username else None):
            await logs_command(update, context)
        else:
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
    
    logger.info(f"Starting GitScope Bot with token: {BOT_TOKEN[:10]}...")
    
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("trending", trending_command))
        application.add_handler(CommandHandler("developer", developer_command))
        application.add_handler(CommandHandler("about", about_command))
        application.add_handler(CommandHandler("logs", logs_command))
        
        # Callback query handler
        application.add_handler(CallbackQueryHandler(handle_callback_query))
        
        # Text message handler
        application.add_handler(MessageHandler(filters.TEXT, handle_text))
        
        # Error handler
        application.add_error_handler(error_handler)
        
        logger.info("Bot handlers registered successfully")
        logger.info("Starting polling...")
        
        # Run the bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        # application.run_polling(drop_pending_updates=True)
        # application.run_polling()

        logger.info("Bot is running...")
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)

if __name__ == "__main__":
    main()