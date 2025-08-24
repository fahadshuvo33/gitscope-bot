from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
import asyncio

# Import the loading system
from utils.loading import show_loading, show_static_loading

class AboutHandler:
    def __init__(self):
        self.bot_name = "GitHub Explorer Bot"
        self.version = "2.0.0"
        self.ABOUT_ANIMATION = "sparkle"  # Animation type for about page

    async def handle_about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle about button with loading animation"""
        query = update.callback_query
        await query.answer()

        # Show static loading first to preserve the window
        await show_static_loading(
            query.message,
            f"ℹ️ **About {self.bot_name}**",
            "Loading information",
            preserve_content=True,
            animation_type=self.ABOUT_ANIMATION,
        )

        # Start animated loading
        loading_task = await show_loading(
            query.message,
            f"ℹ️ **About {self.bot_name}**",
            "Loading information",
            animation_type=self.ABOUT_ANIMATION,
        )

        try:
            # Simulate some processing time (you can remove this if not needed)
            await asyncio.sleep(0.8)

            # Build the about content
            about_text = self._build_about_content()
            keyboard = self._build_about_keyboard()

            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

            # Update with final content
            await query.edit_message_text(
                about_text,
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

            # Show error state
            await self._show_about_error(query.message)

    def _build_about_content(self):
        """Build the about page content"""
        return (
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

    def _build_about_keyboard(self):
        """Build the about page keyboard"""
        return [
            [
                InlineKeyboardButton("👨‍💻 Meet the Developer", callback_data="developer_profile")
            ],
            [
                InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")
            ]
        ]

    async def _show_about_error(self, message):
        """Show error state for about page"""
        error_text = (
            f"ℹ️ **About {self.bot_name}**\n\n"
            "❌ **Loading Error**\n\n"
            "Unable to load about information.\n\n"
            "💡 **Tip:** Try going back and accessing again!"
        )

        keyboard = [
            [
                InlineKeyboardButton("🔄 Try Again", callback_data="about")
            ],
            [
                InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")
            ]
        ]

        try:
            await message.edit_text(
                error_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception:
            pass  # Silent fail for error display

# Create instance
about_handler = AboutHandler()
