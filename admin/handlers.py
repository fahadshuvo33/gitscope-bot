# admin/handlers.py
from telegram import Update
from telegram.ext import ContextTypes
import logging
from . import is_admin_telegram
from .logs import get_logs, format_logs_message, get_logs_keyboard
from .reports import save_report, get_reports, format_reports_message, get_reports_keyboard
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

# In admin/handlers.py, update the report_command function:
async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report command - available to all users"""
    user = update.effective_user
    
    if not context.args:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Back to Start", callback_data="start")]
        ])
        await update.message.reply_text(
            "📢 **Submit a Report**\n\n"
            "Usage: `/report [your message]`\n\n"
            "Examples:\n"
            "• `/report Profile pictures not loading`\n"
            "• `/report Please add private repositories support`",
            parse_mode="Markdown",
            reply_markup=keyboard

        )
        return
    
    message = ' '.join(context.args)
    username = user.username or f"user_{user.id}"
    
    report_id = save_report(str(user.id), username, message)
    
    if report_id:
        # Success message with praise
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Back to Start", callback_data="start")]
        ])
        
        await update.message.reply_text(
            f"✅ **Report Submitted Successfully!**\n\n"
            f"Thank you so much for taking the time to help us improve GitScope Bot!\n\n"
            f"Your feedback is incredibly valuable to us. We review every single report and use them to make the bot better for everyone.\n\n"
            f"Together, we're building something amazing! 💪",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Back to Start", callback_data="start")]
        ])
        
        await update.message.reply_text(
            "❌ Oops! Something went wrong while submitting your report.\n\n"
            "Please try again in a moment. Your feedback is important to us!",
            parse_mode="Markdown",
            reply_markup=keyboard
        )


# Simplify the admin callbacks:
async def handle_admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin-related callbacks"""
    query = update.callback_query
    data = query.data
    user = query.from_user
    
    # Check admin permission
    if not user.username or not is_admin_telegram(user.username):
        await query.answer("❌ Access denied. Admin only.", show_alert=True)
        return
    
    await query.answer()
    
    # Handle logs
    if data == "show_logs":
        logs, total, has_next = get_logs(page=0)
        text = format_logs_message(logs, 0, total)
        keyboard = get_logs_keyboard(0, has_next)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    
    elif data.startswith("logs_page_"):
        page = int(data.split("_")[-1])
        logs, total, has_next = get_logs(page=page)
        text = format_logs_message(logs, page, total)
        keyboard = get_logs_keyboard(page, has_next)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    
    # Handle reports
    elif data == "show_reports":
        reports, total, has_next = get_reports(page=0)
        text = format_reports_message(reports, 0, total)
        keyboard = get_reports_keyboard(0, has_next)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    
    elif data.startswith("reports_page_"):
        page = int(data.split("_")[-1])
        reports, total, has_next = get_reports(page=page)
        text = format_reports_message(reports, page, total)
        keyboard = get_reports_keyboard(page, has_next)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)