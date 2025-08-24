from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging

logger = logging.getLogger(__name__)


class AvatarHandler:
    """Handles avatar display functionality"""

    async def show_user_avatar_info(self, message, username, context, preserve_content=True):
            """Show avatar info inline (not as separate message)"""
            try:
                user_data = context.user_data.get("current_user")

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
            """Legacy method - creates separate message (if still needed elsewhere)"""
            try:
                user_data = context.user_data.get("current_user")

                if not user_data:
                    await self._show_session_error(message)
                    return

                avatar_url = user_data.get("avatar_url")

                if not avatar_url:
                    await self._show_no_avatar_error(message)
                    return

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
                await self._show_avatar_error(message)


    async def _show_session_error(self, message):
        """Show session expired error"""
        await message.reply_text(
            "❌ Session expired. Please search for the user again.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")
            ]])
        )

    async def _show_no_avatar_error(self, message):
        """Show no avatar available error"""
        await message.reply_text(
            "📸 No avatar available for this user.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Profile", callback_data="back_to_profile")
            ]])
        )

    async def _show_avatar_error(self, message):
        """Show avatar loading error"""
        await message.reply_text(
            "❌ Could not load avatar",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Profile", callback_data="back_to_profile")
            ]])
        )
