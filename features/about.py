from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

class AboutHandler:
    def __init__(self):
        self.bot_name = "GitHub Explorer Bot"
        self.version = "2.0.0"

    async def handle_about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle about button"""
        query = update.callback_query
        await query.answer()

        about_text = (
            f"ℹ️ *About {escape_markdown(self.bot_name, 2)}*\n\n"
            f"🔧 Version: `{escape_markdown(self.version, 2)}`\n"
            f"🛠️ Built with: Python \\& python\\-telegram\\-bot\n"
            f"🔗 GitHub API: Official REST API v3\n\n"

            "🌟 *Features:*\n"
            "• 📊 Repository exploration\n"
            "• 👤 User profile viewing\n"
            "• 📈 Trending repositories\n"
            "• 💻 Language\\-based filtering\n"
            "• 🔍 Real\\-time GitHub data\n\n"

            "🚀 *New in v2\\.0:*\n"
            "• User profile exploration\n"
            "• Trending repositories by language\n"
            "• Enhanced navigation\n"
            "• Better error handling\n\n"

            "🔒 *Privacy:*\n"
            "• No data stored permanently\n"
            "• Only public GitHub data accessed\n"
            "• Your searches are not logged\n\n"

            "Made with ❤️ for developers\\!"
        )

        keyboard = [
            [
                InlineKeyboardButton("👨‍💻 Meet the Developer", callback_data="developer_profile")
            ],
            [
                InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            about_text,
            parse_mode="MarkdownV2",
            reply_markup=reply_markup
        )

# Create instance
about_handler = AboutHandler()
