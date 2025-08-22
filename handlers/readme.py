import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from utils.git_api import fetch_readme

async def handle_readme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    repo = context.user_data.get("current_repo")
    if not repo:
        await query.edit_message_text("❌ _No repo selected\\. Send me a repository first\\._", parse_mode="MarkdownV2")
        return

    # Show loading state
    await query.edit_message_text("⏳ *Fetching README\\.\\.\\.*", parse_mode="MarkdownV2")

    async with aiohttp.ClientSession() as session:
        text = await fetch_readme(session, repo)

    # Add back button
    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")]
    ])

    if not text:
        await query.edit_message_text(
            f"❌ _README not found for_ `{escape_markdown(repo, 2)}`",
            parse_mode="MarkdownV2",
            reply_markup=back_keyboard
        )
        return

    # Clean and limit the README content
    lines = text.split('\n')

    # Remove markdown formatting that conflicts with MarkdownV2
    cleaned_lines = []
    for line in lines[:30]:  # Limit to first 30 lines
        # Remove images, complex markdown
        if line.startswith('![') or line.startswith('<img'):
            continue
        if line.startswith('---') or line.startswith('==='):
            continue
        cleaned_lines.append(line)

    preview = '\n'.join(cleaned_lines)

    # Further limit if still too long
    if len(preview) > 2500:
        preview = preview[:2500] + "..."

    # Escape for MarkdownV2
    preview_escaped = escape_markdown(preview, 2)
    repo_escaped = escape_markdown(repo, 2)

    formatted = f"📖 *README Preview for* __{repo_escaped}__:\n\n```\n{preview_escaped}\n```\n\n_\$Showing preview only\$_"

    await query.edit_message_text(
        formatted,
        parse_mode="MarkdownV2",
        reply_markup=back_keyboard
    )
