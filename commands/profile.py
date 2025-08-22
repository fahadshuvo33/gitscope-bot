from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import aiohttp
import asyncio

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /user or /profile command"""

    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a GitHub username\\!\n\n"
            "**Usage:** `/user username`\n"
            "**Example:** `/user octocat`",
            parse_mode="MarkdownV2"
        )
        return

    username = context.args[0].replace('@', '')  # Remove @ if present

    if not username:
        await update.message.reply_text(
            "❌ Please provide a valid username\\!",
            parse_mode="MarkdownV2"
        )
        return

    loading_msg = await update.message.reply_text(
        f"🔄 *Loading profile for {username}\\.\\.\\.*",
        parse_mode="MarkdownV2"
    )

    try:
        from utils.git_api import fetch_user_info

        async with aiohttp.ClientSession() as session:
            user_data = await fetch_user_info(session, username)

        if not user_data:
            await loading_msg.edit_text(
                f"❌ User `{username}` not found\\!\n\nPlease check the username and try again\\.",
                parse_mode="MarkdownV2"
            )
            return

        # Format user profile
        await show_user_profile(loading_msg, user_data, context)

    except Exception as e:
        await loading_msg.edit_text(
            f"❌ Error fetching user profile: {str(e)}",
            parse_mode=None
        )

async def show_user_profile(message, user_data, context):
    """Display user profile information"""
    from telegram.helpers import escape_markdown

    # Store user data
    context.user_data["current_user"] = user_data.get('login', '')

    # Get user info safely
    name = user_data.get('name') or user_data.get('login', 'Unknown')
    username = user_data.get('login', 'Unknown')
    bio = user_data.get('bio', 'No bio available')
    company = user_data.get('company', 'Not specified')
    location = user_data.get('location', 'Not specified')
    blog = user_data.get('blog', '')

    public_repos = user_data.get('public_repos', 0)
    followers = user_data.get('followers', 0)
    following = user_data.get('following', 0)

    created_at = user_data.get('created_at', '')
    if created_at:
        from datetime import datetime
        created_date = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
        joined = created_date.strftime("%B %Y")
    else:
        joined = "Unknown"

    # Escape text for MarkdownV2
    name_escaped = escape_markdown(name, 2)
    username_escaped = escape_markdown(username, 2)
    bio_escaped = escape_markdown(bio[:100] + ("..." if len(bio) > 100 else ""), 2)
    company_escaped = escape_markdown(company, 2)
    location_escaped = escape_markdown(location, 2)

    # Build profile text
    profile_text = (
        f"👤 *GitHub User Profile*\n\n"
        f"🏷️ **{name_escaped}** \$@{username_escaped}\$\n\n"
        f"📝 _{bio_escaped}_\n\n"

        f"📊 **Statistics:**\n"
        f"📂 {public_repos} public repositories\n"
        f"👥 {followers} followers • {following} following\n"
        f"📅 Joined {joined}\n\n"

        f"ℹ️ **Details:**\n"
        f"🏢 Company: {company_escaped}\n"
        f"📍 Location: {location_escaped}\n"
    )

    if blog and blog.strip():
        blog_escaped = escape_markdown(blog, 2)
        if not blog.startswith(('http://', 'https://')):
            blog = f"https://{blog}"
        profile_text += f"🌐 Website: [{blog_escaped}]({blog})\n"

    profile_text += f"\n🔗 [View on GitHub](https://github.com/{username})"

    # Create keyboard with user actions
    keyboard = [
        [
            InlineKeyboardButton("📂 Repositories", callback_data=f"user_repos_{username}"),
            InlineKeyboardButton("⭐ Starred Repos", callback_data=f"user_starred_{username}")
        ],
        [
            InlineKeyboardButton("👥 Followers", callback_data=f"user_followers_{username}"),
            InlineKeyboardButton("👤 Following", callback_data=f"user_following_{username}")
        ],
        [
            InlineKeyboardButton("📊 Contribution Stats", callback_data=f"user_stats_{username}")
        ],
        [
            InlineKeyboardButton("🔄 Refresh Profile", callback_data=f"refresh_user_{username}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.edit_text(
        profile_text,
        parse_mode="MarkdownV2",
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )
