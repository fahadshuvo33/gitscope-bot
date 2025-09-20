# profile/avatar.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging
from utils.formatting import format_admin_header, format_admin_footer, add_admin_context

logger = logging.getLogger(__name__)


class AvatarHandler:
    """Handles avatar display functionality with admin support"""

    async def show_user_avatar_info(self, message, username, context, preserve_content=True):
        """Show avatar info inline (not as separate message)"""
        try:
            user_data = context.user_data.get("current_user")
            is_admin = context.user_data.get("is_admin_profile", False)

            if not user_data:
                return False, "Session expired"

            avatar_url = user_data.get("avatar_url")

            if not avatar_url:
                return False, "No avatar available"

            return True, avatar_url

        except Exception as e:
            logger.error(f"Avatar info failed: {type(e).__name__}")
            return False, "Avatar info failed"
    
    async def show_user_avatar(self, message, username, context):
        """Display user avatar as separate message with admin support"""
        try:
            user_data = context.user_data.get("current_user")
            is_admin = context.user_data.get("is_admin_profile", False)

            if not user_data:
                await self._show_session_error(message)
                return

            avatar_url = user_data.get("avatar_url")

            if not avatar_url:
                await self._show_no_avatar_error(message, username, is_admin)
                return

            # Create avatar caption with admin context if needed
            caption = self._format_avatar_caption(username, is_admin)
            keyboard = self._get_avatar_keyboard(username, is_admin)
            
            large_avatar_url = f"{avatar_url}&s=400"

            await message.reply_photo(
                photo=large_avatar_url,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=keyboard
            )

        except Exception as e:
            logger.error(f"Avatar display failed: {type(e).__name__}")
            await self._show_avatar_error(message, username)

    async def refresh_avatar(self, message, username, context):
        """Refresh and redisplay avatar"""
        try:
            is_admin = context.user_data.get("is_admin_profile", False)
            
            # Get fresh user data
            from utils.git_api import fetch_user_info
            import aiohttp
            
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                fresh_user_data = await fetch_user_info(session, username)

            if not fresh_user_data:
                await self._show_refresh_error(message, username, is_admin)
                return

            # Update context with fresh data
            context.user_data["current_user"] = fresh_user_data
            avatar_url = fresh_user_data.get("avatar_url")
            
            if not avatar_url:
                await self._show_no_avatar_error(message, username, is_admin)
                return

            # Create refreshed avatar caption
            caption = self._format_avatar_refreshed_caption(username, is_admin)
            keyboard = self._get_avatar_keyboard(username, is_admin)
            
            large_avatar_url = f"{avatar_url}&s=400"

            # Delete old message and send new one
            await message.delete()
            new_message = await message.chat.send_photo(
                photo=large_avatar_url,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            
            # Update context with new message
            context.user_data["avatar_message"] = new_message

        except Exception as e:
            logger.error(f"Avatar refresh failed: {type(e).__name__}")
            await self._show_refresh_error(message, username, context.user_data.get("is_admin_profile", False))

    def _format_avatar_caption(self, username, is_admin=False):
        """Format avatar display caption"""
        base_caption = (
            f"👤 **{username}'s GitHub Avatar**\n\n"
            f"📸 Profile picture displayed!\n\n"
            f"💡 **Tip:** This is their GitHub profile picture!"
        )
        
        if is_admin:
            return add_admin_context(base_caption, username)
        
        return base_caption

    def _format_avatar_refreshed_caption(self, username, is_admin=False):
        """Format avatar refreshed caption"""
        base_caption = (
            f"👤 **{username}'s GitHub Avatar**\n\n"
            f"📸 Avatar refreshed successfully!\n\n"
            f"💡 **Tip:** Profile picture updated!"
        )
        
        if is_admin:
            return add_admin_context(base_caption, username)
        
        return base_caption

    def _get_avatar_keyboard(self, username, is_admin=False):
        """Get avatar navigation keyboard with admin support"""
        buttons = [
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
            ]
        ]
        
        # Add admin-specific buttons if admin profile
        if is_admin:
            buttons.append([
                InlineKeyboardButton("📊 Admin Stats", callback_data=f"admin_stats_{username}"),
                InlineKeyboardButton("💾 Export Avatar", callback_data=f"admin_export_avatar_{username}")
            ])
        
        # Add back button
        buttons.append([
            InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")
        ])
        
        return InlineKeyboardMarkup(buttons)

    def _get_simple_back_keyboard(self):
        """Get simple back keyboard for errors"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Back to Profile", callback_data="back_to_profile")],
            [InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")]
        ])

    # ==================== ERROR HANDLERS ====================

    async def _show_session_error(self, message):
        """Show session expired error"""
        error_text = (
            f"👤 **Avatar Display**\n\n"
            f"❌ **Session Expired**\n\n"
            f"Your session has expired or user data was lost.\n\n"
            f"💡 **Tip:** Search for the user again!"
        )
        
        await message.edit_text(
            error_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")
            ]]),
            disable_web_page_preview=True
        )

    async def _show_no_avatar_error(self, message, username, is_admin=False):
        """Show no avatar available error"""
        base_text = (
            f"👤 **{username}'s Avatar**\n\n"
            f"📸 **No Avatar Available**\n\n"
            f"This user doesn't have a profile picture set.\n\n"
            f"💡 **Tip:** Try refreshing or check their profile!"
        )
        
        error_text = add_admin_context(base_text, username) if is_admin else base_text
        
        try:
            await message.edit_text(
                error_text,
                parse_mode="Markdown",
                reply_markup=self._get_simple_back_keyboard(),
                disable_web_page_preview=True
            )
        except Exception:
            await message.reply_text(
                error_text,
                parse_mode="Markdown",
                reply_markup=self._get_simple_back_keyboard()
            )

    async def _show_avatar_error(self, message, username):
        """Show avatar loading error"""
        error_text = (
            f"👤 **{username}'s Avatar**\n\n"
            f"❌ **Avatar Loading Failed**\n\n"
            f"Could not load the profile picture.\n\n"
            f"**Possible causes:**\n"
            f"• Network connection issues\n"
            f"• GitHub API temporarily unavailable\n"
            f"• User avatar not accessible\n\n"
            f"💡 **Tip:** Try refreshing or go back to profile!"
        )
        
        try:
            await message.edit_text(
                error_text,
                parse_mode="Markdown",
                reply_markup=self._get_simple_back_keyboard(),
                disable_web_page_preview=True
            )
        except Exception:
            await message.reply_text(
                error_text,
                parse_mode="Markdown",
                reply_markup=self._get_simple_back_keyboard()
            )

    async def _show_refresh_error(self, message, username, is_admin=False):
        """Show avatar refresh error"""
        base_text = (
            f"👤 **{username}'s Avatar**\n\n"
            f"❌ **Refresh Failed**\n\n"
            f"Could not refresh the avatar.\n\n"
            f"**Possible causes:**\n"
            f"• Network connection issues\n"
            f"• GitHub API temporarily unavailable\n"
            f"• User data not accessible\n\n"
            f"💡 **Tip:** Try again later or go back to profile!"
        )
        
        error_text = add_admin_context(base_text, username) if is_admin else base_text
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 Try Again", callback_data=f"refresh_avatar_{username}"),
                InlineKeyboardButton("🏠 Back to Profile", callback_data="back_to_profile")
            ],
            [InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")]
        ])
        
        try:
            await message.edit_caption(
                caption=error_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        except Exception:
            try:
                await message.edit_text(
                    error_text,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )
            except Exception:
                await message.reply_text(
                    error_text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )

    # ==================== UTILITY METHODS ====================

    def get_avatar_url_with_size(self, base_url, size=400):
        """Get avatar URL with specific size"""
        if not base_url:
            return None
        
        if '?' in base_url:
            return f"{base_url}&s={size}"
        else:
            return f"{base_url}?s={size}"

    def validate_avatar_url(self, url):
        """Validate if avatar URL is accessible"""
        if not url:
            return False
        
        # Basic validation
        if not url.startswith(('http://', 'https://')):
            return False
        
        if 'avatars.githubusercontent.com' not in url and 'github.com' not in url:
            return False
        
        return True

    async def get_avatar_metadata(self, user_data):
        """Get avatar metadata for advanced features"""
        try:
            avatar_url = user_data.get("avatar_url", "")
            
            metadata = {
                "has_avatar": bool(avatar_url),
                "avatar_url": avatar_url,
                "default_size": "400x400",
                "available_sizes": ["100", "200", "300", "400", "500"],
                "format": "image/png" if avatar_url else None
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Avatar metadata error: {type(e).__name__}")
            return {"has_avatar": False, "error": str(e)}


# Create instance
avatar_handler = AvatarHandler()