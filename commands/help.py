from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "📖 *GitHub Explorer Bot Help*\n\n"

        "🎯 *Commands:*\n"
        "• `/start` \\- Show welcome message\n"
        "• `/help` \\- Show this help\n"
        "• `/trending` \\- View trending repositories\n"
        "• `/user <username>` \\- View GitHub user profile\n\n"

        "🔍 *Quick Search:*\n"
        "Send me any of these formats:\n"
        "• `facebook/react` \\- Repository name\n"
        "• `https://github.com/microsoft/vscode` \\- Full URL\n"
        "• `@octocat` \\- User profile \$with @\$\n\n"

        "📊 *Repository Features:*\n"
        "• View statistics & info\n"
        "• Browse contributors\n"
        "• Check open issues & PRs\n"
        "• See programming languages\n"
        "• View latest releases\n"
        "• Read README preview\n\n"

        "👤 *User Profile Features:*\n"
        "• View user information\n"
        "• Browse user repositories\n"
        "• See contribution stats\n"
        "• Check followers/following\n\n"

        "📈 *Trending Features:*\n"
        "• Filter by programming language\n"
        "• View daily/weekly/monthly trends\n"
        "• Discover new repositories\n\n"

        "💡 *Tips:*\n"
        "• All data is fetched in real\\-time\n"
        "• Only public repositories are supported\n"
        "• Use buttons for easy navigation\n\n"

        "Need help\\? Just ask\\! 😊"
    )

    if update.callback_query:
        query = update.callback_query
        await query.answer()

        keyboard = [[InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            help_text,
            parse_mode="MarkdownV2",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(help_text, parse_mode="MarkdownV2")
