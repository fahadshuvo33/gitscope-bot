from telegram import Update
from telegram.ext import ContextTypes
import logging

from profile.handler import profile_handler
from admin import ADMIN_GITHUB_USERNAME
from utils.formatting import _escape_markdown_v2 # Import the new escape function

logger = logging.getLogger(__name__)

async def show_admin_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, username: str):
    """Displays the admin's GitHub profile with special highlighting."""
    logger.info(f"Displaying special admin profile for: {username}")

    # You can add custom display logic here specific to your profile.
    # For now, let's call the regular profile handler and add a special message.

    # Create a loading message (or edit existing if possible) within the admin handler
    escaped_username = _escape_markdown_v2(username) # Use the new escape function
    if update.message:
        try:
            loading_msg = await update.message.edit_text(
                f"👤 **{escaped_username}'s Profile**\n\n✨ _Special Admin Profile_ ✨\n\n💡 **Tip:** Searching for user...",
                parse_mode="Markdown",
            )
        except Exception:
            loading_msg = await update.message.reply_text(
                f"👤 **{escaped_username}'s Profile**\n\n✨ _Special Admin Profile_ ✨\n\n💡 **Tip:** Searching for user...",
                parse_mode="Markdown",
            )
    elif update.callback_query and update.callback_query.message:
        query = update.callback_query
        await query.answer()
        loading_msg = query.message
    else:
        logger.error("Cannot determine message object for admin profile display.")
        return

    # Pass the created/identified loading_msg to the generic profile handler, with the admin flag
    await profile_handler.show_profile(update, context, username, loading_msg=loading_msg, is_admin_profile=True)

    # Optional: Further enhance the display if needed after the profile is shown by the generic handler
    # This could involve editing the final message from show_profile to add more admin-specific details.
