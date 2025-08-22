from telegram import Update
from telegram.ext import ContextTypes
import logging

# Import features
from features.about import about_handler
from features.developer import developer_handler
from features.trending_repos import trending_handler
from features.user_profile import user_profile_handler

# Import commands
from .start import start_command
from .help import help_command
from .trending import trending_command
from .profile import profile_command

logger = logging.getLogger(__name__)


class CommandRouter:
    """Router for all bot commands and callbacks"""

    def __init__(self):
        self.about = about_handler
        self.developer = developer_handler
        self.trending = trending_handler
        self.user_profile = user_profile_handler

    # Command handlers
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await start_command(update, context)

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await help_command(update, context)

    async def handle_trending(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await trending_command(update, context)

    async def handle_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await profile_command(update, context)

    # Callback query router
    async def handle_callback_query(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Route callback queries to appropriate handlers"""
        query = update.callback_query
        action = query.data

        try:
            # Basic navigation
            if action == "back_to_start":
                await start_command(update, context)

            elif action == "help":
                await help_command(update, context)

            elif action == "trending":
                await trending_command(update, context)

            # About & Developer
            elif action == "about":
                await self.about.handle_about(update, context)

            elif action == "developer_profile":
                await self.developer.handle_developer_profile(update, context)

            elif action == "source_code":
                await self.developer.handle_source_code(update, context)

            elif action == "other_projects":
                await self.developer.handle_other_projects(update, context)

            elif action == "rate_bot":
                await self.developer.handle_rate_bot(update, context)

            # Trending languages
            # Trending languages with time ranges
            elif action.startswith("trending_"):
                parts = action.split("_")

                if len(parts) == 3 and parts[2] in ["daily", "weekly", "monthly"]:
                    # Handle time range callbacks like trending_python_weekly
                    language = parts[1]
                    time_range = parts[2]
                    await self.trending.handle_trending_by_language(
                        update, context, language, time_range
                    )

                elif len(parts) == 2:
                    # Handle basic language callbacks like trending_python (defaults to weekly)
                    language = parts[1]
                    await self.trending.handle_trending_by_language(
                        update, context, language
                    )

                else:
                    # Fallback for malformed trending callbacks
                    logger.warning(f"Malformed trending callback: {action}")
                    await query.answer("❌ Invalid action")
            # User profile actions
            elif action.startswith("user_"):
                await self.user_profile.handle_user_callback(update, context, action)

            elif action.startswith("refresh_user_"):
                username = action.replace("refresh_user_", "")
                await self.user_profile.refresh_user_profile(update, context, username)

            # Repository actions (when accessed from user profile)
            elif action.startswith("repo_"):
                await self.handle_repository_callback(update, context, action)

            else:
                logger.warning(f"Unknown callback action: {action}")
                await query.answer("❌ Unknown action")

        except Exception as e:
            logger.error(f"Error handling callback {action}: {str(e)}")
            await query.answer("❌ Something went wrong. Please try again.")

    async def handle_repository_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str
    ):
        """Handle repository-related callbacks"""
        # This will route to your existing repository handlers
        from features.repository import repository_handler

        await repository_handler.handle_callback(update, context, action)


# Create router instance
command_router = CommandRouter()
