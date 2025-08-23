from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /user or /profile command"""

    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a GitHub username!\n\n"
            "**Usage:** `/user username`\n"
            "**Example:** `/user octocat`",
            parse_mode="Markdown",
        )
        return

    username = context.args[0].replace("@", "").strip()

    if not username:
        await update.message.reply_text(
            "❌ Please provide a valid username!", parse_mode=None
        )
        return

    # Import the profile handler
    from profile.handler import profile_handler

    # Show the profile
    await profile_handler.show_profile(update, context, username)
