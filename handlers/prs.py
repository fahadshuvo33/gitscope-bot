import aiohttp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from utils.git_api import fetch_open_prs

# Import the loading system
from utils.loading import show_loading, show_static_loading

async def handle_prs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pull requests display with loading animation"""
    q = update.callback_query
    await q.answer()

    repo = context.user_data.get("current_repo")
    if not repo:
        await q.edit_message_text("❌ _No repo selected\\. Send me a repository first\\._", parse_mode="MarkdownV2")
        return

    # Show static loading first to preserve the window
    await show_static_loading(
        q.message,
        f"🔀 **{repo} Pull Requests**",
        "Loading pull requests",
        preserve_content=True,
        animation_type="wave",  # Wave animation for pull requests (merging flows)
    )

    # Start animated loading
    loading_task = await show_loading(
        q.message,
        f"🔀 **{repo} Pull Requests**",
        "Loading pull requests",
        animation_type="wave",
    )

    try:
        async with aiohttp.ClientSession() as session:
            prs = await fetch_open_prs(session, repo)

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
                InlineKeyboardButton("🔄 Refresh", callback_data="prs"),
                InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")
            ]
        ])

        if not prs:
            await _show_no_prs(q.message, repo, back_keyboard)
            return

        # Build and display pull requests content
        text = _build_prs_content(prs, repo)

        await q.edit_message_text(
            text,
            parse_mode="MarkdownV2",
            disable_web_page_preview=True,
            reply_markup=back_keyboard
        )

    except Exception as e:
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
                InlineKeyboardButton("🔄 Try Again", callback_data="prs"),
                InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")
            ]
        ])

        await _show_prs_error(q.message, repo, "Fetch Error", back_keyboard)


def _build_prs_content(prs, repo):
    """Build the pull requests content with enhanced formatting"""
    repo_name = escape_markdown(repo, 2)
    text = f"🔀 *Open Pull Requests in* __{repo_name}__\n\n"

    # Add summary info
    total_shown = min(len(prs), 5)
    text += f"🔥 **{total_shown} Recent Pull Requests:**\n\n"

    try:
        for i, pr in enumerate(prs[:5], 1):
            # Safely get PR data
            raw_title = pr.get('title', 'No title')
            if len(raw_title) > 45:  # Shortened for better display
                raw_title = raw_title[:45] + "..."
            title = escape_markdown(raw_title, 2)

            number = pr.get('number', 0)
            pr_url = pr.get('html_url', '')

            # Get user info safely
            user_data = pr.get('user', {})
            if user_data:
                user_login = user_data.get('login', 'Unknown')
                user = escape_markdown(user_login, 2)
            else:
                user = "Unknown"

            # Calculate time ago
            time_ago = _calculate_time_ago(pr.get('created_at', ''))
            time_ago_escaped = escape_markdown(time_ago, 2)

            # Get PR status indicators
            status_info = _get_pr_status(pr)

            # Add PR to text with better formatting
            if pr_url:
                text += f"{i}\\. [\\#{number}]({pr_url}){status_info}\n"
            else:
                text += f"{i}\\. \\#{number}{status_info}\n"

            text += f"   📝 _{title}_\n"
            text += f"   👤 {user} • ⏰ {time_ago_escaped}\n\n"

        # Add summary if more PRs exist
        if len(prs) > 5:
            text += f"📊 _{total_shown} of {len(prs)} total open pull requests shown_\n\n"

        text += f"💡 **Tip:** Click on PR numbers to view them on GitHub!"

    except Exception as e:
        # Fallback formatting if there's an error
        text += f"❌ _Error formatting pull requests data_\n\n"
        text += f"📊 _{len(prs)} open pull requests found_"

    return text


def _calculate_time_ago(created_at):
    """Calculate human-readable time ago from creation date"""
    try:
        from datetime import datetime
        if not created_at:
            return "unknown time"

        created_date = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
        time_diff = datetime.utcnow() - created_date

        if time_diff.days > 365:
            return f"{time_diff.days // 365}y ago"
        elif time_diff.days > 30:
            return f"{time_diff.days // 30}mo ago"
        elif time_diff.days > 0:
            return f"{time_diff.days}d ago"
        elif time_diff.seconds > 3600:
            return f"{time_diff.seconds // 3600}h ago"
        elif time_diff.seconds > 60:
            return f"{time_diff.seconds // 60}m ago"
        else:
            return "just now"
    except Exception:
        return "unknown time"


def _get_pr_status(pr):
    """Get PR status indicators"""
    try:
        # Check if PR is draft
        if pr.get('draft', False):
            return " 🚧"

        # Check for review status (if available)
        # This would require additional API calls, so we'll keep it simple for now
        return ""

    except Exception:
        return ""


async def _show_no_prs(message, repo, keyboard):
    """Show message when no pull requests are found"""
    repo_escaped = escape_markdown(repo, 2)
    text = f"🔀 **{repo} Pull Requests**\n\n"
    text += f"✅ **No Open Pull Requests**\n\n"
    text += f"Great news! This repository has no open pull requests\\.\n\n"
    text += f"**This could mean:**\n"
    text += f"• All PRs are reviewed and merged quickly\n"
    text += f"• Well\\-maintained project workflow\n"
    text += f"• Active maintainer community\n"
    text += f"• Stable development phase\n\n"
    text += f"💡 **Tip:** This is usually a good sign for project health!"

    try:
        await message.edit_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )
    except Exception:
        # Fallback to simpler message
        await message.edit_text(
            f"✅ _No open pull requests in_ `{repo_escaped}`",
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )


async def _show_prs_error(message, repo, error_type, keyboard):
    """Show pull requests error with structured message"""
    error_text = f"🔀 **{repo} Pull Requests**\n\n"
    error_text += f"❌ **{error_type}**\n\n"

    if error_type == "Fetch Error":
        error_text += f"Unable to fetch pull requests information\\.\n\n"
        error_text += f"**Possible causes:**\n"
        error_text += f"• Network connection issue\n"
        error_text += f"• GitHub API temporarily unavailable\n"
        error_text += f"• Repository access restrictions\n"
        error_text += f"• Rate limit exceeded\n\n"
        error_text += f"💡 **Tip:** Try again in a few moments!"
    else:
        error_text += f"An error occurred while loading pull requests\\.\n\n"
        error_text += f"💡 **Tip:** Please try again!"

    try:
        await message.edit_text(
            error_text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )
    except Exception:
        # Fallback to simple error message
        await message.edit_text(
            "❌ Error fetching pull requests\\. Please try again\\.",
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )
