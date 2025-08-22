from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

# Set up logger
logger = logging.getLogger(__name__)


async def trending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /trending command"""

    # Language selection keyboard
    languages = [
        ("🐍 Python", "python"),
        ("☕ JavaScript", "javascript"),
        ("⚡ TypeScript", "typescript"),
        ("☕ Java", "java"),
        ("🔧 C++", "cpp"),
        ("🐹 Go", "go"),
        ("🦀 Rust", "rust"),
        ("💎 Ruby", "ruby"),
        ("🐘 PHP", "php"),
        ("🍎 Swift", "swift"),
        ("🟣 Kotlin", "kotlin"),
        ("All Languages", "all"),
    ]

    keyboard = []
    for i in range(0, len(languages), 2):
        row = []
        for j in range(2):
            if i + j < len(languages):
                lang_name, lang_code = languages[i + j]
                row.append(
                    InlineKeyboardButton(
                        lang_name, callback_data=f"trending_{lang_code}"
                    )
                )
        keyboard.append(row)

    # Add back button if it's a callback
    if update.callback_query:
        keyboard.append(
            [InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)

    trending_text = (
        "📈 *Trending Repositories*\n\n"
        "🔥 Discover the hottest repositories on GitHub\\!\n\n"
        "Choose a programming language to see trending repositories:\n\n"
        "💡 *Tip:* These are the most starred repositories from the past week\\."
    )

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            trending_text, parse_mode="MarkdownV2", reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            trending_text, parse_mode="MarkdownV2", reply_markup=reply_markup
        )
