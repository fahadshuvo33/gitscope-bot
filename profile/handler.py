from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import aiohttp
import logging

from profile.display import ProfileDisplay
from profile.repositories import ProfileRepositories
from profile.social import ProfileSocial
from profile.stats import ProfileStats

logger = logging.getLogger(__name__)


class ProfileHandler:
    def __init__(self):
        self.display = ProfileDisplay()
        self.repositories = ProfileRepositories()
        self.social = ProfileSocial()
        self.stats = ProfileStats()

    async def show_profile(self, update, context, username):
        """Main entry point for showing user profile"""
        # Determine if it's a command or message
        if hasattr(update, "message") and update.message:
            loading_msg = await update.message.reply_text(
                f"🔄 Loading profile for {username}...", parse_mode=None
            )
        else:
            # It's a callback query
            query = update.callback_query
            await query.answer()
            loading_msg = query.message

        try:
            from utils.git_api import fetch_user_info

            async with aiohttp.ClientSession() as session:
                user_data = await fetch_user_info(session, username)

            if not user_data:
                await loading_msg.edit_text(
                    f"❌ User `{username}` not found!\n\nPlease check the username and try again.",
                    parse_mode="Markdown",
                )
                return

            # Store user data for callbacks
            context.user_data["current_user"] = user_data
            context.user_data["current_username"] = username

            # Display the profile
            await self.display.show_user_profile(loading_msg, user_data, context)

        except Exception as e:
            logger.error(f"Error fetching profile for {username}: {e}", exc_info=True)
            await loading_msg.edit_text(
                f"❌ Error fetching user profile.\n\nPlease try again later.",
                parse_mode=None,
            )

    async def handle_profile_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str
    ):
        """Handle profile-related callback queries"""
        query = update.callback_query
        await query.answer()

        try:
            # Parse the action for pagination
            if "_page_" in action:
                # Handle pagination callbacks like user_followers_username_page_2
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
                    await self.social.show_followers(
                        query.message, username, context, page
                    )

                elif base_action.startswith("user_following_"):
                    username = base_action.replace("user_following_", "")
                    await self.social.show_following(
                        query.message, username, context, page
                    )

            # Handle regular callbacks (page 1)
            elif action.startswith("user_repos_"):
                username = action.replace("user_repos_", "")
                await self.repositories.show_user_repos(
                    query.message, username, context, 1
                )

            elif action.startswith("user_starred_"):
                username = action.replace("user_starred_", "")
                await self.repositories.show_starred_repos(
                    query.message, username, context, 1
                )

            elif action.startswith("user_followers_"):
                username = action.replace("user_followers_", "")
                await self.social.show_followers(query.message, username, context, 1)

            elif action.startswith("user_following_"):
                username = action.replace("user_following_", "")
                await self.social.show_following(query.message, username, context, 1)

            elif action.startswith("user_stats_"):
                username = action.replace("user_stats_", "")
                await self.stats.show_contribution_stats(
                    query.message, username, context
                )

            elif action.startswith("refresh_user_"):
                username = action.replace("refresh_user_", "")
                await self.show_profile(update, context, username)

            elif action == "back_to_profile":
                # Go back to main profile
                user_data = context.user_data.get("current_user")
                if user_data:
                    await self.display.show_user_profile(
                        query.message, user_data, context
                    )
                else:
                    await query.message.edit_text(
                        "❌ Profile data not found. Please search again."
                    )

        except Exception as e:
            logger.error(
                f"Error handling profile callback {action}: {e}", exc_info=True
            )
            await query.message.edit_text(
                "❌ Something went wrong. Please try again.", parse_mode=None
            )


# Create instance
profile_handler = ProfileHandler()
