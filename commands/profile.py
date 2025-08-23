from telegram import Update
from telegram.ext import ContextTypes
import logging
import re

# Import the loading system
from utils.loading import show_static_loading, show_error

logger = logging.getLogger(__name__)


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /user or /profile command with validation and loading"""

    # Validate command arguments
    if not context.args:
        await _show_usage_help(update.message)
        return

    username = context.args[0].replace("@", "").strip().lower()

    # Validate username format
    validation_result = _validate_github_username(username)
    if not validation_result["valid"]:
        await _show_validation_error(update.message, username, validation_result["error"])
        return

    # Show initial loading state
    loading_msg = await update.message.reply_text(
        f"👤 **{username}'s Profile**\n\n💡 **Tip:** Starting search...",
        parse_mode="Markdown"
    )

    try:
        # Import and use the profile handler
        from profile.handler import profile_handler

        # Create a mock update object for the profile handler
        class MockUpdate:
            def __init__(self, message):
                self.message = message
                self.callback_query = None

        mock_update = MockUpdate(loading_msg)

        # Show the profile using the handler's robust system
        await profile_handler.show_profile(mock_update, context, username)

    except ImportError as e:
        logger.error(f"Profile handler import error: {type(e).__name__}")
        await _show_system_error(loading_msg, username, "System Error")
    except Exception as e:
        logger.error(f"Profile command error for {username}: {type(e).__name__}")
        await _show_system_error(loading_msg, username, "Unexpected Error")


def _validate_github_username(username):
    """Validate GitHub username format"""
    if not username:
        return {"valid": False, "error": "empty"}

    # GitHub username rules:
    # - May only contain alphanumeric characters or single hyphens
    # - Cannot begin or end with a hyphen
    # - Maximum 39 characters

    if len(username) > 39:
        return {"valid": False, "error": "too_long"}

    if len(username) < 1:
        return {"valid": False, "error": "too_short"}

    if username.startswith('-') or username.endswith('-'):
        return {"valid": False, "error": "hyphen_edges"}

    if '--' in username:
        return {"valid": False, "error": "double_hyphen"}

    # Check for valid characters (alphanumeric + single hyphens)
    if not re.match(r'^[a-zA-Z0-9-]+$', username):
        return {"valid": False, "error": "invalid_chars"}

    # Additional checks for common issues
    if username in ['admin', 'root', 'api', 'www', 'github', 'support']:
        return {"valid": False, "error": "reserved"}

    return {"valid": True, "error": None}


async def _show_usage_help(message):
    """Show usage help with examples"""
    help_text = (
        "🔍 **GitHub Profile Search**\n\n"
        "**Usage:** `/user <username>`\n\n"
        "**Examples:**\n"
        "• `/user octocat`\n"
        "• `/user torvalds`\n"
        "• `/user gaearon`\n\n"
        "💡 **Tip:** Enter any GitHub username to explore their profile!"
    )

    try:
        await message.reply_text(help_text, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Help message failed: {type(e).__name__}")
        # Fallback to simple message
        await message.reply_text(
            "❌ Please provide a GitHub username!\n\nUsage: /user username\nExample: /user octocat"
        )


async def _show_validation_error(message, username, error_type):
    """Show username validation error with helpful guidance"""

    error_messages = {
        "empty": "Username cannot be empty",
        "too_long": f"Username '{username}' is too long (max 39 characters)",
        "too_short": "Username is too short",
        "hyphen_edges": f"Username '{username}' cannot start or end with a hyphen",
        "double_hyphen": f"Username '{username}' cannot contain consecutive hyphens",
        "invalid_chars": f"Username '{username}' contains invalid characters",
        "reserved": f"Username '{username}' appears to be reserved"
    }

    specific_error = error_messages.get(error_type, f"Username '{username}' is invalid")

    error_text = (
        "❌ **Invalid Username**\n\n"
        f"**Error:** {specific_error}\n\n"
        "**GitHub Username Rules:**\n"
        "• Only letters, numbers, and single hyphens\n"
        "• Cannot start or end with hyphen\n"
        "• Maximum 39 characters\n\n"
        "**Example:** `/user octocat`"
    )

    try:
        await message.reply_text(error_text, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Validation error display failed: {type(e).__name__}")
        # Fallback to simple message
        await message.reply_text(f"❌ Invalid username '{username}'. Please check and try again.")


async def _show_system_error(message, username, error_type):
    """Show system error with structured message"""
    try:
        error_text = await show_error(
            message,
            f"👤 **{username}'s Profile**",
            error_type,
            preserve_content=True,
        )

        # Replace generic error with more specific message
        if error_type == "System Error":
            error_text = error_text.replace(
                f"❌❌ {error_type} - Try again ❌❌",
                "⚙️ System temporarily unavailable"
            )
        elif error_type == "Unexpected Error":
            error_text = error_text.replace(
                f"❌❌ {error_type} - Try again ❌❌",
                "🔄 Something unexpected happened"
            )

        await message.edit_text(error_text, parse_mode="Markdown")

    except Exception as e:
        logger.warning(f"System error display failed: {type(e).__name__}")
        # Fallback to simple error message
        try:
            await message.edit_text(
                f"❌ Error loading profile for {username}. Please try again later."
            )
        except Exception:
            # Final fallback - send new message
            await message.reply_text(
                f"❌ Error loading profile for {username}. Please try again later."
            )


# Additional utility functions for other parts of the bot

def get_command_help():
    """Get help text for the profile command"""
    return {
        "command": "/user",
        "description": "Search and display GitHub user profiles",
        "usage": "/user <username>",
        "examples": ["/user octocat", "/user torvalds"]
    }


def is_valid_username_format(username):
    """Quick username format validation for other components"""
    if not username or not isinstance(username, str):
        return False

    username = username.strip().lower()
    validation = _validate_github_username(username)
    return validation["valid"]


async def quick_profile_lookup(update, context, username):
    """Quick profile lookup for other components to use"""
    if not is_valid_username_format(username):
        return False

    try:
        await profile_command(update, context)
        return True
    except Exception as e:
        logger.warning(f"Quick lookup failed for {username}: {type(e).__name__}")
        return False
