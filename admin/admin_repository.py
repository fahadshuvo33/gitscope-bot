from telegram import Update
from telegram.ext import ContextTypes
import logging

from features.repository import repository_handler
from admin import ADMIN_GITHUB_USERNAME

logger = logging.getLogger(__name__)

async def show_admin_repository(update: Update, context: ContextTypes.DEFAULT_TYPE, repo: str, loading_msg=None):
    """Displays an admin's repository with special highlighting."""
    logger.info(f"Displaying special admin repository for: {repo}")

    # Use the provided loading_msg if available, otherwise determine it from the update
    message_to_edit = loading_msg
    if message_to_edit is None:
        if update.message:
            message_to_edit = update.message
        elif update.callback_query and update.callback_query.message:
            message_to_edit = update.callback_query.message
        else:
            logger.error("Cannot determine message object for admin repository display.")
            return

    # Call the regular repository handler to show the repository info
    await repository_handler.show_repository_info(message_to_edit, repo, context, is_admin_repo=True)

    # Optional: Add a follow-up message or edit the existing one to add special flair
    # (This would require more advanced message editing or a custom display function)
    # For now, a simple logger message indicates the special handling.
