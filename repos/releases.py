import aiohttp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from utils.git_api import fetch_releases

# Import the loading system
from utils.loading import show_loading, show_static_loading

async def handle_releases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle releases display with loading animation"""
    q = update.callback_query
    await q.answer()

    repo = context.user_data.get("current_repo")
    if not repo:
        await q.edit_message_text("❌ _No repo selected\\. Send me a repository first\\._", parse_mode="MarkdownV2")
        return

    # Show static loading first to preserve the window
    await show_static_loading(
        q.message,
        f"🏷️ **{repo} Releases**",
        "Loading releases",
        preserve_content=True,
        animation_type="rocket",  # Rocket animation for releases (launches/versions)
    )

    # Start animated loading
    loading_task = await show_loading(
        q.message,
        f"🏷️ **{repo} Releases**",
        "Loading releases",
        animation_type="rocket",
    )

    try:
        async with aiohttp.ClientSession() as session:
            releases = await fetch_releases(session, repo)

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
                InlineKeyboardButton("🔄 Refresh", callback_data="releases"),
                InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")
            ]
        ])

        if not releases:
            await _show_no_releases(q.message, repo, back_keyboard)
            return

        # Build and display releases content
        text = _build_releases_content(releases, repo)

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
                InlineKeyboardButton("🔄 Try Again", callback_data="releases"),
                InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")
            ]
        ])

        await _show_releases_error(q.message, repo, "Fetch Error", back_keyboard)


def _build_releases_content(releases, repo):
    """Build the releases content with enhanced formatting"""
    repo_name = escape_markdown(repo, 2)
    text = f"🏷️ *Latest Releases of* __{repo_name}__\n\n"

    # Add summary info
    total_shown = min(len(releases), 5)  # Show up to 5 releases
    text += f"🚀 **{total_shown} Most Recent Releases:**\n\n"

    try:
        for i, release in enumerate(releases[:5], 1):
            # Safely get release data
            tag_name = release.get('tag_name', 'No tag')
            raw_name = release.get('name') or release.get('tag_name', 'Unnamed Release')

            # Truncate long release names
            if len(raw_name) > 40:
                raw_name = raw_name[:40] + "..."

            name = escape_markdown(raw_name, 2)
            tag_escaped = escape_markdown(tag_name, 2)

            is_prerelease = release.get('prerelease', False)
            is_draft = release.get('draft', False)
            release_url = release.get('html_url', '')

            # Calculate time ago
            time_ago = _calculate_time_ago(release.get('published_at', ''))
            time_ago_escaped = escape_markdown(time_ago, 2)

            # Enhanced status indicators
            status_info = _get_release_status(is_prerelease, is_draft)

            # Add release to text with better formatting
            if release_url:
                text += f"{i}\\. [{name}]({release_url})\n"
            else:
                text += f"{i}\\. {name}\n"

            text += f"   🏷️ `{tag_escaped}` {status_info}\n"
            text += f"   📅 {time_ago_escaped}"

            # Add download information if available
            download_info = _get_download_info(release)
            if download_info:
                text += f" • {download_info}"

            text += "\n\n"

        # Add summary if more releases exist
        if len(releases) > 5:
            text += f"📊 _{total_shown} of {len(releases)} total releases shown_\n\n"

        text += f"💡 **Tip:** Click on release names to view full details and downloads!"

    except Exception as e:
        # Fallback formatting if there's an error
        text += f"❌ _Error formatting releases data_\n\n"
        text += f"📊 _{len(releases)} releases found_"

    return text


def _calculate_time_ago(published_at):
    """Calculate human-readable time ago from publication date"""
    try:
        from datetime import datetime
        if not published_at:
            return "unknown time"

        published_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
        time_diff = datetime.utcnow() - published_date

        if time_diff.days > 365:
            years = time_diff.days // 365
            return f"{years}y ago"
        elif time_diff.days > 30:
            months = time_diff.days // 30
            return f"{months}mo ago"
        elif time_diff.days > 0:
            return f"{time_diff.days}d ago"
        elif time_diff.seconds > 3600:
            hours = time_diff.seconds // 3600
            return f"{hours}h ago"
        elif time_diff.seconds > 60:
            minutes = time_diff.seconds // 60
            return f"{minutes}m ago"
        else:
            return "just released"
    except Exception:
        return "unknown time"


def _get_release_status(is_prerelease, is_draft):
    """Get release status indicators"""
    if is_draft:
        return "🟡 Draft"
    elif is_prerelease:
        return "🔴 Pre\\-release"
    else:
        return "🟢 Stable"


def _get_download_info(release):
    """Get download information for release"""
    try:
        assets = release.get('assets', [])
        if not assets:
            return None

        total_downloads = sum(asset.get('download_count', 0) for asset in assets)
        if total_downloads == 0:
            return f"📦 {len(assets)} assets"
        elif total_downloads >= 1000000:
            return f"📥 {total_downloads/1000000:.1f}M downloads"
        elif total_downloads >= 1000:
            return f"📥 {total_downloads/1000:.1f}K downloads"
        else:
            return f"📥 {total_downloads:,} downloads"
    except Exception:
        return None


async def _show_no_releases(message, repo, keyboard):
    """Show message when no releases are found"""
    repo_escaped = escape_markdown(repo, 2)
    text = f"🏷️ **{repo} Releases**\n\n"
    text += f"❌ **No Releases Found**\n\n"
    text += f"This repository doesn't have any releases yet\\.\n\n"
    text += f"**What are releases\\?**\n"
    text += f"• Tagged versions of the code\n"
    text += f"• Packaged downloads for users\n"
    text += f"• Release notes and changelogs\n"
    text += f"• Stable snapshots of the project\n\n"
    text += f"💡 **Tip:** Developers may still be working on the first release!"

    try:
        await message.edit_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )
    except Exception:
        # Fallback to simpler message
        await message.edit_text(
            f"❌ _No releases found for_ `{repo_escaped}`",
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )


async def _show_releases_error(message, repo, error_type, keyboard):
    """Show releases error with structured message"""
    error_text = f"🏷️ **{repo} Releases**\n\n"
    error_text += f"❌ **{error_type}**\n\n"

    if error_type == "Fetch Error":
        error_text += f"Unable to fetch releases information\\.\n\n"
        error_text += f"**Possible causes:**\n"
        error_text += f"• Network connection issue\n"
        error_text += f"• GitHub API temporarily unavailable\n"
        error_text += f"• Repository access restrictions\n"
        error_text += f"• Rate limit exceeded\n\n"
        error_text += f"💡 **Tip:** Try again in a few moments!"
    else:
        error_text += f"An error occurred while loading releases\\.\n\n"
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
            "❌ Error fetching releases\\. Please try again\\.",
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )
