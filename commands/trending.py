# commands/trending.py
"""Entry point for trending command"""

from telegram import Update
from telegram.ext import ContextTypes
from utils.loading import with_loading
from trending import show_languages_menu

# @with_loading("📈 Loading trending")
async def trending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /trending command - entry point"""
    await show_languages_menu(update, context)