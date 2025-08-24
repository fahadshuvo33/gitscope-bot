import asyncio
from telegram import Update
from telegram.ext import ContextTypes
import logging

# Import features
from features.about import about_handler
from features.developer import developer_handler
from features.trending_repos import trending_handler

# Import commands
from .start import start_command
from .help import help_command
from .trending import trending_command
from .profile import profile_command

# Import handlers
from profile.handler import ProfileHandler
from features.repository import repository_handler

# Import loading utilities
from utils.loading import show_loading, show_static_loading

logger = logging.getLogger(__name__)


class CommandRouter:
    """Router for all bot commands and callbacks"""

    def __init__(self):
        self.about = about_handler
        self.developer = developer_handler
        self.trending = trending_handler
        self.profile = ProfileHandler()  # Initialize profile handler directly

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
        logger.debug(f"DEBUG: handle_callback_query - Received action: {action}")

        try:
            # Answer callback query immediately to remove loading indicator
            await query.answer()
            
            # Basic navigation with loading for heavy operations
            if action == "back_to_start":
                await start_command(update, context)

            elif action == "help":
                await help_command(update, context)

            elif action == "trending":
                await trending_command(update, context)

            # About & Developer
            elif action == "about":
                await self._handle_with_loading(
                    update, context, 
                    self.about.handle_about,
                    "ℹ️ **About GitScope Bot**",
                    "Loading information",
                    "stars"
                )

            elif action == "developer_profile":
                await self._handle_with_loading(
                    update, context,
                    self.developer.handle_developer_profile,
                    "👨‍💻 **Developer Profile**",
                    "Loading developer info",
                    "tech"
                )

            elif action == "source_code":
                await self._handle_with_loading(
                    update, context,
                    self.developer.handle_source_code,
                    "💻 **Source Code**",
                    "Loading repository",
                    "tech"
                )

            elif action == "other_projects":
                await self._handle_with_loading(
                    update, context,
                    self.developer.handle_other_projects,
                    "🚀 **Other Projects**",
                    "Loading projects",
                    "rocket"
                )

            elif action == "rate_bot":
                await self.developer.handle_rate_bot(update, context)

            # Trending languages with time ranges
            elif action.startswith("trending_"):
                parts = action.split("_")

                if len(parts) == 3 and parts[2] in ["daily", "weekly", "monthly"]:
                    # Handle time range callbacks like trending_python_weekly
                    language = parts[1]
                    time_range = parts[2]
                    await self._handle_trending_with_loading(
                        update, context, language, time_range
                    )

                elif len(parts) == 2:
                    # Handle basic language callbacks like trending_python (defaults to weekly)
                    language = parts[1]
                    await self._handle_trending_with_loading(
                        update, context, language
                    )

                else:
                    # Fallback for malformed trending callbacks
                    logger.warning(f"Malformed trending callback: {action}")
                    await query.answer("❌ Invalid action")

            # Handle profile-related actions
            elif (
                action.startswith("user_")
                or action.startswith("refresh_user_")
                or action == "back_to_profile"
                or action.startswith("show_avatar_")
            ):
                logger.info(f"Routing profile action: {action}")
                logger.debug(f"DEBUG: handle_callback_query - Routing to profile handler for action: {action}")
                try:
                    await self.profile.handle_profile_callback(update, context, action)
                except Exception as e:
                    logger.error(
                        f"Profile callback error for action '{action}': {str(e)}"
                    )
                    await query.message.edit_text(
                        "❌ Could not process profile action. Please try again."
                    )

            # Repository actions (when accessed from user profile)
            elif action.startswith("repo_"):
                await self.handle_repository_callback(update, context, action)

            else:
                logger.warning(f"Unknown callback action: {action}")
                await query.message.edit_text("❌ Invalid action. Please try again.")

        except Exception as e:
            logger.error(f"Error handling callback {action}: {str(e)}", exc_info=True)
            try:
                await query.message.edit_text(
                    "❌ Something went wrong. Please try again."
                )
            except:
                # If edit fails, just log it
                logger.error("Failed to show error message")

    async def _handle_with_loading(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE,
        handler_func,
        title: str,
        loading_text: str,
        animation_type: str
    ):
        """Handle callback with loading animation"""
        query = update.callback_query
        message = query.message
        
        # Show static loading first
        try:
            await show_static_loading(
                message,
                title,
                loading_text,
                preserve_content=True,
                animation_type=animation_type,
            )
        except Exception as e:
            logger.debug(f"Static loading skipped: {e}")
        
        # Start animated loading
        loading_task = await show_loading(
            message,
            title,
            loading_text,
            animation_type=animation_type,
            preserve_content=True,
        )
        
        try:
            # Brief wait for effect
            await asyncio.sleep(0.5)
            
            # Stop loading animation
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass
            
            # Call the actual handler
            await handler_func(update, context)
            
        except Exception as e:
            # Stop loading on error
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass
            
            logger.error(f"Error in {handler_func.__name__}: {e}")
            await message.edit_text(
                f"❌ Error loading content. Please try again.",
                parse_mode="Markdown"
            )

    async def _handle_trending_with_loading(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        language: str,
        time_range: str = "weekly"
    ):
        """Handle trending with loading animation"""
        query = update.callback_query
        message = query.message
        
        # Create language display name
        lang_display = language.title() if language != "all" else "All Languages"
        
        # Show static loading first
        try:
            await show_static_loading(
                message,
                f"📈 **Trending {lang_display}**",
                f"Fetching {time_range} trends",
                preserve_content=True,
                animation_type="fire",
            )
        except Exception as e:
            logger.debug(f"Static loading skipped: {e}")
        
        # Start animated loading
        loading_task = await show_loading(
            message,
            f"📈 **Trending {lang_display}**",
            f"Analyzing {time_range} trends",
            animation_type="fire",
            preserve_content=True,
        )
        
        try:
            # Brief wait
            await asyncio.sleep(1.0)
            
            # Stop loading animation
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass
            
            # Call the trending handler
            await self.trending.handle_trending_by_language(
                update, context, language, time_range
            )
            
        except Exception as e:
            # Stop loading on error
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass
            
            logger.error(f"Error fetching trending repos: {e}")
            await message.edit_text(
                f"❌ Error fetching trending repositories. Please try again.",
                parse_mode="Markdown"
            )

    async def handle_repository_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str
    ):
        """Handle repository-related callbacks"""
        # This will route to your existing repository handlers
        await repository_handler.handle_callback(update, context, action)


# Create router instance
command_router = CommandRouter()