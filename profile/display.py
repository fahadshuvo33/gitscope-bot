from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime


class ProfileDisplay:
    def __init__(self):
        pass

    async def show_user_profile(self, message, user_data, context):
        """Display beautiful user profile"""

        # Get user info safely
        name = user_data.get("name") or user_data.get("login", "Unknown")
        username = user_data.get("login", "Unknown")
        bio = user_data.get("bio", "")
        company = user_data.get("company", "")
        location = user_data.get("location", "")
        blog = user_data.get("blog", "")
        twitter = user_data.get("twitter_username", "")

        public_repos = user_data.get("public_repos", 0)
        followers = user_data.get("followers", 0)
        following = user_data.get("following", 0)
        public_gists = user_data.get("public_gists", 0)

        # Format join date
        created_at = user_data.get("created_at", "")
        if created_at:
            try:
                created_date = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                joined = created_date.strftime("%B %d, %Y")
                join_year = created_date.year
                years_on_github = datetime.now().year - join_year
            except:
                joined = "Unknown"
                years_on_github = 0
        else:
            joined = "Unknown"
            years_on_github = 0

        # Build beautiful profile
        profile_text = f"👤 **{name}**\n"
        profile_text += f"🏷️ @{username}\n\n"

        if bio:
            profile_text += f"📝 _{bio[:150]}{'...' if len(bio) > 150 else ''}_\n\n"

        # Stats section with emojis
        profile_text += "📊 **GitHub Stats**\n"
        profile_text += f"┌─ 📂 **{public_repos:,}** public repositories\n"
        profile_text += f"├─ 👥 **{followers:,}** followers\n"
        profile_text += f"├─ 👤 **{following:,}** following\n"
        profile_text += f"└─ 📄 **{public_gists:,}** public gists\n\n"

        # Details section
        profile_text += "ℹ️ **Profile Details**\n"
        if company:
            profile_text += f"🏢 {company}\n"
        if location:
            profile_text += f"📍 {location}\n"
        if blog:
            if not blog.startswith(("http://", "https://")):
                blog = f"https://{blog}"
            profile_text += f"🌐 [Website]({blog})\n"
        if twitter:
            profile_text += f"🐦 [@{twitter}](https://twitter.com/{twitter})\n"

        profile_text += f"📅 Joined {joined}"
        if years_on_github > 0:
            profile_text += f" ({years_on_github} years ago)"
        profile_text += "\n"

        profile_text += f"\n🔗 [View on GitHub](https://github.com/{username})"

        # Create action buttons
        keyboard = [
            [
                InlineKeyboardButton(
                    "📂 Repositories", callback_data=f"user_repos_{username}"
                ),
                InlineKeyboardButton(
                    "⭐ Starred", callback_data=f"user_starred_{username}"
                ),
            ],
            [
                InlineKeyboardButton(
                    f"👥 Followers ({followers:,})",
                    callback_data=f"user_followers_{username}",
                ),
                InlineKeyboardButton(
                    f"👤 Following ({following:,})",
                    callback_data=f"user_following_{username}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📊 Stats & Activity", callback_data=f"user_stats_{username}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔄 Refresh", callback_data=f"refresh_user_{username}"
                ),
                InlineKeyboardButton("⬅️ Back", callback_data="back_to_start"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await message.edit_text(
            profile_text,
            parse_mode="Markdown",
            reply_markup=reply_markup,
            disable_web_page_preview=True,
        )
