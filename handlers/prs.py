import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from utils.git_api import fetch_open_prs

async def handle_prs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    repo = context.user_data.get("current_repo")
    if not repo:
        await q.edit_message_text("❌ _No repo selected\\. Send me a repository first\\._", parse_mode="MarkdownV2")
        return

    # Loading state - FIX: Properly escape dots
    await q.edit_message_text("⏳ *Fetching pull requests\\.\\.\\.*", parse_mode="MarkdownV2")

    async with aiohttp.ClientSession() as session:
        prs = await fetch_open_prs(session, repo)

    # Add back button
    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")]
    ])

    if not prs:
        await q.edit_message_text(
            f"✅ _No open pull requests in_ `{escape_markdown(repo, 2)}`",
            parse_mode="MarkdownV2",
            reply_markup=back_keyboard
        )
        return

    repo_name = escape_markdown(repo, 2)
    text = f"🔀 *Open Pull Requests in* __{repo_name}__:\n\n"

    for i, pr in enumerate(prs[:5], 1):
        title = escape_markdown(pr['title'][:50] + ("..." if len(pr['title']) > 50 else ""), 2)
        number = pr['number']
        user = escape_markdown(pr['user']['login'], 2)
        pr_url = pr['html_url']

        # Calculate time ago
        from datetime import datetime
        created = pr['created_at']
        created_date = datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ")
        time_diff = datetime.utcnow() - created_date

        if time_diff.days > 0:
            time_ago = f"{time_diff.days}d ago"
        elif time_diff.seconds > 3600:
            time_ago = f"{time_diff.seconds // 3600}h ago"
        else:
            time_ago = f"{time_diff.seconds // 60}m ago"

        # FIX: Properly escape the hash symbol and dots
        text += f"{i}\\. [\\#{number}]({pr_url}): {title}\n"
        text += f"   👤 by {user} • 📅 _{escape_markdown(time_ago, 2)}_\n\n"

    await q.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        disable_web_page_preview=True,
        reply_markup=back_keyboard
    )
