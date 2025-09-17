import aiohttp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from utils.git_api import fetch_contributors

# Import the loading system
from utils.loading import show_loading, show_static_loading

async def handle_contributors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle contributors display with loading animation"""
    q = update.callback_query
    await q.answer()

    repo = context.user_data.get("current_repo")
    if not repo:
        await q.edit_message_text("❌ _No repo selected\\. Send me a repository first\\._", parse_mode="MarkdownV2")
        return

    # Show static loading first to preserve the window
    await show_static_loading(
        q.message,
        f"👥 **{escape_markdown(repo, 2)} Contributors**",  # FIXED: Escaped repo name
        "Loading contributors",
        preserve_content=True,
        animation_type="heart",  # Heart animation for contributors
    )

    # Start animated loading
    loading_task = await show_loading(
        q.message,
        f"👥 **{escape_markdown(repo, 2)} Contributors**",  # FIXED: Escaped repo name
        "Loading contributors",
        animation_type="heart",
    )

    try:
        async with aiohttp.ClientSession() as session:
            contributors = await fetch_contributors(session, repo)

        # Stop loading animation gracefully
        if loading_task and not loading_task.done():
            loading_task.cancel()
            try:
                await loading_task
            except asyncio.CancelledError:
                pass

        # Create back button
        back_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="contributors"),
                InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")
            ]
        ])

        if not contributors:
            await _show_contributors_error(q, repo, "No Contributors Found", back_keyboard)
            return

        # Build and display contributors content
        text = _build_contributors_content(contributors, repo)

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
                InlineKeyboardButton("🔄 Try Again", callback_data="contributors"),
                InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")
            ]
        ])

        await _show_contributors_error(q, repo, "Fetch Error", back_keyboard)


def _build_contributors_content(contributors, repo):
    """Build the contributors content"""
    repo_name = escape_markdown(repo, 2)
    text = f"👥 *Top Contributors of* __{repo_name}__\n\n"

    # Add helpful tip
    text += f"🔥 *Top {min(len(contributors), 5)} Contributors:*\n\n"

    for i, c in enumerate(contributors[:5], 1):
        login = escape_markdown(c['login'], 2)
        contributions = c['contributions']

        # Format contributions count
        if contributions >= 1000:
            contrib_fmt = f"{contributions/1000:.1f}k"
        else:
            contrib_fmt = str(contributions)

        # FIXED: Escape the formatted contributions (might contain dots)
        contrib_fmt_escaped = escape_markdown(contrib_fmt, 2)

        # FIXED: Properly escape URL for MarkdownV2
        url = c['html_url'].replace(')', '\\)').replace('(', '\\(')

        text += f"{i}\\. [{login}]({url}) — _{contrib_fmt_escaped} contributions_\n"

    # Add summary info if more contributors exist
    if len(contributors) > 5:
        text += f"\n📊 _Showing top 5 of {len(contributors)} total contributors_"

    text += f"\n\n💡 *Tip:* Click on usernames to view their GitHub profiles\\!"

    return text


async def _show_contributors_error(q, repo, error_type, keyboard):
    """Show contributors error with structured message"""
    repo_escaped = escape_markdown(repo, 2)
    error_text = f"👥 *{repo_escaped} Contributors*\n\n"
    error_text += f"❌ *{escape_markdown(error_type, 2)}*\n\n"

    if error_type == "No Contributors Found":
        error_text += f"No contributors found for this repository\\.\n\n"
        error_text += f"*Possible causes:*\n"
        error_text += f"• Repository is very new\n"
        error_text += f"• Repository has no commits\n"
        error_text += f"• Contributors data not available\n\n"
        error_text += f"💡 *Tip:* Try refreshing or check back later\\!"
    else:
        error_text += f"Unable to fetch contributors information\\.\n\n"
        error_text += f"*Possible causes:*\n"
        error_text += f"• Network connection issue\n"
        error_text += f"• GitHub API temporarily unavailable\n"
        error_text += f"• Repository access restrictions\n\n"
        error_text += f"💡 *Tip:* Try again in a few moments\\!"

    try:
        await q.edit_message_text(
            error_text,
            parse_mode="MarkdownV2",  # FIXED: Changed from "Markdown" to "MarkdownV2"
            reply_markup=keyboard
        )
    except Exception:
        # Fallback to simple error message
        await q.edit_message_text(
            "❌ Error fetching contributors\\. Please try again\\.",
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )
