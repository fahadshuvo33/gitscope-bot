from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
import aiohttp

class UserProfileHandler:

    async def handle_user_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
        """Handle user-related callback actions"""
        query = update.callback_query
        await query.answer()

        # Parse action
        parts = action.split('_')
        if len(parts) < 3:
            await query.edit_message_text("❌ Invalid action")
            return

        action_type = parts[1]  # repos, starred, followers, following, stats
        username = parts[2]

        await query.edit_message_text(f"🔄 *Loading {action_type}\\.\\.\\.*", parse_mode="MarkdownV2")

        try:
            if action_type == "repos":
                await self.show_user_repositories(query, username, context)
            elif action_type == "starred":
                await self.show_user_starred(query, username, context)
            elif action_type == "followers":
                await self.show_user_followers(query, username, context)
            elif action_type == "following":
                await self.show_user_following(query, username, context)
            elif action_type == "stats":
                await self.show_user_stats(query, username, context)
            else:
                await query.edit_message_text("❌ Unknown action")

        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)}")

    async def show_user_repositories(self, query, username, context):
        """Show user's repositories"""
        from utils.git_api import fetch_user_repositories

        async with aiohttp.ClientSession() as session:
            repos = await fetch_user_repositories(session, username, limit=10)

        if not repos:
            await query.edit_message_text(
                f"❌ No repositories found for `{escape_markdown(username, 2)}`",
                parse_mode="MarkdownV2"
            )
            return

        text = f"📂 *Repositories by {escape_markdown(username, 2)}*\n\n"

        for i, repo in enumerate(repos[:8], 1):
            name = repo.get('name', 'Unknown')
            description = repo.get('description', 'No description')[:50]
            stars = repo.get('stargazers_count', 0)
            language = repo.get('language', 'Unknown')

            if description:
                description += "..." if len(repo.get('description', '')) > 50 else ""

            text += f"{i}\\. `{escape_markdown(name, 2)}`\n"
            text += f"   {escape_markdown(description, 2)}\n"
            text += f"   ⭐ {stars} • 💻 {language}\n\n"

        # Add buttons for repository interaction
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data=f"user_repos_{username}"),
                InlineKeyboardButton("👤 Back to Profile", callback_data=f"refresh_user_{username}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

    async def show_user_starred(self, query, username, context):
        """Show user's starred repositories"""
        # Similar implementation to repositories but for starred repos
        await query.edit_message_text(
            f"⭐ *Starred repositories by {escape_markdown(username, 2)}*\n\n"
            "🚧 This feature is coming soon\\!",
            parse_mode="MarkdownV2"
        )

    async def show_user_followers(self, query, username, context):
        """Show user's followers"""
        await query.edit_message_text(
            f"👥 *Followers of {escape_markdown(username, 2)}*\n\n"
            "🚧 This feature is coming soon\\!",
            parse_mode="MarkdownV2"
        )

    async def show_user_following(self, query, username, context):
        """Show who the user is following"""
        await query.edit_message_text(
            f"👤 *Following by {escape_markdown(username, 2)}*\n\n"
            "🚧 This feature is coming soon\\!",
            parse_mode="MarkdownV2"
        )

    async def show_user_stats(self, query, username, context):
        """Show user's contribution statistics"""
        await query.edit_message_text(
            f"📊 *Contribution Stats for {escape_markdown(username, 2)}*\n\n"
            "🚧 This feature is coming soon\\!",
            parse_mode="MarkdownV2"
        )

    async def refresh_user_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE, username: str):
        """Refresh user profile"""
        from commands.profile import profile_command

        # Simulate the profile command
        context.args = [username]
        query = update.callback_query

        # Convert callback query to message-like object for profile_command
        update.message = type('MockMessage', (), {
            'reply_text': lambda text, **kwargs: query.edit_message_text(text, **kwargs)
        })()

        await profile_command(update, context)

# Create instance
user_profile_handler = UserProfileHandler()
