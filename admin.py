import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

def is_admin(username: str) -> bool:
    """Check if user is admin"""
    admin_username = os.getenv("ADMIN_TELEGRAM_USERNAME")
    return admin_username and username and username.lower() == admin_username.lower()

def get_logs(page=0, per_page=5):
    """Get logs from database with pagination"""
    try:
        conn = sqlite3.connect('logs.db')
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM logs")
        total = cursor.fetchone()[0]
        
        # Get logs for current page
        offset = page * per_page
        cursor.execute("""
            SELECT timestamp, level, message, user_id, command 
            FROM logs 
            ORDER BY id DESC 
            LIMIT ? OFFSET ?
        """, (per_page, offset))
        
        logs = cursor.fetchall()
        conn.close()
        
        return logs, total, (page + 1) * per_page < total
        
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return [], 0, False

def format_logs(logs, page, total):
    """Format logs for display"""
    if not logs:
        return "📋 **ADMIN LOGS**\n\n❌ No logs found"
    
    text = f"📋 **ADMIN LOGS** (Page {page + 1})\n\n"
    text += f"📊 Total logs: `{total}`\n\n"
    
    for timestamp, level, message, user_id, command in logs:
        # Format timestamp
        time_str = timestamp[:19] if timestamp else "Unknown"
        
        # Format level with emoji
        level_emoji = {
            'INFO': 'ℹ️',
            'WARNING': '⚠️', 
            'ERROR': '❌',
            'DEBUG': '🔍'
        }.get(level, '📝')
        
        # Truncate long messages
        if len(message) > 100:
            message = message[:97] + "..."
        
        text += f"{level_emoji} `{time_str}`\n"
        text += f"**{level}:** {message}\n"
        
        if user_id:
            text += f"👤 User: `{user_id}`\n"
        if command:
            text += f"⌨️ Command: `{command}`\n"
        
        text += "\n"
    
    return text

async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle logs command - admin only"""
    user = update.effective_user
    
    if not user.username or not is_admin(user.username):
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    page = 0
    if context.args and context.args[0].isdigit():
        page = int(context.args[0])
    
    logs, total, has_next = get_logs(page)
    text = format_logs(logs, page, total)
    
    # Create pagination buttons
    buttons = []
    nav_buttons = []
    
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"logs_page_{page-1}"))
    
    if has_next:
        nav_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"logs_page_{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton("🏠 Back to Start", callback_data="start")])
    
    keyboard = InlineKeyboardMarkup(buttons)
    
    try:
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                text,
                parse_mode="Markdown", 
                reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f"Error in logs command: {e}")
        error_text = "📋 **ADMIN LOGS**\n\n❌ Error loading logs"
        
        if update.callback_query:
            await update.callback_query.message.edit_text(error_text)
        else:
            await update.message.reply_text(error_text)

async def handle_logs_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle logs pagination callbacks"""
    query = update.callback_query
    data = query.data
    
    if data.startswith("logs_page_"):
        page = int(data.split("_")[-1])
        
        logs, total, has_next = get_logs(page)
        text = format_logs(logs, page, total)
        
        # Create pagination buttons
        buttons = []
        nav_buttons = []
        
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"logs_page_{page-1}"))
        
        if has_next:
            nav_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"logs_page_{page+1}"))
        
        if nav_buttons:
            buttons.append(nav_buttons)
        
        buttons.append([InlineKeyboardButton("🏠 Back to Start", callback_data="start")])
        
        keyboard = InlineKeyboardMarkup(buttons)
        
        try:
            await query.answer()
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error in logs callback: {e}")
            await query.answer("❌ Error loading logs")


__all__ = ['logs_command', 'handle_logs_callback', 'is_admin']