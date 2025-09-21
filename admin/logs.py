# admin/logs.py
import sqlite3
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

def get_logs(page=0, per_page=5):
    """Get logs from database with pagination"""
    try:
        conn = sqlite3.connect('admin.db')
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

def format_logs_message(logs, page, total):
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

def get_logs_keyboard(page, has_next):
    """Get keyboard for logs pagination"""
    buttons = []
    nav_buttons = []
    
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"logs_page_{page-1}"))
    
    if has_next:
        nav_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"logs_page_{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton("📊 View Reports", callback_data="admin_reports")])
    buttons.append([InlineKeyboardButton("🏠 Back to Start", callback_data="start")])
    
    return InlineKeyboardMarkup(buttons)