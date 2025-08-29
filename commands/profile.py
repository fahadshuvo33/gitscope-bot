from telegram import Update
from telegram.ext import ContextTypes
import logging
import re

# Import the loading system
from utils.loading import show_static_loading, show_error
from admin import ADMIN_GITHUB_USERNAME
from admin.admin_profile import show_admin_profile
from utils.formatting import _escape_markdown_v2

logger = logging.getLogger(__name__)


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /user or /profile command with validation and loading"""

    # Validate command arguments
    if not update.message or not context.args:
        await _show_usage_help(update.message)
        return

    username = context.args[0].replace("@", "").strip()

    # Check if it's the admin's profile
    if username.lower() == ADMIN_GITHUB_USERNAME.lower():
        await show_admin_profile(update, context, username)
        return

    # Validate username format for non-admin profiles
    validation_result = _validate_github_username(username)
    if not validation_result["valid"]:
        await _show_validation_error(
            update.message, username, validation_result["error"]
        )
        return

    # Show initial loading state for non-admin profiles
    loading_msg = await update.message.reply_text(
        f"👤 **{_escape_markdown_v2(username)}'s Profile**\n\n💡 **Tip:** Starting search...",
        parse_mode="Markdown",
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


def _clean_username(username):
    """Clean and normalize username"""
    if not username:
        return ""

    # Remove @ symbol if present at the start
    username = username.lstrip("@")

    # Remove any URL parts if someone pastes a GitHub URL
    if "github.com" in username:
        # Extract username from URL
        parts = username.split("/")
        # Find the part after github.com
        for i, part in enumerate(parts):
            if "github.com" in part and i + 1 < len(parts):
                username = parts[i + 1]
                break
    elif "/" in username:
        # If it contains / but not github.com, take the first part
        username = username.split("/")[0]

    # Remove common URL prefixes/suffixes
    username = username.replace("https://", "").replace("http://", "")
    username = username.replace("www.", "").replace(".git", "")

    # Clean whitespace and normalize (don't lowercase to preserve original case)
    username = username.strip()

    return username


# Removed _escape_markdown as it's now in utils/formatting.py


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

    if username.startswith("-") or username.endswith("-"):
        return {"valid": False, "error": "hyphen_edges"}

    if "--" in username:
        return {"valid": False, "error": "double_hyphen"}

    # Check for valid characters (alphanumeric + single hyphens)
    if not re.match(r"^[a-zA-Z0-9-]+$", username):
        return {"valid": False, "error": "invalid_chars"}

    reserved_names = [
        "admin",
        "root",
        "api",
        "www",
        "github",
        "support",
        "help",
        "about",
        "blog",
        "api",
        "status",
    ]
    if username.lower() in reserved_names:
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
        f"• `{_escape_markdown_v2("@gaearon")}` (just send the @username)\n\n"  # Use _escape_markdown_v2
        "💡 **Tip:** You can use @ symbol or just the username!"
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

    # Escape username for display
    display_username = (
        _escape_markdown_v2(username) if username else "empty"
    )  # Use the new escape function

    error_messages = {
        "empty": "Username cannot be empty",
        "too_long": f"Username '{display_username}' is too long (max 39 characters)",
        "too_short": "Username is too short",
        "hyphen_edges": f"Username '{display_username}' cannot start or end with a hyphen",
        "double_hyphen": f"Username '{display_username}' cannot contain consecutive hyphens",
        "invalid_chars": f"Username '{display_username}' contains invalid characters",
        "reserved": f"Username '{display_username}' appears to be reserved",
    }

    specific_error = error_messages.get(
        error_type, f"Username '{display_username}' is invalid"
    )

    error_text = (
        "❌ **Invalid Username**\n\n"
        f"**Error:** {specific_error}\n\n"
        "**GitHub Username Rules:**\n"
        "• Only letters, numbers, and single hyphens\n"
        "• Cannot start or end with hyphen\n"
        "• Maximum 39 characters\n\n"
        "**Valid Examples:**\n"
        "• `/user octocat`\n"
        "• `/user torvalds`\n"
        "• Just send `@username`"
        "**Valid Examples:**\n"
        "• `/user octocat`\n"
        "• `/user torvalds`\n"
        "• Just send `@username`"
    )

    try:
        await message.reply_text(error_text, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Validation error display failed: {type(e).__name__}")
        # Fallback to simple message
        await message.reply_text("❌ Invalid username. Please check and try again.")
        await message.reply_text("❌ Invalid username. Please check and try again.")


async def _show_system_error(message, username, error_type):
    """Show system error with structured message"""
    try:
        # Escape username for display
        escaped_username = _escape_markdown_v2(username)  # Use the new escape function

        error_text = await show_error(
            message,
            f"👤 **{escaped_username}'s Profile**",
            f"👤 **{escaped_username}'s Profile**",
            error_type,
            preserve_content=True,
        )

        # Replace generic error with more specific message
        if error_type == "System Error":
            error_text = error_text.replace(
                f"❌❌ {error_type} - Please try again ❌❌",
                f"❌❌ {error_type} - Please try again ❌❌",
                "⚙️ System temporarily unavailable",
            )
        elif error_type == "Unexpected Error":
            error_text = error_text.replace(
                f"❌❌ {error_type} - Please try again ❌❌",
                f"❌❌ {error_type} - Please try again ❌❌",
                "🔄 Something unexpected happened",
            )

        await message.edit_text(error_text, parse_mode="Markdown")

    except Exception as e:
        logger.warning(f"System error display failed: {type(e).__name__}")
        # Fallback to simple error message
        try:
            await message.edit_text(
                "❌ Error loading profile. Please try again later."
                "❌ Error loading profile. Please try again later."
            )
        except Exception:
            # Don't send another message, just log the error
            logger.error(f"Failed to show error message: {e}")
            # Don't send another message, just log the error
            logger.error(f"Failed to show error message: {e}")


# Additional utility functions for other parts of the bot


def get_command_help():
    """Get help text for the profile command"""
    return {
        "command": "/user",
        "aliases": ["/profile"],
        "aliases": ["/profile"],
        "description": "Search and display GitHub user profiles",
        "usage": "/user <username>",
        "examples": ["/user octocat", "/user torvalds", "@gaearon"],
    }


def is_valid_username_format(username):
    """Quick username format validation for other components"""
    if not username or not isinstance(username, str):
        return False

    username = _clean_username(username)
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
