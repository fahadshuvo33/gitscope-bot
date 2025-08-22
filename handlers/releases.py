import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from utils.git_api import fetch_releases

async def handle_releases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    repo = context.user_data.get("current_repo")
    if not repo:
        await q.edit_message_text("❌ _No repo selected\\. Send me a repository first\\._", parse_mode="MarkdownV2")
        return

    # Loading state - FIX: Properly escape dots
    await q.edit_message_text("⏳ *Fetching releases\\.\\.\\.*", parse_mode="MarkdownV2")

    async with aiohttp.ClientSession() as session:
        releases = await fetch_releases(session, repo)

    # Add back button
    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")]
    ])

    if not releases:
        await q.edit_message_text(
            f"❌ _No releases found for_ `{escape_markdown(repo, 2)}`",
            parse_mode="MarkdownV2",
            reply_markup=back_keyboard
        )
        return

    repo_name = escape_markdown(repo, 2)
    text = f"🏷️ *Latest Releases of* __{repo_name}__:\n\n"

    for i, release in enumerate(releases[:3], 1):
        tag_name = escape_markdown(release.get('tag_name', 'No tag'), 2)
        name = escape_markdown(release.get('name') or release.get('tag_name', 'Unnamed'), 2)
        is_prerelease = release.get('prerelease', False)
        release_url = release['html_url']

        # Calculate time ago
        from datetime import datetime
        published = release.get('published_at')
        if published:
            published_date = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
            time_diff = datetime.utcnow() - published_date

            if time_diff.days > 365:
                time_ago = f"{time_diff.days // 365}y ago"
            elif time_diff.days > 30:
                time_ago = f"{time_diff.days // 30}mo ago"
            elif time_diff.days > 0:
                time_ago = f"{time_diff.days}d ago"
            elif time_diff.seconds > 3600:
                time_ago = f"{time_diff.seconds // 3600}h ago"
            else:
                time_ago = f"{time_diff.seconds // 60}m ago"
        else:
            time_ago = "Unknown"

        # Status indicator
        status = "🔴 Pre\\-release" if is_prerelease else "🟢 Stable"

        text += f"{i}\\. [{name}]({release_url}) `{tag_name}`\n"
        text += f"   {status} • 📅 _{escape_markdown(time_ago, 2)}_\n"

        # Add download count if available
        assets = release.get('assets', [])
        if assets:
            total_downloads = sum(asset.get('download_count', 0) for asset in assets)
            if total_downloads > 0:
                text += f"   📥 _{total_downloads:,} downloads_\n"

        text += "\n"

    await q.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        disable_web_page_preview=True,
        reply_markup=back_keyboard
    )
