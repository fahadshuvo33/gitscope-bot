import aiohttp
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from telegram.error import BadRequest
from utils.git_api import fetch_languages

# Import the loading system
from utils.loading import show_loading, show_static_loading

logger = logging.getLogger(__name__)

async def handle_languages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle languages display with loading animation"""
    q = update.callback_query
    await q.answer()

    repo = context.user_data.get("current_repo")
    if not repo:
        await q.edit_message_text("❌ _No repo selected\\. Send me a repository first\\._", parse_mode="MarkdownV2")
        return

    # Show static loading first to preserve the window
    try:
        await show_static_loading(
            q.message,
            f"💻 **{escape_markdown(repo, 2)} Languages**",
            "Loading language data",
            preserve_content=True,
            animation_type="tech",
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.warning(f"Static loading error: {e}")

    # Start animated loading
    loading_task = None
    try:
        loading_task = await show_loading(
            q.message,
            f"💻 **{escape_markdown(repo, 2)} Languages**",
            "Loading language data",
            animation_type="tech",
        )
    except Exception as e:
        logger.warning(f"Could not start loading animation: {e}")

    try:
        # Set timeout for API request
        timeout = aiohttp.ClientTimeout(total=10)  # 10 second timeout
        async with aiohttp.ClientSession(timeout=timeout) as session:
            languages = await fetch_languages(session, repo)

        # Stop loading animation gracefully
        if loading_task and not loading_task.done():
            loading_task.cancel()
            try:
                await loading_task
            except asyncio.CancelledError:
                pass

        # Create keyboard with refresh option
        back_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="languages"),
                InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")
            ]
        ])

        if not languages:
            await _show_no_languages(q, repo, back_keyboard)
            return

        # Build and display languages content
        text = _build_languages_content(languages, repo)

        await q.edit_message_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=back_keyboard
        )

    except asyncio.TimeoutError:
        logger.error("Timeout fetching languages")
        # Stop loading animation
        if loading_task and not loading_task.done():
            loading_task.cancel()
            try:
                await loading_task
            except asyncio.CancelledError:
                pass

        await _show_timeout_error(q, repo)

    except aiohttp.ClientError as e:
        logger.error(f"Network error fetching languages: {e}")
        # Stop loading animation
        if loading_task and not loading_task.done():
            loading_task.cancel()
            try:
                await loading_task
            except asyncio.CancelledError:
                pass

        await _show_network_error(q, repo)

    except Exception as e:
        logger.error(f"Unexpected error fetching languages: {e}")
        # Stop loading animation gracefully
        if loading_task and not loading_task.done():
            loading_task.cancel()
            try:
                await loading_task
            except asyncio.CancelledError:
                pass

        # Create error keyboard
        back_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 Try Again", callback_data="languages"),
                InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")
            ]
        ])

        await _show_languages_error(q, repo, "Fetch Error", back_keyboard)


def _build_languages_content(languages, repo):
    """Build the languages content with progress bars"""
    repo_name = escape_markdown(repo, 2)
    text = f"💻 *Programming Languages in* __{repo_name}__\n\n"

    # Calculate total bytes and sort languages
    total_bytes = sum(languages.values())
    sorted_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)

    # Enhanced language emojis mapping
    lang_emojis = {
        'JavaScript': '🟨',
        'TypeScript': '🔵',
        'Python': '🐍',
        'Java': '☕',
        'C++': '⚡',
        'C': '🔧',
        'C#': '💜',
        'Go': '🐹',
        'Rust': '🦀',
        'Ruby': '💎',
        'PHP': '🐘',
        'Swift': '🍎',
        'Kotlin': '🟣',
        'HTML': '🌐',
        'CSS': '🎨',
        'Shell': '🐚',
        'Dockerfile': '🐳',
        'YAML': '📄',
        'JSON': '📋',
        'Dart': '🎯',
        'Scala': '🔴',
        'R': '📊',
        'MATLAB': '🧮',
        'Perl': '🐪',
        'Lua': '🌙',
        'Assembly': '🔩',
        'Makefile': '⚙️',
        'CMake': '🏗️',
        'Vim Script': '📝'
    }

    # Show top languages with progress bars
    for i, (lang, bytes_count) in enumerate(sorted_languages[:10], 1):  # Show top 10
        percentage = (bytes_count / total_bytes) * 100
        emoji = lang_emojis.get(lang, '📝')
        lang_escaped = escape_markdown(lang, 2)

        # Create progress bar
        bar_length = int(percentage / 5)  # Scale down to fit
        bar = '█' * bar_length + '░' * (20 - bar_length)

        text += f"{emoji} *{lang_escaped}* :  `{percentage:.1f}%`\n"
        text += f"   `{escape_markdown(bar, 2)}`\n\n"

    # Add summary for remaining languages if any
    if len(sorted_languages) > 10:
        remaining_count = len(sorted_languages) - 10
        remaining_percentage = sum(bytes_count for _, bytes_count in sorted_languages[10:]) / total_bytes * 100
        # FIXED: Using escaped parentheses instead of dollar signs
        text += f"📊 _\\+{remaining_count} more languages {remaining_percentage:.1f}%\n"

    return text

async def _show_timeout_error(q, repo):
    """Show timeout error message"""
    back_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Try Again", callback_data="languages"),
            InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")
        ]
    ])

    repo_escaped = escape_markdown(repo, 2)
    error_text = f"💻 *{repo_escaped} Languages*\n\n"
    error_text += f"⏱️ *Request Timeout*\n\n"
    error_text += f"The request took too long to complete\\.\n\n"
    error_text += f"💡 *Tip:* Try again in a moment\\!"

    try:
        await q.edit_message_text(
            error_text,
            parse_mode="MarkdownV2",
            reply_markup=back_keyboard
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.error(f"Error updating message: {e}")


async def _show_network_error(q, repo):
    """Show network error message"""
    back_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Try Again", callback_data="languages"),
            InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")
        ]
    ])

    repo_escaped = escape_markdown(repo, 2)
    error_text = f"💻 *{repo_escaped} Languages*\n\n"
    error_text += f"🌐 *Network Error*\n\n"
    error_text += f"Could not connect to GitHub API\\.\n\n"
    error_text += f"*Please check:*\n"
    error_text += f"• Your internet connection\n"
    error_text += f"• GitHub API status\n\n"
    error_text += f"💡 *Tip:* Try again in a few moments\\!"

    try:
        await q.edit_message_text(
            error_text,
            parse_mode="MarkdownV2",
            reply_markup=back_keyboard
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.error(f"Error updating message: {e}")


async def _show_no_languages(q, repo, keyboard):
    """Show message when no language data is found"""
    repo_escaped = escape_markdown(repo, 2)
    text = f"💻 *{repo_escaped} Languages*\n\n"
    text += f"❌ *No Language Data Available*\n\n"
    text += f"No programming language data found for this repository\\.\n\n"
    text += f"*Possible reasons:*\n"
    text += f"• Empty repository\n"
    text += f"• Files not yet analyzed by GitHub\n"
    text += f"• Repository contains only data files\n"
    text += f"• Language detection failed\n\n"
    text += f"💡 *Tip:* Try again later as GitHub may still be analyzing\\!"

    try:
        await q.edit_message_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.error(f"Error updating message: {e}")


async def _show_languages_error(q, repo, error_type, keyboard):
    """Show languages error with structured message"""
    repo_escaped = escape_markdown(repo, 2)
    error_text = f"💻 *{repo_escaped} Languages*\n\n"
    error_text += f"❌ *{escape_markdown(error_type, 2)}*\n\n"

    if error_type == "Fetch Error":
        error_text += f"Unable to fetch language information\\.\n\n"
        error_text += f"*Possible causes:*\n"
        error_text += f"• Network connection issue\n"
        error_text += f"• GitHub API temporarily unavailable\n"
        error_text += f"• Repository access restrictions\n"
        error_text += f"• Language data not yet processed\n\n"
        error_text += f"💡 *Tip:* Try again in a few moments\\!"
    else:
        error_text += f"An error occurred while loading languages\\.\n\n"
        error_text += f"💡 *Tip:* Please try again\\!"

    try:
        await q.edit_message_text(
            error_text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.error(f"Error updating message: {e}")
