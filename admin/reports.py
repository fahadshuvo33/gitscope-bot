# admin/reports.py
import sqlite3
import logging
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

def save_report(user_id, username, message):
    """Save a report to the database"""
    try:
        conn = sqlite3.connect('admin.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reports (user_id, username, message, timestamp)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, message, datetime.now().isoformat()))
        report_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Report #{report_id} saved from {username}")
        return report_id
        
    except Exception as e:
        logger.error(f"Error saving report: {e}")
        return None

def get_reports(page=0, per_page=5):
    """Get reports with pagination"""
    try:
        conn = sqlite3.connect('admin.db')
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM reports")
        total = cursor.fetchone()[0]
        
        # Get reports
        cursor.execute("""
            SELECT id, username, message, timestamp
            FROM reports
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """, (per_page, page * per_page))
        reports = cursor.fetchall()
        conn.close()
        
        has_next = (page + 1) * per_page < total
        return reports, total, has_next
        
    except Exception as e:
        logger.error(f"Error getting reports: {e}")
        return [], 0, False

def format_reports_message(reports, page, total):
    """Format reports for display"""
    text = f"📊 **USER REPORTS** (Page {page + 1})\n"
    text += f"Total Reports: {total}\n\n"
    
    if not reports:
        text += "❌ No reports found"
        return text
    
    for report_id, username, message, timestamp in reports:
        # Format timestamp
        time_str = timestamp[:16] if timestamp else "Unknown"
        
        # Truncate long messages
        if len(message) > 150:
            message = message[:147] + "..."
        
        text += f"📌 **Report #{report_id}**\n"
        text += f"👤 From: {username}\n"
        text += f"💬 {message}\n"
        text += f"🕒 {time_str}\n"
        text += "━━━━━━━━━━━━━━━\n"
    
    return text

def get_reports_keyboard(page, has_next):
    """Get keyboard for reports pagination"""
    buttons = []
    
    # Navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"reports_page_{page-1}"))
    if has_next:
        nav_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"reports_page_{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    # Other buttons
    buttons.append([InlineKeyboardButton("📋 View Logs", callback_data="show_logs")])
    buttons.append([InlineKeyboardButton("🏠 Back to Start", callback_data="start")])
    
    return InlineKeyboardMarkup(buttons)