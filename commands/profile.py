from telegram import Update
from telegram.ext import ContextTypes
import logging
import re

# Import the loading system
from utils.loading import show_static_loading, show_error

logger = logging.getLogger(__name__)


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /user or /profile command with validation and loading"""

    # Check if called from a message
    if not update.message:
        return

    # Get username from command arguments or message text
    username = None
    
    if context.args:
        # Get username from command args
        raw_username = " ".join(context.args).strip()
        username = _clean_username(raw_username)
    else:
        # Check if the message text contains @username
        message_text = update.message.text
        if message_text:
            # Extract username from message (handles @username sent directly)
            parts = message_text.split()
            for part in parts:
                if part.startswith('@') and len(part) > 1:
                    username = _clean_username(part)
                    break
    
    # If still no username, show help
    if not username:
        await _show_usage_help(update.message)
        return

    # Validate username format
    validation_result = _validate_github_username(username)
    if not validation_result["valid"]:
        await _show_validation_error(update.message, username, validation_result["error"])
        return

    # IMPORTANT: The initial message is handled by profile_handler.show_profile
    # This prevents the two-block issue by letting the handler manage the message lifecycle
    
    try:
        # Import and use the profile handler
        from profile.handler import profile_handler

        # Show the profile using the handler's robust system, passing the original update
        await profile_handler.show_profile(update, context, username)

    except ImportError as e:
        logger.error(f"Profile handler import error: {type(e).__name__} - {e}")
        # Use original message for error if possible
        if update.message:
            await _show_system_error(update.message, username, "System Error")
    except Exception as e:
        logger.error(f"Profile command error for {username}: {type(e).__name__} - {e}")
        # Use original message for error if possible
        if update.message:
            await _show_system_error(update.message, username, "Unexpected Error")


# Handle @username messages directly (not as command)
async def handle_at_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages that start with @username"""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    
    # Check if message starts with @ and has more than just @
    if text.startswith('@') and len(text) > 1:
        # Extract username
        username = _clean_username(text.split()[0])
        
        if username:
            # Validate username format
            validation_result = _validate_github_username(username)
            if not validation_result["valid"]:
                await _show_validation_error(update.message, username, validation_result["error"])
                return
            
            # Delete the user's message to keep chat clean
            try:
                await update.message.delete()
            except:
                pass
            
            # Send loading message
            escaped_username = _escape_markdown(username)
            loading_msg = await update.message.chat.send_message(
                f"👤 **{escaped_username}'s Profile**\n\n💡 **Tip:** Searching GitHub...",
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
                logger.error(f"Profile handler import error: {type(e).__name__} - {e}")
                await _show_system_error(loading_msg, username, "System Error")
            except Exception as e:
                logger.error(f"Profile command error for {username}: {type(e).__name__} - {e}")
                await _show_system_error(loading_msg, username, "Unexpected Error")
            
            return True
    
    return False


def _clean_username(username):
    """Clean and normalize username"""
    if not username:
        return ""
    
    # Remove @ symbol if present at the start
    username = username.lstrip('@')
    
    # Remove any URL parts if someone pastes a GitHub URL
    if 'github.com' in username:
        # Extract username from URL
        parts = username.split('/')
        # Find the part after github.com
        for i, part in enumerate(parts):
            if 'github.com' in part and i + 1 < len(parts):
                username = parts[i + 1]
                break
    elif '/' in username:
        # If it contains / but not github.com, take the first part
        username = username.split('/')[0]
    
    # Remove common URL prefixes/suffixes
    username = username.replace('https://', '').replace('http://', '')
    username = username.replace('www.', '').replace('.git', '')
    
    # Clean whitespace and normalize (don't lowercase to preserve original case)
    username = username.strip()
    
    return username


def _escape_markdown(text):
    """Escape special characters for Markdown"""
    # List of characters that need escaping in Markdown
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    escaped_text = text
    for char in special_chars:
        escaped_text = escaped_text.replace(char, f'\\{char}')
    
    return escaped_text


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
    reserved_names = ['admin', 'root', 'api', 'www', 'github', 'support', 'help', 'about', 'blog', 'api', 'status']
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
        "• `@gaearon` just send the @username\n\n"
        "💡 **Tip:** You can use @ symbol or just the username\\!"
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
    display_username = _escape_markdown(username) if username else "empty"

    error_messages = {
        "empty": "Username cannot be empty",
        "too_long": f"Username '{display_username}' is too long max 39 characters",
        "too_short": "Username is too short",
        "hyphen_edges": f"Username '{display_username}' cannot start or end with a hyphen",
        "double_hyphen": f"Username '{display_username}' cannot contain consecutive hyphens",
        "invalid_chars": f"Username '{display_username}' contains invalid characters",
        "reserved": f"Username '{display_username}' appears to be reserved"
    }

    specific_error = error_messages.get(error_type, f"Username '{display_username}' is invalid")

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
    )

    try:
        await message.reply_text(error_text, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Validation error display failed: {type(e).__name__}")
        # Fallback to simple message
        await message.reply_text("❌ Invalid username. Please check and try again.")


async def _show_system_error(message, username, error_type):
    """Show system error with structured message"""
    try:
        # Escape username for display
        escaped_username = _escape_markdown(username)
        
        error_text = await show_error(
            message,
            f"👤 **{escaped_username}'s Profile**",
            error_type,
            preserve_content=True,
        )

        # Replace generic error with more specific message
        if error_type == "System Error":
            error_text = error_text.replace(
                f"❌❌ {error_type} - Please try again ❌❌",
                "⚙️ System temporarily unavailable"
            )
        elif error_type == "Unexpected Error":
            error_text = error_text.replace(
                f"❌❌ {error_type} - Please try again ❌❌",
                "🔄 Something unexpected happened"
            )

        await message.edit_text(error_text, parse_mode="Markdown")

    except Exception as e:
        logger.warning(f"System error display failed: {type(e).__name__}")
        # Fallback to simple error message
        try:
            await message.edit_text(
                "❌ Error loading profile. Please try again later."
            )
        except Exception:
            # Don't send another message, just log the error
            logger.error(f"Failed to show error message: {e}")


# Additional utility functions for other parts of the bot

def get_command_help():
    """Get help text for the profile command"""
    return {
        "command": "/user",
        "aliases": ["/profile"],
        "description": "Search and display GitHub user profiles",
        "usage": "/user <username>",
        "examples": ["/user octocat", "/user torvalds", "@gaearon"]
    }


def is_valid_username_format(username):
    """Quick username format validation for other components"""
    if not username or not isinstance(username, str):
        return False

    username = _clean_username(username)