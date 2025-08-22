import aiohttp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from utils.git_api import fetch_open_issues

async def handle_issues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    repo = context.user_data.get("current_repo")
    if not repo:
        await q.edit_message_text("❌ No repo selected\\. Send me a repository first\\.", parse_mode="MarkdownV2")
        return

    # Loading state with simpler text
    try:
        await q.edit_message_text("⏳ Loading issues\\.\\.\\.", parse_mode="MarkdownV2")
    except Exception as e:
        print(f"Error updating loading message: {e}")
        return

    try:
        # Add timeout to prevent hanging
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            issues = await asyncio.wait_for(
                fetch_open_issues(session, repo),
                timeout=8.0  # 8 second timeout
            )
    except asyncio.TimeoutError:
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")]
        ])
        await q.edit_message_text(
            "⏰ Request timed out\\. Please try again\\.",
            parse_mode="MarkdownV2",
            reply_markup=back_keyboard
        )
        return
    except Exception as e:
        print(f"Error fetching issues: {e}")
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")]
        ])
        await q.edit_message_text(
            "❌ Error fetching issues\\. Please try again\\.",
            parse_mode="MarkdownV2",
            reply_markup=back_keyboard
        )
        return

    # Add back button
    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")]
    ])

    if not issues:
        repo_escaped = escape_markdown(repo, 2)
        await q.edit_message_text(
            f"✅ No open issues in `{repo_escaped}`",
            parse_mode="MarkdownV2",
            reply_markup=back_keyboard
        )
        return

    # Filter out pull requests (they appear in issues API too)
    actual_issues = [issue for issue in issues if 'pull_request' not in issue]

    if not actual_issues:
        repo_escaped = escape_markdown(repo, 2)
        await q.edit_message_text(
            f"✅ No open issues in `{repo_escaped}`",
            parse_mode="MarkdownV2",
            reply_markup=back_keyboard
        )
        return

    # Build response
    repo_name = escape_markdown(repo, 2)
    text = f"🐛 *Open Issues in* `{repo_name}`:\n\n"

    try:
        for i, issue in enumerate(actual_issues[:5], 1):
            # Safely get title
            raw_title = issue.get('title', 'No title')
            if len(raw_title) > 60:
                raw_title = raw_title[:60] + "..."
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
            try:
                from datetime import datetime
                created = issue.get('created_at', '')
                if created:
                    created_date = datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ")
                    time_diff = datetime.utcnow() - created_date

                    if time_diff.days > 30:
                        time_ago = f"{time_diff.days // 30}mo ago"
                    elif time_diff.days > 0:
                        time_ago = f"{time_diff.days}d ago"
                    elif time_diff.seconds > 3600:
                        time_ago = f"{time_diff.seconds // 3600}h ago"
                    else:
                        time_ago = f"{time_diff.seconds // 60}m ago"
                else:
                    time_ago = "unknown"
            except:
                time_ago = "unknown"

            time_ago_escaped = escape_markdown(time_ago, 2)

            # Add issue to text
            if issue_url:
                text += f"{i}\\. [\\#{number}]({issue_url})\n"
            else:
                text += f"{i}\\. \\#{number}\n"

            text += f"   📝 {title}\n"
            text += f"   👤 {user} • ⏰ {time_ago_escaped}\n\n"

    except Exception as e:
        print(f"Error formatting issues: {e}")
        await q.edit_message_text(
            "❌ Error formatting issues data\\.",
            parse_mode="MarkdownV2",
            reply_markup=back_keyboard
        )
        return

    try:
        await q.edit_message_text(
            text,
            parse_mode="MarkdownV2",
            disable_web_page_preview=True,
            reply_markup=back_keyboard
        )
    except Exception as e:
        print(f"Error sending final message: {e}")
        # Fallback to plain text
        plain_text = text.replace('\\', '').replace('*', '').replace('_', '').replace('`', '')
        await q.edit_message_text(
            plain_text,
            parse_mode=None,
            disable_web_page_preview=True,
            reply_markup=back_keyboard
        )
