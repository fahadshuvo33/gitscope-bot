from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
import aiohttp
import asyncio

# Import the loading system
from utils.loading import show_loading, show_static_loading

class UserProfileHandler:
    def __init__(self):
        # Different animation types for different user actions
        self.REPOS_ANIMATION = "progress"      # Progress bars for repositories
        self.STARRED_ANIMATION = "stars"       # Stars animation for starred repos
        self.FOLLOWERS_ANIMATION = "pulse"     # Pulse animation for followers
        self.FOLLOWING_ANIMATION = "wave"      # Wave animation for following
        self.STATS_ANIMATION = "rainbow"       # Rainbow animation for stats
        self.REFRESH_ANIMATION = "spinner"     # Spinner for refresh

    async def handle_user_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
        """Handle user-related callback actions with loading animations"""
        query = update.callback_query
        await query.answer()

        # Parse action
        parts = action.split('_')
        if len(parts) < 3:
            await query.edit_message_text("❌ Invalid action")
            return

        action_type = parts[1]  # repos, starred, followers, following, stats
        username = parts[2]

        # Show appropriate loading for each action
        animations = {
            "repos": self.REPOS_ANIMATION,
            "starred": self.STARRED_ANIMATION,
            "followers": self.FOLLOWERS_ANIMATION,
            "following": self.FOLLOWING_ANIMATION,
            "stats": self.STATS_ANIMATION
        }

        animation_type = animations.get(action_type, "bounce")
        action_labels = {
            "repos": "repositories",
            "starred": "starred repos",
            "followers": "followers",
            "following": "following",
            "stats": "statistics"
        }
        action_label = action_labels.get(action_type, action_type)

        # Show static loading first to preserve the window
        await show_static_loading(
            query.message,
            f"👤 **{username}'s {action_label.title()}**",
            f"Loading {action_label}",
            preserve_content=True,
            animation_type=animation_type,
        )

        # Start animated loading
        loading_task = await show_loading(
            query.message,
            f"👤 **{username}'s {action_label.title()}**",
            f"Loading {action_label}",
            animation_type=animation_type,
        )

        try:
            if action_type == "repos":
                await self.show_user_repositories(query, username, context, loading_task)
            elif action_type == "starred":
                await self.show_user_starred(query, username, context, loading_task)
            elif action_type == "followers":
                await self.show_user_followers(query, username, context, loading_task)
            elif action_type == "following":
                await self.show_user_following(query, username, context, loading_task)
            elif action_type == "stats":
                await self.show_user_stats(query, username, context, loading_task)
            else:
                # Stop loading animation gracefully
                if loading_task and not loading_task.done():
                    loading_task.cancel()
                    try:
                        await loading_task
                    except asyncio.CancelledError:
                        pass
                await query.edit_message_text("❌ Unknown action")

        except Exception as e:
            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass
            await self._show_user_error(query.message, username, action_type, "Action Error")

    async def show_user_repositories(self, query, username, context, loading_task):
        """Show user's repositories with loading animation"""
        try:
            from utils.git_api import fetch_user_repositories

            async with aiohttp.ClientSession() as session:
                repos = await fetch_user_repositories(session, username, limit=10)

            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

            if not repos:
                await self._show_user_error(query.message, username, "repos", "No Repositories Found")
                return

            text = self._build_repositories_content(repos, username)
            keyboard = self._build_repositories_keyboard(username)

            await query.edit_message_text(
                text,
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )

        except Exception as e:
            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass
            await self._show_user_error(query.message, username, "repos", "Fetch Error")

    async def show_user_starred(self, query, username, context, loading_task):
        """Show user's starred repositories with loading animation"""
        try:
            # Simulate some processing time
            await asyncio.sleep(0.5)

            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

            text = f"⭐ *Starred repositories by {escape_markdown(username, 2)}*\n\n"
            text += "🚧 This feature is coming soon\\!\n\n"
            text += "**What will be available:**\n"
            text += "• List of starred repositories\n"
            text += "• Repository details and stats\n"
            text += "• Direct links to repos\n"
            text += "• Filter and search options"

            keyboard = [
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data=f"user_starred_{username}"),
                    InlineKeyboardButton("👤 Back to Profile", callback_data=f"refresh_user_{username}")
                ]
            ]

            await query.edit_message_text(
                text,
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass
            await self._show_user_error(query.message, username, "starred", "Display Error")

    async def show_user_followers(self, query, username, context, loading_task):
        """Show user's followers with loading animation"""
        try:
            # Simulate some processing time
            await asyncio.sleep(0.5)

            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

            text = f"👥 *Followers of {escape_markdown(username, 2)}*\n\n"
            text += "🚧 This feature is coming soon\\!\n\n"
            text += "**What will be available:**\n"
            text += "• Complete followers list\n"
            text += "• Follower profiles and stats\n"
            text += "• Recent followers\n"
            text += "• Mutual connections"

            keyboard = [
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data=f"user_followers_{username}"),
                    InlineKeyboardButton("👤 Back to Profile", callback_data=f"refresh_user_{username}")
                ]
            ]

            await query.edit_message_text(
                text,
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass
            await self._show_user_error(query.message, username, "followers", "Display Error")

    async def show_user_following(self, query, username, context, loading_task):
        """Show who the user is following with loading animation"""
        try:
            # Simulate some processing time
            await asyncio.sleep(0.5)

            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

            text = f"👤 *Following by {escape_markdown(username, 2)}*\n\n"
            text += "🚧 This feature is coming soon\\!\n\n"
            text += "**What will be available:**\n"
            text += "• Complete following list\n"
            text += "• User profiles and activity\n"
            text += "• Recently followed users\n"
            text += "• Shared interests"

            keyboard = [
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data=f"user_following_{username}"),
                    InlineKeyboardButton("👤 Back to Profile", callback_data=f"refresh_user_{username}")
                ]
            ]

            await query.edit_message_text(
                text,
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass
            await self._show_user_error(query.message, username, "following", "Display Error")

    async def show_user_stats(self, query, username, context, loading_task):
        """Show user's contribution statistics with loading animation"""
        try:
            # Simulate some processing time
            await asyncio.sleep(0.7)

            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

            text = f"📊 *Contribution Stats for {escape_markdown(username, 2)}*\n\n"
            text += "🚧 This feature is coming soon\\!\n\n"
            text += "**What will be available:**\n"
            text += "• Commit activity graphs\n"
            text += "• Language usage statistics\n"
            text += "• Contribution streaks\n"
            text += "• Repository activity timeline\n"
            text += "• Collaboration insights"

            keyboard = [
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data=f"user_stats_{username}"),
                    InlineKeyboardButton("👤 Back to Profile", callback_data=f"refresh_user_{username}")
                ]
            ]

            await query.edit_message_text(
                text,
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass
            await self._show_user_error(query.message, username, "stats", "Display Error")

    def _build_repositories_content(self, repos, username):
        """Build the repositories content"""
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

        return text

    def _build_repositories_keyboard(self, username):
        """Build the repositories keyboard"""
        return [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data=f"user_repos_{username}"),
                InlineKeyboardButton("👤 Back to Profile", callback_data=f"refresh_user_{username}")
            ]
        ]

    async def _show_user_error(self, message, username, action_type, error_type):
        """Show user action error with structured message and action buttons"""
        action_labels = {
            "repos": "Repositories",
            "starred": "Starred Repos",
            "followers": "Followers",
            "following": "Following",
            "stats": "Statistics"
        }
        action_label = action_labels.get(action_type, action_type.title())

        error_text = f"👤 **{username}'s {action_label}**\n\n"
        error_text += f"❌ **{error_type}**\n\n"

        if error_type == "No Repositories Found":
            error_text += f"No public repositories found for {username}.\n\n"
            error_text += f"**Possible causes:**\n"
            error_text += f"• User has no public repositories\n"
            error_text += f"• All repositories are private\n"
            error_text += f"• User account doesn't exist\n\n"
            error_text += f"💡 **Tip:** Check if the username is correct!"
        else:
            error_text += f"Unable to load {action_label.lower()} information.\n\n"
            error_text += f"**Possible causes:**\n"
            error_text += f"• Network connection issue\n"
            error_text += f"• GitHub API temporarily unavailable\n"
            error_text += f"• Rate limit exceeded\n\n"
            error_text += f"💡 **Tip:** Try again in a few moments!"

        keyboard = [
            [
                InlineKeyboardButton("🔄 Try Again", callback_data=f"user_{action_type}_{username}"),
                InlineKeyboardButton("👤 Back to Profile", callback_data=f"refresh_user_{username}")
            ],
            [
                InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")
            ]
        ]

        try:
            await message.edit_text(
                error_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception:
            pass  # Silent fail for error display

    async def refresh_user_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE, username: str):
        """Refresh user profile with loading animation"""
        query = update.callback_query

        # Show static loading first to preserve the window
        await show_static_loading(
            query.message,
            f"👤 **{username}'s Profile**",
            "Refreshing profile",
            preserve_content=True,
            animation_type=self.REFRESH_ANIMATION,
        )

        try:
            from commands.profile import profile_command

            # Simulate the profile command
            context.args = [username]

            # Convert callback query to message-like object for profile_command
            update.message = type('MockMessage', (), {
                'reply_text': lambda text, **kwargs: query.edit_message_text(text, **kwargs)
            })()

            await profile_command(update, context)

        except Exception as e:
            await self._show_user_error(query.message, username, "profile", "Refresh Error")

# Create instance
user_profile_handler = UserProfileHandler()
