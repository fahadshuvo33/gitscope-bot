import aiohttp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from utils.git_api import fetch_open_issues

# Import the loading system
from utils.loading import show_loading, show_static_loading

async def handle_issues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle issues display with loading animation"""
    q = update.callback_query
    await q.answer()

    repo = context.user_data.get("current_repo")
    if not repo:
        await q.edit_message_text("❌ No repo selected\\. Send me a repository first\\.", parse_mode="MarkdownV2")
        return

    # Show static loading first to preserve the window
    await show_static_loading(
        q.message,
        f"🐛 **{repo} Issues**",
        "Loading open issues",
        preserve_content=True,
        animation_type="pulse",  # Pulse animation for issues
    )

    # Start animated loading
    loading_task = await show_loading(
        q.message,
        f"🐛 **{repo} Issues**",
        "Loading open issues",
        animation_type="pulse",
    )

    try:
        # Add timeout to prevent hanging
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            issues = await asyncio.wait_for(
                fetch_open_issues(session, repo),
                timeout=8.0  # 8 second timeout
            )

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
                InlineKeyboardButton("🔄 Refresh", callback_data="issues"),
                InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")
            ]
        ])

        if not issues:
            await _show_no_issues(q.message, repo, back_keyboard)
            return

        # Filter out pull requests (they appear in issues API too)
        actual_issues = [issue for issue in issues if 'pull_request' not in issue]

        if not actual_issues:
            await _show_no_issues(q.message, repo, back_keyboard)
            return

        # Build and display issues content
        text = _build_issues_content(actual_issues, repo)

        await q.edit_message_text(
            text,
            parse_mode="MarkdownV2",
            disable_web_page_preview=True,
            reply_markup=back_keyboard
        )

    except asyncio.TimeoutError:
        # Stop loading animation gracefully
        if loading_task and not loading_task.done():
            loading_task.cancel()
            try:
                await loading_task
            except asyncio.CancelledError:
                pass

        back_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 Try Again", callback_data="issues"),
                InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")
            ]
        ])

        await _show_issues_error(q.message, repo, "Request Timeout", back_keyboard)

    except Exception as e:
        # Stop loading animation gracefully
        if loading_task and not loading_task.done():
            loading_task.cancel()
            try:
                await loading_task
            except asyncio.CancelledError:
                pass

        back_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 Try Again", callback_data="issues"),
                InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")
            ]
        ])

        await _show_issues_error(q.message, repo, "Fetch Error", back_keyboard)


def _build_issues_content(issues, repo):
    """Build the issues content with proper formatting"""
    repo_name = escape_markdown(repo, 2)
    text = f"🐛 *Open Issues in* `{repo_name}`\n\n"

    # Add summary info
    total_shown = min(len(issues), 5)
    text += f"🔥 **Showing {total_shown} Recent Issues:**\n\n"

    try:
        for i, issue in enumerate(issues[:5], 1):
            # Safely get title
            raw_title = issue.get('title', 'No title')
            if len(raw_title) > 50:  # Shortened for better display
                raw_title = raw_title[:50] + "..."
            title = escape_markdown(raw_title, 2)

            number = issue.get('number', 0)
            issue_url = issue.get('html_url', '')

            # Get user safely
            user_data = issue.get('user', {})
            if user_data:
                user_login = user_data.get('login', 'Unknown')
                user = escape_markdown(user_login, 2)
            else:
                user = "Unknown"

            # Calculate time ago
            time_ago = _calculate_time_ago(issue.get('created_at', ''))
            time_ago_escaped = escape_markdown(time_ago, 2)

            # Add issue to text with better formatting
            if issue_url:
                text += f"{i}\\. [\\#{number}]({issue_url})\n"
            else:
                text += f"{i}\\. \\#{number}\n"

            text += f"   📝 _{title}_\n"
            text += f"   👤 {user} • ⏰ {time_ago_escaped}\n\n"

        # Add summary if more issues exist
        if len(issues) > 5:
            text += f"📊 _{total_shown} of {len(issues)} total open issues shown_\n\n"

        text += f"💡 **Tip:** Click on issue numbers to view them on GitHub!"

    except Exception as e:
        # Fallback formatting if there's an error
        text += f"❌ _Error formatting issues data_\n\n"
        text += f"📊 _{len(issues)} open issues found_"

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


async def _show_no_issues(message, repo, keyboard):
    """Show message when no issues are found"""
    repo_escaped = escape_markdown(repo, 2)
    text = f"🐛 **{repo} Issues**\n\n"
    text += f"✅ **No Open Issues Found**\n\n"
    text += f"Great news! This repository has no open issues\\.\n\n"
    text += f"**This could mean:**\n"
    text += f"• Well\\-maintained project\n"
    text += f"• Issues are resolved quickly\n"
    text += f"• Community uses other channels\n"
    text += f"• Very stable codebase\n\n"
    text += f"💡 **Tip:** Check back later for new issues!"

    try:
        await message.edit_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )
    except Exception:
        # Fallback to simpler message
        await message.edit_text(
            f"✅ No open issues in `{repo_escaped}`",
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )


async def _show_issues_error(message, repo, error_type, keyboard):
    """Show issues error with structured message"""
    error_text = f"🐛 **{repo} Issues**\n\n"
    error_text += f"❌ **{error_type}**\n\n"

    if error_type == "Request Timeout":
        error_text += f"Request timed out while fetching issues\\.\n\n"
        error_text += f"**Possible causes:**\n"
        error_text += f"• Slow network connection\n"
        error_text += f"• GitHub API responding slowly\n"
        error_text += f"• Large repository with many issues\n\n"
        error_text += f"💡 **Tip:** Try again with a better connection!"
    else:
        error_text += f"Unable to fetch issues information\\.\n\n"
        error_text += f"**Possible causes:**\n"
        error_text += f"• Network connection issue\n"
        error_text += f"• GitHub API temporarily unavailable\n"
        error_text += f"• Repository access restrictions\n\n"
        error_text += f"💡 **Tip:** Try again in a few moments!"

    try:
        await message.edit_text(
            error_text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )
    except Exception:
        # Fallback to simple error message
        await message.edit_text(
            "❌ Error fetching issues\\. Please try again\\.",
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )
