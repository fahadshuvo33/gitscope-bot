from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import aiohttp
import logging
import asyncio

from profile.display import ProfileDisplay
from profile.repositories import ProfileRepositories
from profile.social import ProfileSocial
from profile.stats import ProfileStats
from profile.avatar_handler import AvatarHandler

# Import the loading system
from utils.loading import show_loading, show_static_loading

logger = logging.getLogger(__name__)


class ProfileHandler:
    def __init__(self):
        self.display = ProfileDisplay()
        self.repositories = ProfileRepositories()
        self.social = ProfileSocial()
        self.stats = ProfileStats()
        self.avatar = AvatarHandler()  # Add this line
        self.SEARCH_ANIMATION = "pulse"

    async def show_profile(self, update, context, username):
        """Main entry point for showing user profile with loading animation"""
        # Determine if it's a command or message
        if hasattr(update, "message") and update.message:
            loading_msg = await update.message.reply_text(
                f"👤 **{username}'s Profile**\n\n💡 **Tip:** Searching for user...",
                parse_mode="Markdown",
            )
        else:
            # It's a callback query
            query = update.callback_query
            await query.answer()
            loading_msg = query.message

        # Show static loading first to preserve the window
        await show_static_loading(
            loading_msg,
            f"👤 **{username}'s Profile**",
            "Searching user",
            preserve_content=True,
            animation_type=self.SEARCH_ANIMATION,
        )

        # Start animated loading
        loading_task = await show_loading(
            loading_msg,
            f"👤 **{username}'s Profile**",
            "Searching user",
            animation_type=self.SEARCH_ANIMATION,
        )

        try:
            from utils.git_api import fetch_user_info

            timeout = aiohttp.ClientTimeout(total=12, connect=6)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                user_data = await fetch_user_info(session, username)

            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

            if not user_data:
                await self._show_user_not_found(loading_msg, username)
                return

            # Store user data for callbacks
            context.user_data["current_user"] = user_data
            context.user_data["current_username"] = username

            # Display the profile
            await self.display.show_user_profile(loading_msg, user_data, context, username)

        except Exception as e:
            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

            # Log minimal error info
            logger.error(f"Profile fetch error for {username}: {type(e).__name__}")
            await self._show_search_error(loading_msg, username)

    async def handle_profile_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str
    ):
        """Handle profile-related callback queries with error handling"""
        query = update.callback_query
        await query.answer()

        try:
            # Parse the action for pagination
            if "_page_" in action:
                await self._handle_paginated_action(query, context, action)
            else:
                await self._handle_regular_action(query, context, action)

        except Exception as e:
            # Log minimal error info
            logger.error(f"Callback error for {action}: {type(e).__name__}")
            await self._show_callback_error(query.message, action)

    async def _handle_paginated_action(self, query, context, action):
        """Handle paginated callback actions"""
        try:
            parts = action.split("_page_")
            base_action = parts[0]
            page = int(parts[1])

            if base_action.startswith("user_repos_"):
                username = base_action.replace("user_repos_", "")
                await self.repositories.show_user_repos(
                    query.message, username, context, page
                )

            elif base_action.startswith("user_starred_"):
                username = base_action.replace("user_starred_", "")
                await self.repositories.show_starred_repos(
                    query.message, username, context, page
                )

            elif base_action.startswith("user_followers_"):
                username = base_action.replace("user_followers_", "")
                await self.social.show_followers(query.message, username, context, page)

            elif base_action.startswith("user_following_"):
                username = base_action.replace("user_following_", "")
                await self.social.show_following(query.message, username, context, page)
            else:
                await self._show_callback_error(query.message, action, "Unknown Action")

        except (ValueError, IndexError):
            await self._show_callback_error(query.message, action, "Invalid Page")

    async def _handle_regular_action(self, query, context, action):
        """Handle regular (non-paginated) callback actions"""
        if action.startswith("user_repos_"):
            username = action.replace("user_repos_", "")
            await self.repositories.show_user_repos(query.message, username, context, 1)

        elif action.startswith("user_starred_"):
            username = action.replace("user_starred_", "")
            await self.repositories.show_starred_repos(query.message, username, context, 1)

        elif action.startswith("user_followers_"):
            username = action.replace("user_followers_", "")
            await self.social.show_followers(query.message, username, context, 1)

        elif action.startswith("user_following_"):
            username = action.replace("user_following_", "")
            await self.social.show_following(query.message, username, context, 1)

        elif action.startswith("user_stats_"):
            username = action.replace("user_stats_", "")
            await self.stats.show_contribution_stats(query.message, username, context)

        elif action.startswith("refresh_user_"):
            username = action.replace("refresh_user_", "")
            await self.display.refresh_user_profile(query.message, username, context)

        elif action.startswith("show_avatar_"):
            username = action.replace("show_avatar_", "")
            await self.avatar.show_user_avatar(query.message, username, context)

        elif action == "back_to_profile":
            await self._handle_back_to_profile(query, context)

        else:
            await self._show_callback_error(query.message, action, "Unknown Command")

    async def _handle_back_to_profile(self, query, context):
        """Handle back to profile action with error checking"""
        user_data = context.user_data.get("current_user")
        username = context.user_data.get("current_username", "Unknown")

        if user_data:
            await self.display.show_user_profile(query.message, user_data, context, username)
        else:
            await self._show_session_lost(query.message)

    async def _show_user_avatar(self, message, username, context):
        """Show user's avatar picture - FIXED VERSION"""
        try:
            user_data = context.user_data.get("current_user")
            
            if not user_data:
                await message.reply_text(
                    "❌ Session expired. Please search for the user again.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")
                    ]])
                )
                return
                
            avatar_url = user_data.get("avatar_url")
            
            if not avatar_url:
                await message.reply_text(
                    "📸 No avatar available for this user.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⬅️ Back to Profile", callback_data="back_to_profile")
                    ]])
                )
                return

            # Send avatar as a new photo message (can't edit text to photo)
            large_avatar_url = f"{avatar_url}&s=400"
            
            await message.reply_photo(
                photo=large_avatar_url,
                caption=f"👤 **{username}'s GitHub Avatar**\n\n💡 **Tip:** This is their profile picture!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Profile", callback_data="back_to_profile")
                ]])
            )
            
        except Exception as e:
            logger.error(f"Avatar display failed: {type(e).__name__}")
            await message.reply_text(
                "❌ Could not load avatar",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Profile", callback_data="back_to_profile")
                ]])
            )

    async def _show_user_not_found(self, message, username):
        """Show user not found error - preserves window"""
        error_text = f"👤 **User Search**\n\n"
        error_text += f"❌ **User Not Found**\n\n"
        error_text += f"User `{username}` not found on GitHub.\n\n"
        error_text += f"**Possible reasons:**\n"
        error_text += f"• Username doesn't exist\n"
        error_text += f"• Account was deleted\n"
        error_text += f"• Typo in username\n\n"
        error_text += f"💡 **Tip:** Double-check the username spelling!"

        keyboard = [
            [InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")]
        ]

        try:
            await message.edit_text(
                error_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.warning(f"User not found display failed: {type(e).__name__}")

    async def _show_search_error(self, message, username):
        """Show search error - preserves window"""
        error_text = f"👤 **{username}'s Profile**\n\n"
        error_text += f"❌ **Search Error**\n\n"
        error_text += f"Unable to search for user profile.\n\n"
        error_text += f"**Possible causes:**\n"
        error_text += f"• Network connection issues\n"
        error_text += f"• GitHub API temporary unavailable\n"
        error_text += f"• Rate limiting\n\n"
        error_text += f"💡 **Tip:** Wait a moment and try again!"

        keyboard = [
            [
                InlineKeyboardButton("🔄 Retry", callback_data=f"refresh_user_{username}"),
                InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start"),
            ]
        ]

        try:
            await message.edit_text(
                error_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.warning(f"Search error display failed: {type(e).__name__}")

    async def _show_callback_error(self, message, action, error_type="Action Error"):
        """Show callback error - preserves window"""
        # Extract username from action if possible
        username = "Unknown"
        for prefix in [
            "user_repos_", "user_starred_", "user_followers_", 
            "user_following_", "user_stats_", "show_avatar_",
        ]:
            if action.startswith(prefix):
                username = action.replace(prefix, "").split("_page_")[0]
                break

        error_text = f"👤 **{username}'s Profile**\n\n"
        error_text += f"❌ **{error_type}**\n\n"
        error_text += f"Something went wrong with this action.\n\n"
        error_text += f"💡 **Tip:** Try the action again or go back to profile!"

        keyboard = [
            [
                InlineKeyboardButton("🔄 Try Again", callback_data=action),
                InlineKeyboardButton("🏠 Back to Profile", callback_data="back_to_profile"),
            ],
            [InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")],
        ]

        try:
            await message.edit_text(
                error_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.warning(f"Callback error display failed: {type(e).__name__}")

    async def _show_session_lost(self, message):
        """Show session lost error - preserves window"""
        error_text = f"👤 **User Profile**\n\n"
        error_text += f"❌ **Session Expired**\n\n"
        error_text += f"Your session has expired or profile data was lost.\n\n"
        error_text += f"💡 **Tip:** Search for the user again!"

        keyboard = [
            [InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")]
        ]

        try:
            await message.edit_text(
                error_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.warning(f"Session lost display failed: {type(e).__name__}")

    def get_handler_stats(self):
        """Get basic handler statistics for monitoring"""
        return {
            "display": "ProfileDisplay initialized",
            "repositories": "ProfileRepositories initialized",
            "social": "ProfileSocial initialized",
            "stats": "ProfileStats initialized",
        }


# Create instance
profile_handler = ProfileHandler()