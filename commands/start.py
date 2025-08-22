from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    user_name = escape_markdown(user.first_name or "there", 2)

    welcome_text = (
        f"👋 *Hello {user_name}\\!*\n\n"
        f"🚀 Welcome to **GitHub Explorer Bot**\n"
        f"_Your ultimate GitHub companion_\n\n"

        "🔥 *What I can do:*\n"
        "• 📊 View repository details\n"
        "• 👤 Show user profiles\n"
        "• 📈 Display trending repositories\n"
        "• 💻 Browse by programming language\n"
        "• 🔍 Search GitHub content\n\n"

        "⚡ *Quick Commands:*\n"
        "• `/help` \\- Get detailed help\n"
        "• `/trending` \\- See trending repos\n"
        "• `/user username` \\- View user profile\n\n"

        "💡 *Quick Start:*\n"
        "Just send me a repository name like `facebook/react` or a GitHub URL\\!"
    )

    keyboard = [
        [
            InlineKeyboardButton("📖 Help", callback_data="help"),
            InlineKeyboardButton("📈 Trending", callback_data="trending")
        ],
        [
            InlineKeyboardButton("ℹ️ About", callback_data="about")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Check if it's a callback query or regular message
    if update.callback_query:
        await update.callback_query.edit_message_text(
            welcome_text,
            parse_mode="MarkdownV2",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            welcome_text,
            parse_mode="MarkdownV2",
            reply_markup=reply_markup
        )

    # Clear any existing data
    context.user_data.clear()
