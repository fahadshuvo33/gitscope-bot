# profile/handler.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import aiohttp
import logging
import asyncio

from profile.display import ProfileDisplay
from profile.repositories import ProfileRepositories
from profile.social import ProfileSocial
from profile.stats import ProfileStats
from profile.avatar import AvatarHandler

# Import the loading system
from utils.loading import show_loading, show_static_loading

logger = logging.getLogger(__name__)


class ProfileHandler:
    def __init__(self):
        self.display = ProfileDisplay()
        self.repositories = ProfileRepositories()
        self.social = ProfileSocial()
        self.stats = ProfileStats()
        self.avatar = AvatarHandler()
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
            context.user_data["current_view"] = "profile"  # Track current view

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
        """Handle paginated callback actions with loading"""
        try:
            parts = action.split("_page_")
            base_action = parts[0]
            page = int(parts[1])

            # Check if we're on avatar page first
            current_view = context.user_data.get("current_view", "profile")
            if current_view == "avatar":
                await self._restore_profile_from_avatar(query, context)
                await asyncio.sleep(0.3)
                return

            if base_action.startswith("user_repos_"):
                username = base_action.replace("user_repos_", "")
                original_text, original_markup = await self._show_loading_preserve_content(
                    query.message, f"Loading repositories page {page}", "tech"
                )
                try:
                    await self.repositories.show_user_repos(
                        query.message, username, context, page
                    )
                except Exception as e:
                    await self._show_error_preserve_content(
                        query.message, original_text, original_markup, f"Could not load repositories page {page}"
                    )

            elif base_action.startswith("user_starred_"):
                username = base_action.replace("user_starred_", "")
                original_text, original_markup = await self._show_loading_preserve_content(
                    query.message, f"Loading starred repos page {page}", "stars"
                )
                try:
                    await self.repositories.show_starred_repos(
                        query.message, username, context, page
                    )
                except Exception as e:
                    await self._show_error_preserve_content(
                        query.message, original_text, original_markup, f"Could not load starred repos page {page}"
                    )

            elif base_action.startswith("user_followers_"):
                username = base_action.replace("user_followers_", "")
                original_text, original_markup = await self._show_loading_preserve_content(
                    query.message, f"Loading followers page {page}", "heart"
                )
                try:
                    await self.social.show_followers(query.message, username, context, page)
                except Exception as e:
                    await self._show_error_preserve_content(
                        query.message, original_text, original_markup, f"Could not load followers page {page}"
                    )

            elif base_action.startswith("user_following_"):
                username = base_action.replace("user_following_", "")
                original_text, original_markup = await self._show_loading_preserve_content(
                    query.message, f"Loading following page {page}", "wave"
                )
                try:
                    await self.social.show_following(query.message, username, context, page)
                except Exception as e:
                    await self._show_error_preserve_content(
                        query.message, original_text, original_markup, f"Could not load following page {page}"
                    )
            else:
                await self._show_callback_error(query.message, action, "Unknown Action")

        except (ValueError, IndexError):
            await self._show_callback_error(query.message, action, "Invalid Page")

    async def _handle_regular_action(self, query, context, action):
        """Handle regular callback actions with preserved content loading"""

        # Check current view
        current_view = context.user_data.get("current_view", "profile")

        # Handle avatar-specific actions
        if current_view == "avatar" and action.startswith("refresh_avatar_"):
            username = action.replace("refresh_avatar_", "")
            await self._handle_refresh_avatar(query, context, username)
            return

        # If we're on avatar page but clicked other buttons, go back to profile first
        if current_view == "avatar" and not action.startswith(("refresh_avatar_", "back_to_profile", "back_to_start")):
            await self._restore_profile_from_avatar(query, context)
            await asyncio.sleep(0.3)
            # Re-call this method with profile view
            context.user_data["current_view"] = "profile"
            await self._handle_regular_action(query, context, action)
            return

        if action.startswith("user_repos_"):
            username = action.replace("user_repos_", "")
            original_text, original_markup = await self._show_loading_preserve_content(
                query.message, "Loading repositories", "tech"
            )
            try:
                await self.repositories.show_user_repos(query.message, username, context, 1)
            except Exception as e:
                await self._show_error_preserve_content(
                    query.message, original_text, original_markup, "Could not load repositories"
                )

        elif action.startswith("user_starred_"):
            username = action.replace("user_starred_", "")
            original_text, original_markup = await self._show_loading_preserve_content(
                query.message, "Loading starred repos", "stars"
            )
            try:
                await self.repositories.show_starred_repos(query.message, username, context, 1)
            except Exception as e:
                await self._show_error_preserve_content(
                    query.message, original_text, original_markup, "Could not load starred repos"
                )

        elif action.startswith("user_followers_"):
            username = action.replace("user_followers_", "")
            original_text, original_markup = await self._show_loading_preserve_content(
                query.message, "Loading followers", "heart"
            )
            try:
                await self.social.show_followers(query.message, username, context, 1)
            except Exception as e:
                await self._show_error_preserve_content(
                    query.message, original_text, original_markup, "Could not load followers"
                )

        elif action.startswith("user_following_"):
            username = action.replace("user_following_", "")
            original_text, original_markup = await self._show_loading_preserve_content(
                query.message, "Loading following", "wave"
            )
            try:
                await self.social.show_following(query.message, username, context, 1)
            except Exception as e:
                await self._show_error_preserve_content(
                    query.message, original_text, original_markup, "Could not load following"
                )

        elif action.startswith("user_stats_"):
            username = action.replace("user_stats_", "")
            original_text, original_markup = await self._show_loading_preserve_content(
                query.message, "Loading stats", "pulse"
            )
            try:
                await self.stats.show_contribution_stats(query.message, username, context)
            except Exception as e:
                await self._show_error_preserve_content(
                    query.message, original_text, original_markup, "Could not load stats"
                )

        elif action.startswith("show_avatar_"):
            username = action.replace("show_avatar_", "")
            original_text, original_markup = await self._show_loading_preserve_content(
                query.message, "Loading avatar", "magic"
            )
            try:
                await self._show_avatar_replace_message(query.message, username, context, original_text, original_markup)
            except Exception as e:
                await self._show_error_preserve_content(
                    query.message, original_text, original_markup, "Could not load avatar"
                )

        elif action.startswith("refresh_user_"):
            username = action.replace("refresh_user_", "")
            await self.display.refresh_user_profile(query.message, username, context)

        elif action == "back_to_profile":
            await self._handle_back_to_profile(query, context)

        else:
            original_text, original_markup = await self._show_loading_preserve_content(
                query.message, "Processing", "bounce"
            )
            await self._show_error_preserve_content(
                query.message, original_text, original_markup, "Unknown command"
            )

    # ==================== LOADING AND ERROR HELPERS ====================

    async def _show_loading_preserve_content(self, message, action, animation_type="pulse"):
        """Show loading while preserving existing content"""
        original_text = message.text if hasattr(message, 'text') else message.caption
        original_markup = message.reply_markup

        # Create temporary loading message
        loading_text = f"{original_text}\n\n💫 {action}..."

        try:
            if hasattr(message, 'text'):
                await message.edit_text(
                    loading_text,
                    parse_mode="Markdown",
                    reply_markup=original_markup,
                    disable_web_page_preview=True,
                )
            else:
                await message.edit_caption(
                    caption=loading_text,
                    parse_mode="Markdown",
                    reply_markup=original_markup,
                )
        except Exception:
            pass  # If edit fails, continue anyway

        return original_text, original_markup

    async def _show_error_preserve_content(self, message, original_text, original_markup, error_msg):
        """Show error at bottom of existing content"""
        error_text = f"{original_text}\n\n❌ {error_msg} - Try again"

        try:
            if hasattr(message, 'text'):
                await message.edit_text(
                    error_text,
                    parse_mode="Markdown",
                    reply_markup=original_markup,
                    disable_web_page_preview=True,
                )
            else:
                await message.edit_caption(
                    caption=error_text,
                    parse_mode="Markdown",
                    reply_markup=original_markup,
                )
        except Exception:
            pass

    # ==================== AVATAR HANDLING METHODS ====================

    async def _show_avatar_replace_message(self, message, username, context, original_text, original_markup):
        """Replace profile message with avatar image (Option 2)"""
        try:
            user_data = context.user_data.get("current_user")

            if not user_data:
                await self._show_error_preserve_content(
                    message, original_text, original_markup, "Session expired"
                )
                return

            avatar_url = user_data.get("avatar_url")

            if not avatar_url:
                await self._show_error_preserve_content(
                    message, original_text, original_markup, "No avatar available"
                )
                return

            # Store original message info for back navigation
            context.user_data["original_profile_text"] = original_text
            context.user_data["original_profile_markup"] = original_markup
            context.user_data["chat_id"] = message.chat_id
            context.user_data["current_view"] = "avatar"

            # Small delay to show loading animation
            await asyncio.sleep(0.5)

            # Delete the original profile message
            await message.delete()

            # Send avatar image in its place
            large_avatar_url = f"{avatar_url}&s=400"

            avatar_message = await message.chat.send_photo(
                photo=large_avatar_url,
                caption=f"👤 **{username}'s GitHub Avatar**\n\n📸 Profile picture displayed!\n\n💡 **Tip:** Use the buttons below to navigate!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🏠 Back to Profile", callback_data="back_to_profile"),
                        InlineKeyboardButton("🔄 Refresh Avatar", callback_data=f"refresh_avatar_{username}")
                    ],
                    [
                        InlineKeyboardButton("📂 Repositories", callback_data=f"user_repos_{username}"),
                        InlineKeyboardButton("⭐ Starred", callback_data=f"user_starred_{username}")
                    ],
                    [
                        InlineKeyboardButton("👥 Followers", callback_data=f"user_followers_{username}"),
                        InlineKeyboardButton("👤 Following", callback_data=f"user_following_{username}")
                    ],
                    [
                        InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")
                    ]
                ])
            )

            # Store avatar message for future operations
            context.user_data["avatar_message"] = avatar_message
            context.user_data["avatar_message_id"] = avatar_message.message_id

        except Exception as e:
            logger.error(f"Avatar replace failed: {type(e).__name__}")
            await self._show_error_preserve_content(
                message, original_text, original_markup, "Avatar display failed"
            )

    async def _handle_back_to_profile(self, query, context):
        """Handle back to profile with loading animation"""
        current_view = context.user_data.get("current_view", "profile")

        if current_view == "avatar":
            # We're coming back from avatar view
            await self._restore_profile_from_avatar(query, context)
        else:
            # Regular back to profile
            user_data = context.user_data.get("current_user")
            username = context.user_data.get("current_username", "Unknown")

            if user_data:
                await self.display.show_user_profile(query.message, user_data, context, username)
            else:
                await self._show_session_lost(query.message)

    async def _restore_profile_from_avatar(self, query, context):
        """Restore profile view from avatar with loading animation"""
        try:
            user_data = context.user_data.get("current_user")
            username = context.user_data.get("current_username", "Unknown")

            if not user_data:
                await self._show_session_lost_avatar(query.message)
                return

            # Show loading animation on avatar image
            await self._show_loading_on_avatar(query.message, "Returning to profile", "pulse")

            # Small delay to show loading
            await asyncio.sleep(0.5)

            # Delete avatar message
            await query.message.delete()

            # Send profile message back
            chat_id = context.user_data.get("chat_id")
            if chat_id:
                # Create new profile message
                from telegram import Bot
                bot = context.bot

                profile_message = await bot.send_message(
                    chat_id=chat_id,
                    text=f"👤 **{username}'s Profile**\n\n💫 Restoring profile...",
                    parse_mode="Markdown"
                )

                # Update context
                context.user_data["current_view"] = "profile"

                # Show the full profile
                await self.display.show_user_profile(profile_message, user_data, context, username)

        except Exception as e:
            logger.error(f"Profile restore failed: {type(e).__name__}")
            # Fallback - try to show profile anyway
            try:
                chat_id = context.user_data.get("chat_id")
                if chat_id:
                    from telegram import Bot
                    bot = context.bot
                    error_message = await bot.send_message(
                        chat_id=chat_id,
                        text="❌ Error restoring profile. Please search again.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")
                        ]])
                    )
            except Exception:
                pass

    async def _show_loading_on_avatar(self, message, action, animation_type="magic"):
        """Show loading animation on avatar message"""
        try:
            # Update caption with loading
            original_caption = message.caption or ""
            loading_caption = f"{original_caption}\n\n💫 {action}..."

            await message.edit_caption(
                caption=loading_caption,
                parse_mode="Markdown",
                reply_markup=message.reply_markup
            )
        except Exception:
            pass  # If edit fails, continue anyway

    async def _handle_refresh_avatar(self, query, context, username):
        """Handle avatar refresh with loading animation"""
        try:
            # Show loading on avatar
            await self._show_loading_on_avatar(query.message, "Refreshing avatar", "magic")

            # Fetch fresh user data
            from utils.git_api import _make_request_with_retry

            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                    user_data = await _make_request_with_retry(
                    session, f"/users/{username}", timeout=8
                )

            if not user_data:
                # Show error on avatar
                error_caption = f"{query.message.caption}\n\n❌ Refresh failed - Try again"
                await query.message.edit_caption(
                    caption=error_caption,
                    parse_mode="Markdown",
                    reply_markup=query.message.reply_markup
                )
                return

            # Update context with fresh data
            context.user_data["current_user"] = user_data

            # Get new avatar URL
            new_avatar_url = user_data.get("avatar_url")

            if new_avatar_url:
                # Update avatar image
                large_avatar_url = f"{new_avatar_url}&s=400"

                # Delete old avatar
                await query.message.delete()

                # Send fresh avatar
                new_avatar_message = await query.message.chat.send_photo(
                    photo=large_avatar_url,
                    caption=f"👤 **{username}'s GitHub Avatar**\n\n📸 Profile picture refreshed!\n\n💡 **Tip:** Avatar updated successfully!",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("🏠 Back to Profile", callback_data="back_to_profile"),
                            InlineKeyboardButton("🔄 Refresh Avatar", callback_data=f"refresh_avatar_{username}")
                        ],
                        [
                            InlineKeyboardButton("📂 Repositories", callback_data=f"user_repos_{username}"),
                            InlineKeyboardButton("⭐ Starred", callback_data=f"user_starred_{username}")
                        ],
                        [
                            InlineKeyboardButton("👥 Followers", callback_data=f"user_followers_{username}"),
                            InlineKeyboardButton("👤 Following", callback_data=f"user_following_{username}")
                        ],
                        [
                            InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")
                        ]
                    ])
                )

                # Update stored avatar message
                context.user_data["avatar_message"] = new_avatar_message
                context.user_data["avatar_message_id"] = new_avatar_message.message_id

        except Exception as e:
            logger.error(f"Avatar refresh failed: {type(e).__name__}")
            # Show error on avatar
            try:
                error_caption = f"{query.message.caption}\n\n❌ Refresh failed - Try again"
                await query.message.edit_caption(
                    caption=error_caption,
                    parse_mode="Markdown",
                    reply_markup=query.message.reply_markup
                )
            except Exception:
                pass

    async def _show_session_lost_avatar(self, message):
        """Show session lost error on avatar page"""
        try:
            error_caption = f"{message.caption}\n\n❌ Session expired"
            await message.edit_caption(
                caption=error_caption,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")
                ]])
            )
        except Exception:
            pass

    # ==================== ERROR DISPLAY METHODS ====================

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
            "avatar": "AvatarHandler initialized",
        }


# Create instance
profile_handler = ProfileHandler()
