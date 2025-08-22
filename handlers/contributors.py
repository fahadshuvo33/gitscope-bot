import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from utils.git_api import fetch_contributors

async def handle_contributors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    repo = context.user_data.get("current_repo")
    if not repo:
        await q.edit_message_text("❌ _No repo selected\\. Send me a repository first\\._", parse_mode="MarkdownV2")
        return

    # Loading state - FIX: Properly escape dots
    await q.edit_message_text("⏳ *Fetching contributors\\.\\.\\.*", parse_mode="MarkdownV2")

    async with aiohttp.ClientSession() as session:
        contributors = await fetch_contributors(session, repo)

    # Add back button
    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")]
    ])

    if not contributors:
        await q.edit_message_text(
            "❌ _No contributors found\\._",
            parse_mode="MarkdownV2",
            reply_markup=back_keyboard
        )
        return

    repo_name = escape_markdown(repo, 2)
    text = f"👥 *Top Contributors of* __{repo_name}__:\n\n"

    for i, c in enumerate(contributors[:5], 1):
        login = escape_markdown(c['login'], 2)
        contributions = c['contributions']
        text += f"{i}\\. [{login}]({c['html_url']}) — _{contributions} contributions_\n"

    await q.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        disable_web_page_preview=True,
        reply_markup=back_keyboard
    )
