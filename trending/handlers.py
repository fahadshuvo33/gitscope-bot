# trending/handlers.py
"""Handlers for trending functionality"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from utils.git_api import create_github_session
from utils.db_logger import log_activity
from .languages import LANGUAGE_CODES, get_language, format_language_button
from .api import fetch_trending_repos
from .formatters import (
    format_repo_entry, 
    format_trending_header,
    format_no_results_message,
    format_error_message,
    format_languages_menu_text,
    format_period_selection_text,
    get_period_info,
    get_period_buttons_data,
    PERIODS
)
from .utils import get_user_period, set_user_period, set_user_language
from utils.loading import with_loading

logger = logging.getLogger(__name__)

async def show_languages_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show language selection menu"""
    user = update.effective_user
    user_id = user.username or f"user_{user.id}"
    
    logger.info(f"Trending menu shown for {user_id}")
    
    # Create language buttons (3 columns)
    keyboard = []
    for i in range(0, len(LANGUAGE_CODES), 3):
        row = []
        for j in range(3):
            if i + j < len(LANGUAGE_CODES):
                code = LANGUAGE_CODES[i + j]
                button_text = format_language_button(code)
                row.append(
                    InlineKeyboardButton(
                        button_text,
                        callback_data=f"trend_lang_{code}"
                    )
                )
        if row:
            keyboard.append(row)
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("🏠 Back to Start", callback_data="start")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = format_languages_menu_text()
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=reply_markup
        )

async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection and show trending repos directly with weekly as default"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language_code = query.data.replace("trend_lang_", "")
    
    # Store user's language selection
    set_user_language(user.id, language_code)
    
    # Get current period (default to weekly)
    current_period = get_user_period(user.id)
    
    # Directly call show_trending_repos with loading
    await _show_trending_repos_internal(update, context, language_code, current_period)

# trending/handlers.py (continued)

async def handle_period_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle period change request - show period selection menu"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Parse callback data
    parts = query.data.split("_")
    language_code = parts[2]
    
    current_period = get_user_period(user.id)
    
    # Create period selection buttons using centralized data
    period_buttons_data = get_period_buttons_data()
    
    keyboard = []
    for period_name, period_code in period_buttons_data:
        if period_code == current_period:
            button_text = f"✅ {period_name}"
        else:
            button_text = period_name
        
        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f"trend_setperiod_{language_code}_{period_code}"
            )
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("🔙 Back to Results", callback_data=f"trend_show_{language_code}_{current_period}")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = format_period_selection_text(language_code, current_period)
    
    await query.message.edit_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=reply_markup
    )

async def handle_period_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle period selection and show results"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Parse callback data: trend_setperiod_language_period
    parts = query.data.split("_")
    language_code = parts[2]
    period = parts[3]
    
    # Update user's period preference
    set_user_period(user.id, period)
    
    # Show trending repos with new period
    await _show_trending_repos_internal(update, context, language_code, period)

async def show_trending_repos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the actual trending repositories - wrapper for callback"""
    query = update.callback_query
    await query.answer()
    
    # Parse callback data: trend_show_language_period
    parts = query.data.split("_")
    language_code = parts[2]
    period = parts[3] if len(parts) > 3 else get_user_period(update.effective_user.id)
    
    await _show_trending_repos_internal(update, context, language_code, period)

@with_loading("🔍 Fetching trending repositories...", duration=2.0)
async def _show_trending_repos_internal(update: Update, context: ContextTypes.DEFAULT_TYPE, language_code: str, period: str):
    """Internal function to show trending repos"""
    user = update.effective_user
    user_id = user.username or f"user_{user.id}"
    
    lang_info = get_language(language_code)
    
    logger.info(f"{user_id}: Fetching {language_code} trending repos ({period})")
    
    # Get the loading message from context
    message = context.user_data.get('_loading_message') or update.callback_query.message
    
    try:
        async with create_github_session() as session:
            repos = await fetch_trending_repos(
                session,
                language=language_code if language_code != "all" else None,
                since=period,
                limit=10
            )
                
            # Create period buttons using centralized data
            period_buttons = []
            period_buttons_data = get_period_buttons_data()
            
            for period_name, period_code in period_buttons_data:
                if period_code == period:
                    # Remove emoji from current selection and add checkmark
                    clean_name = period_name.split(" ", 1)[1]  # Remove emoji
                    button_text = f"✅ {clean_name}"
                else:
                    # Remove emoji for cleaner look
                    clean_name = period_name.split(" ", 1)[1]  # Remove emoji
                    button_text = clean_name
                
                period_buttons.append(
                    InlineKeyboardButton(
                        button_text,
                        callback_data=f"trend_show_{language_code}_{period_code}"
                    )
                )
            
            # Navigation buttons with better icons
            nav_buttons = [
                InlineKeyboardButton(
                    "🔄 Refresh",
                    callback_data=f"trend_show_{language_code}_{period}"
                ),
                InlineKeyboardButton("🔙 Languages", callback_data="trending_menu"),
                InlineKeyboardButton("🏠 Home", callback_data="start")
            ]
            
            if not repos:
                error_text = format_no_results_message(language_code, period)
                
                # Create keyboard with period buttons and navigation
                keyboard = [
                    period_buttons,  # Period selection row
                    nav_buttons[:1],  # Refresh button
                    nav_buttons[1:]   # Navigation buttons
                ]
                
                error_keyboard = InlineKeyboardMarkup(keyboard)
                
                await message.edit_text(
                    error_text,
                    parse_mode='MarkdownV2',
                    reply_markup=error_keyboard
                )
                return
            
            # Format the results
            text = format_trending_header(language_code, period)
            
            # Add repo entries with enhanced formatting (no summary)
            for i, repo in enumerate(repos[:10], 1):
                text += format_repo_entry(
                    repo, 
                    i, 
                    show_language=(language_code == "all")
                )
                text += "\n"
            
            # Create simple keyboard with just period and navigation buttons
            keyboard = [
                period_buttons,   # Period selection row
                nav_buttons[:1],  # Refresh button row
                nav_buttons[1:]   # Navigation buttons row
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Update the message with results
            await message.edit_text(
                text,
                parse_mode='MarkdownV2',
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
            
    except Exception as e:
        logger.error(f"Error fetching trending repos: {e}")
        
        # Determine error type for better messaging
        error_type = "general"
        if "connection" in str(e).lower() or "timeout" in str(e).lower():
            error_type = "network"
        elif "rate limit" in str(e).lower() or "403" in str(e):
            error_type = "api"
        
        # Create period buttons for error case
        period_buttons = []
        period_buttons_data = get_period_buttons_data()
        
        for period_name, period_code in period_buttons_data:
            if period_code == period:
                clean_name = period_name.split(" ", 1)[1]
                button_text = f"✅ {clean_name}"
            else:
                clean_name = period_name.split(" ", 1)[1]
                button_text = clean_name
            
            period_buttons.append(
                InlineKeyboardButton(
                    button_text,
                    callback_data=f"trend_show_{language_code}_{period_code}"
                )
            )
        
        nav_buttons = [
            InlineKeyboardButton("🔄 Try Again", callback_data=f"trend_show_{language_code}_{period}"),
            InlineKeyboardButton("🔙 Languages", callback_data="trending_menu"),
            InlineKeyboardButton("🏠 Home", callback_data="start")
        ]
        
        keyboard = [
            period_buttons,   # Period selection row
            nav_buttons[:1],  # Try Again button
            nav_buttons[1:]   # Navigation buttons
        ]
        
        error_keyboard = InlineKeyboardMarkup(keyboard)
        error_text = format_error_message(error_type)
        
        await message.edit_text(
            error_text,
            parse_mode='MarkdownV2',
            reply_markup=error_keyboard
        )

def register_trending_handlers(app):
    """Register all trending-related handlers"""
    # Language selection
    app.add_handler(CallbackQueryHandler(
        handle_language_selection,
        pattern="^trend_lang_"
    ))
    
    # Period change request
    app.add_handler(CallbackQueryHandler(
        handle_period_change,
        pattern="^trend_period_"
    ))
    
    # Period selection
    app.add_handler(CallbackQueryHandler(
        handle_period_selection,
        pattern="^trend_setperiod_"
    ))
    
    # Show trending repos
    app.add_handler(CallbackQueryHandler(
        show_trending_repos,
        pattern="^trend_show_"
    ))