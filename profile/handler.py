# profile/handler.py
from telegram import Update
from telegram.ext import ContextTypes
import aiohttp
import logging
import asyncio
from utils.git_api import fetch_user_info, _make_request_with_retry
from profile.display import ProfileDisplay
from profile.repositories import ProfileRepositories
from profile.social import ProfileSocial
from profile.stats import ProfileStats
from profile.avatar import AvatarHandler
from profile.formatter import profile_formatter
from utils.formatting import (
    _escape_markdown_v2, format_content_with_loading, format_content_with_error,
    extract_username_from_action, get_loading_text_for_action
)
from utils.loading import with_loading, without_loading

logger = logging.getLogger(__name__)


class ProfileHandler:
    def __init__(self):
        self.display = ProfileDisplay()
        self.repositories = ProfileRepositories()
        self.social = ProfileSocial()
        self.stats = ProfileStats()
        self.avatar = AvatarHandler()
        self.formatter = profile_formatter

    async def show_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                          username: str, is_admin_profile: bool = False):
        """Main entry point for showing user profile with loading animation"""
        
        # Use loading decorator through a wrapper function
        @with_loading("Searching user", 2.0)
        async def _show_profile_with_loading(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
            try:
                # Store admin status in context
                ctx.user_data["is_admin_profile"] = is_admin_profile
                
                # Get the loading message from context (set by decorator)
                message = ctx.user_data.get('_loading_message')
                if not message:
                    # Fallback if no loading message
                    if hasattr(upd, "message") and upd.message:
                        message = upd.message
                    elif hasattr(upd, "callback_query") and upd.callback_query:
                        message = upd.callback_query.message
                    else:
                        logger.error("No message available for profile display")
                        return
                
                # Fetch user data with better error handling
                user_data = None
                try:
                    logger.info(f"Fetching user data for: {username}")
                    timeout = aiohttp.ClientTimeout(total=12, connect=6)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        user_data = await fetch_user_info(session, username)
                    logger.info(f"User data received: {user_data is not None}")
                except Exception as e:
                    logger.error(f"API Error: {type(e).__name__} - {str(e)}")
                    user_data = None
                
                if not user_data:
                    await self._show_user_not_found(message, username, is_admin_profile)
                    return

                # Store data and show profile
                self._store_user_data(ctx, user_data, username, is_admin_profile)
                await self.display.show_user_profile(message, ctx, user_data, username, is_admin_profile=is_admin_profile)

            except Exception as e:
                logger.error(f"Profile display error for {username}: {type(e).__name__} - {str(e)}")
                await self._show_search_error(message, username, is_admin_profile)
        
        # Call the wrapper function
        await _show_profile_with_loading(update, context)

    async def handle_profile_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
        """Handle profile-related callback queries with simplified routing"""
        query = update.callback_query
        await query.answer()

        try:
            # Handle special cases first
            if action == "back_to_profile":
                return await self._handle_back_to_profile(query, context)
            
            # Handle pagination
            if "_page_" in action:
                return await self._handle_paginated_action(query, context, action)
            
            # Handle regular actions
            await self._handle_regular_action(query, context, action)

        except Exception as e:
            logger.error(f"Callback error for {action}: {type(e).__name__}")
            await self._show_callback_error(query.message, action)

    # ==================== FETCH DATA ====================

    async def _fetch_user_data(self, username):
        """Fetch user data from GitHub API"""
        try:
            timeout = aiohttp.ClientTimeout(total=12, connect=6)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                return await fetch_user_info(session, username)
        except Exception as e:
            logger.error(f"Error fetching user data for {username}: {type(e).__name__} - {str(e)}")
            raise

    def _store_user_data(self, context, user_data, username, is_admin_profile=False):
        """Store user data in context"""
        context.user_data.update({
            "current_user": user_data,
            "current_username": username,
            "current_view": "profile",
            "is_admin_profile": is_admin_profile
        })

    # ==================== ACTION HANDLERS ====================

    async def _handle_paginated_action(self, query, context, action):
        """Handle paginated callback actions"""
        try:
            parts = action.split("_page_")
            base_action = parts[0]
            page = int(parts[1])
            
            # Check if coming from avatar view
            if await self._handle_avatar_navigation(query, context):
                return
            
            # Get username and loading text
            username = None
            for prefix in ['user_repos_', 'user_starred_', 'user_followers_', 'user_following_']:
                if base_action.startswith(prefix):
                    username = base_action.replace(prefix, "")
                    break
            
            if not username:
                await self._show_callback_error(query.message, action, "Unknown Action")
                return
            
            # Use loading wrapper for pagination
            @with_loading(f"Loading page {page}", 1.0)
            async def _paginated_action(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
                loading_message = ctx.user_data.get('_loading_message', query.message)
                
                if base_action.startswith('user_repos_'):
                    is_admin = ctx.user_data.get("is_admin_profile", False)
                    await self.repositories.show_user_repos(loading_message, username, ctx, page, is_admin_profile=is_admin)
                elif base_action.startswith('user_starred_'):
                    is_admin = ctx.user_data.get("is_admin_profile", False)
                    await self.repositories.show_starred_repos(loading_message, username, ctx, page, is_admin_profile=is_admin)
                elif base_action.startswith('user_followers_'):
                    is_admin = ctx.user_data.get("is_admin_profile", False)
                    await self.social.show_followers(loading_message, username, ctx, page, is_admin_profile=is_admin)
                elif base_action.startswith('user_following_'):
                    is_admin = ctx.user_data.get("is_admin_profile", False)
                    await self.social.show_following(loading_message, username, ctx, page, is_admin_profile=is_admin)
            
            # Create temporary update for decorator
            temp_update = type('TempUpdate', (), {'callback_query': query, 'message': None})()
            await _paginated_action(temp_update, context)
            
        except (ValueError, IndexError):
            await self._show_callback_error(query.message, action, "Invalid Page")
        except Exception as e:
            logger.error(f"Paginated action error: {type(e).__name__}")
            await self._show_callback_error(query.message, action)

    async def _handle_regular_action(self, query, context, action):
        """Handle regular callback actions"""
        # Check if coming from avatar view
        if await self._handle_avatar_navigation(query, context, action):
            return
        
        # Get username and loading text
        username = None
        loading_text = "Processing"
        
        for prefix in ['user_repos_', 'user_starred_', 'user_followers_', 'user_following_', 
                      'user_stats_', 'show_avatar_', 'refresh_user_', 'refresh_avatar_']:
            if action.startswith(prefix):
                username = action.replace(prefix, "")
                loading_text = get_loading_text_for_action(prefix)
                break
        
        if not username:
            await self._show_callback_error(query.message, action)
            return
        
        # Use loading wrapper for regular actions
        @with_loading(loading_text, 1.5)
        async def _regular_action(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
            loading_message = ctx.user_data.get('_loading_message', query.message)
            is_admin = ctx.user_data.get("is_admin_profile", False)
            
            if action.startswith('user_repos_'):
                await self.repositories.show_user_repos(loading_message, username, ctx, 1, is_admin_profile=is_admin)
            elif action.startswith('user_starred_'):
                await self.repositories.show_starred_repos(loading_message, username, ctx, 1, is_admin_profile=is_admin)
            elif action.startswith('user_followers_'):
                await self.social.show_followers(loading_message, username, ctx, 1, is_admin_profile=is_admin)
            elif action.startswith('user_following_'):
                await self.social.show_following(loading_message, username, ctx, 1, is_admin_profile=is_admin)
            elif action.startswith('user_stats_'):
                await self.stats.show_contribution_stats(loading_message, username, ctx, is_admin_profile=is_admin)
            elif action.startswith('show_avatar_'):
                await self._show_avatar_replace_message_internal(loading_message, username, ctx)
            elif action.startswith('refresh_user_'):
                await self.display.refresh_user_profile(loading_message, username, ctx, is_admin_profile=is_admin)
            elif action.startswith('refresh_avatar_'):
                await self._refresh_avatar_image_internal(loading_message, username, ctx)
        
        # Create temporary update for decorator
        temp_update = type('TempUpdate', (), {'callback_query': query, 'message': None})()
        await _regular_action(temp_update, context)

    async def _handle_avatar_navigation(self, query, context, action=None):
        """Handle navigation from avatar view"""
        current_view = context.user_data.get("current_view", "profile")
        
        if current_view == "avatar":
            if action and action.startswith("refresh_avatar_"):
                # Handle avatar refresh directly
                username = action.replace("refresh_avatar_", "")
                
                @with_loading("Refreshing avatar", 1.0)
                async def _refresh_avatar(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
                    loading_message = ctx.user_data.get('_loading_message', query.message)
                    await self._refresh_avatar_image_internal(loading_message, username, ctx)
                
                temp_update = type('TempUpdate', (), {'callback_query': query, 'message': None})()
                await _refresh_avatar(temp_update, context)
                return True
            else:
                # Return to profile for other actions
                await self._restore_profile_from_avatar(query, context)
                await asyncio.sleep(0.3)
                if action:
                    context.user_data["current_view"] = "profile"
                    await self._handle_regular_action(query, context, action)
                return True
        
        return False

    # ==================== AVATAR HANDLING ====================

    async def _show_avatar_replace_message_internal(self, message, username, context):
        """Internal avatar display method (without decorator)"""
        try:
            user_data = context.user_data.get("current_user")
            is_admin = context.user_data.get("is_admin_profile", False)
            
            if not user_data:
                raise Exception("Session expired")

            avatar_url = user_data.get("avatar_url")
            if not avatar_url:
                raise Exception("No avatar available")

            # Store original message info
            context.user_data.update({
                "original_profile_text": message.text,
                "original_profile_markup": message.reply_markup,
                "chat_id": message.chat_id,
                "current_view": "avatar"
            })

            await message.delete()

            # Send avatar image
            caption = self.formatter.format_avatar_display(username, is_admin)
            keyboard = self.formatter.get_avatar_keyboard(username)
            
            avatar_message = await message.chat.send_photo(
                photo=f"{avatar_url}&s=400",
                caption=caption,
                parse_mode="Markdown",
                reply_markup=keyboard
            )

            context.user_data.update({
                "avatar_message": avatar_message,
                "avatar_message_id": avatar_message.message_id
            })

        except Exception as e:
            logger.error(f"Avatar display failed: {type(e).__name__}")
            raise

    async def _refresh_avatar_image_internal(self, message, username, context):
        """Internal avatar refresh method (without decorator)"""
        try:
            is_admin = context.user_data.get("is_admin_profile", False)
            
            # Fetch fresh user data
            from utils.git_api import _make_request_with_retry
            
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                user_data = await _make_request_with_retry(session, f"/users/{username}", timeout=8)

            if not user_data:
                raise Exception("Refresh failed")

            context.user_data["current_user"] = user_data
            avatar_url = user_data.get("avatar_url")
            
            if avatar_url:
                await message.delete()
                
                caption = self.formatter.format_avatar_refreshed(username, is_admin)
                keyboard = self.formatter.get_avatar_keyboard(username)
                                
                new_avatar = await message.chat.send_photo(
                    photo=f"{avatar_url}&s=400",
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                
                context.user_data.update({
                    "avatar_message": new_avatar,
                    "avatar_message_id": new_avatar.message_id
                })

        except Exception as e:
            logger.error(f"Avatar refresh failed: {type(e).__name__}")
            raise

    async def _handle_back_to_profile(self, query, context):
        """Handle back to profile navigation"""
        current_view = context.user_data.get("current_view", "profile")
        
        if current_view == "avatar":
            await self._restore_profile_from_avatar(query, context)
        else:
            user_data = context.user_data.get("current_user")
            username = context.user_data.get("current_username", "Unknown")
            is_admin = context.user_data.get("is_admin_profile", False)
            
            if user_data:
                await self.display.show_user_profile(query.message, context, user_data, username, is_admin_profile=is_admin)
            else:
                await self._show_session_lost(query.message)

    async def _restore_profile_from_avatar(self, query, context):
        """Restore profile view from avatar"""
        @with_loading("Returning to profile", 0.8)
        async def _restore_profile(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
            try:
                user_data = ctx.user_data.get("current_user")
                username = ctx.user_data.get("current_username", "Unknown")
                is_admin = ctx.user_data.get("is_admin_profile", False)
                
                if not user_data:
                    await self._show_session_lost_avatar(query.message)
                    return

                await query.message.delete()

                # Get loading message from decorator
                loading_message = ctx.user_data.get('_loading_message')
                if not loading_message:
                    # Create new message if no loading message
                    chat_id = ctx.user_data.get("chat_id")
                    if chat_id:
                        loading_text = self.formatter.format_profile_restored(username, is_admin)
                        loading_message = await upd.bot if hasattr(upd, 'bot') else ctx.bot.send_message(
                            chat_id=chat_id,
                            text=loading_text,
                            parse_mode="Markdown"
                        )

                # Update context and show full profile
                ctx.user_data["current_view"] = "profile"
                await self.display.show_user_profile(loading_message, ctx, user_data, username, is_admin_profile=is_admin)

            except Exception as e:
                logger.error(f"Profile restore failed: {type(e).__name__}")
                # Fallback error handling
                try:
                    chat_id = ctx.user_data.get("chat_id")
                    if chat_id:
                        bot = upd.bot if hasattr(upd, 'bot') else ctx.bot
                        await bot.send_message(
                            chat_id=chat_id,
                            text="❌ Error restoring profile. Please search again.",
                            reply_markup=self.formatter.get_session_lost_keyboard()
                        )
                except Exception:
                    pass
        
        # Create temporary update for decorator
        temp_update = type('TempUpdate', (), {
            'callback_query': query, 
            'message': None,
            'bot': context.bot
        })()
        await _restore_profile(temp_update, context)

    # ==================== ERROR DISPLAY METHODS ====================

    async def _show_user_not_found(self, message, username, is_admin=False):
        """Show user not found error"""
        error_text = self.formatter.format_user_not_found(username, is_admin)
        keyboard = self.formatter.get_user_not_found_keyboard()

        try:
            await message.edit_text(
                error_text, parse_mode="Markdown", reply_markup=keyboard,
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.warning(f"User not found display failed: {type(e).__name__}")

    async def _show_search_error(self, message, username, is_admin=False):
        """Show search error"""
        error_text = self.formatter.format_search_error(username, is_admin)
        keyboard = self.formatter.get_search_error_keyboard(username)

        try:
            await message.edit_text(
                error_text, parse_mode="Markdown", reply_markup=keyboard,
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.warning(f"Search error display failed: {type(e).__name__}")

    async def _show_callback_error(self, message, action, error_type="Action Error"):
        """Show callback error"""
        username = extract_username_from_action(action)
        # We can't access context here, so we'll assume non-admin for error display
        error_text = self.formatter.format_callback_error(username, error_type, is_admin=False)
        keyboard = self.formatter.get_callback_error_keyboard(action)

        try:
            await message.edit_text(
                error_text, parse_mode="Markdown", reply_markup=keyboard,
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.warning(f"Callback error display failed: {type(e).__name__}")

    async def _show_session_lost(self, message):
        """Show session lost error"""
        error_text = self.formatter.format_session_lost(is_admin=False)
        keyboard = self.formatter.get_session_lost_keyboard()

        try:
            await message.edit_text(
                error_text, parse_mode="Markdown", reply_markup=keyboard,
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.warning(f"Session lost display failed: {type(e).__name__}")

    async def _show_session_lost_avatar(self, message):
        """Show session lost error on avatar page"""
        try:
            error_caption = self.formatter.format_avatar_error(message.caption or "", "Session expired")
            await message.edit_caption(
                caption=error_caption, parse_mode="Markdown",
                reply_markup=self.formatter.get_session_lost_keyboard()
            )
        except Exception:
            pass

    # ==================== PUBLIC WRAPPER METHODS ====================
    
    async def handle_refresh_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE, username: str):
        """Public wrapper for refresh user action"""
        @with_loading("Refreshing profile", 1.5)
        async def _refresh_user(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
            loading_message = ctx.user_data.get('_loading_message')
            is_admin = ctx.user_data.get("is_admin_profile", False)
            
            if loading_message:
                await self.display.refresh_user_profile(loading_message, username, ctx, is_admin_profile=is_admin)
        
        await _refresh_user(update, context)

    async def handle_refresh_avatar(self, update: Update, context: ContextTypes.DEFAULT_TYPE, username: str):
        """Public wrapper for refresh avatar action"""
        @with_loading("Refreshing avatar", 1.0)
        async def _refresh_avatar(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
            loading_message = ctx.user_data.get('_loading_message')
            
            if loading_message:
                await self._refresh_avatar_image_internal(loading_message, username, ctx)
        
        await _refresh_avatar(update, context)

    async def handle_show_avatar(self, update: Update, context: ContextTypes.DEFAULT_TYPE, username: str):
        """Public wrapper for show avatar action"""
        @with_loading("Loading avatar", 1.0)
        async def _show_avatar(upd: Update, ctx: ContextTypes.DEFAULT_TYPE):
            loading_message = ctx.user_data.get('_loading_message')
            
            if loading_message:
                await self._show_avatar_replace_message_internal(loading_message, username, ctx)
        
        await _show_avatar(update, context)

    # ==================== MONITORING ====================

    def get_handler_stats(self):
        """Get basic handler statistics for monitoring"""
        return {
            "display": "ProfileDisplay initialized",
            "repositories": "ProfileRepositories initialized", 
            "social": "ProfileSocial initialized",
            "stats": "ProfileStats initialized",
            "avatar": "AvatarHandler initialized",
            "formatter": "ProfileFormatter initialized",
            "loading_system": "Decorator-based loading implemented"
        }


# Create instance
profile_handler = ProfileHandler()