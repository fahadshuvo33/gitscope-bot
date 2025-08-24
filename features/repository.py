from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
import aiohttp
import asyncio

# Import the loading system
from utils.loading import show_loading, show_static_loading


class RepositoryHandler:
    def __init__(self):
        self.REPO_ANIMATION = "diamond"  # Diamond animation for repository operations

    async def show_repository_info(
        self, message_or_query, repo_name, context, is_admin_repo: bool = False
    ):
        """Show repository information"""
        # Store current repo in user data
        context.user_data["current_repo"] = repo_name

        # Get the message object
        message = (
            message_or_query
            if hasattr(message_or_query, "edit_text")
            else message_or_query.message
        )

        # Show static loading first to preserve the window
        await show_static_loading(
            message,
            f"📂 **{repo_name}**",
            "Loading repository",
            preserve_content=True,
            animation_type=self.REPO_ANIMATION,
        )

        # Start animated loading
        loading_task = await show_loading(
            message,
            f"📂 **{repo_name}**",
            "Loading repository",
            animation_type=self.REPO_ANIMATION,
        )

        try:
            from utils.git_api import fetch_repo_info
            from utils.formatting import format_repo_info

            async with aiohttp.ClientSession() as session:
                repo_data = await fetch_repo_info(session, repo_name)

            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

            if not repo_data:
                await self._show_repo_error(message, repo_name, "Repository Not Found")
                return

            # Format and send repository information
            repo_info = format_repo_info(repo_data, is_admin_repo=is_admin_repo)
            keyboard = self.create_repo_keyboard()

            await self._update_message(message_or_query, repo_info, keyboard)

        except Exception as e:
            error_text = (
                f"❌ **Error occurred\\!**\n\n"
                f"Failed to fetch: `{escape_markdown(repo_name, 2)}`\n"
                "Please try again later\\."
            )

            if hasattr(message_or_query, "edit_message_text"):
                await message_or_query.edit_message_text(
                    error_text, parse_mode="MarkdownV2"
                )
            else:
                await message_or_query.edit_text(error_text, parse_mode="MarkdownV2")

    def create_repo_keyboard(self):
        """Create inline keyboard for repository actions"""
        keyboard = [
            [
                InlineKeyboardButton("👥 Contributors", callback_data="contributors"),
                InlineKeyboardButton("🔀 Pull Requests", callback_data="prs"),
            ],
            [
                InlineKeyboardButton("🐛 Issues", callback_data="issues"),
                InlineKeyboardButton("💻 Languages", callback_data="languages"),
            ],
            [
                InlineKeyboardButton("🏷️ Releases", callback_data="releases"),
                InlineKeyboardButton("📖 README", callback_data="readme"),
            ],
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh"),
                InlineKeyboardButton("⬅️ Back", callback_data="back_to_start"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    async def handle_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str
    ):
        """Handle repository-related callbacks with loading animations"""
        query = update.callback_query

        if action == "refresh":
            repo = context.user_data.get("current_repo")
            if repo:
                await query.answer()
                await self.refresh_repository(query, repo, context)
            else:
                await query.answer("❌ No repository to refresh")
            return

        # Show loading for other actions
        repo = context.user_data.get("current_repo", "Repository")

        # Show static loading first
        await show_static_loading(
            query.message,
            f"📂 **{repo}**",
            f"Loading {action}",
            preserve_content=True,
            animation_type=self.REPO_ANIMATION,
        )

        # Route to specific repository handlers
        from handlers.contributors import handle_contributors
        from handlers.readme import handle_readme
        from handlers.prs import handle_prs
        from handlers.issues import handle_issues
        from handlers.languages import handle_languages
        from handlers.releases import handle_releases

        handlers = {
            "contributors": handle_contributors,
            "readme": handle_readme,
            "prs": handle_prs,
            "issues": handle_issues,
            "languages": handle_languages,
            "releases": handle_releases,
        }

        handler = handlers.get(action)
        if handler:
            await query.answer()
            await handler(update, context)
        else:
            await query.answer("❌ Unknown action")

    async def _update_message(self, message_or_query, text, keyboard):
        """Update message with proper handling for both message types"""
        try:
            if hasattr(message_or_query, "edit_message_text"):
                await message_or_query.edit_message_text(
                    text,
                    parse_mode="MarkdownV2",
                    reply_markup=keyboard,
                    disable_web_page_preview=True,
                )
            else:
                await message_or_query.edit_text(
                    text,
                    parse_mode="MarkdownV2",
                    reply_markup=keyboard,
                    disable_web_page_preview=True,
                )
        except Exception as e:
            # If edit fails, try alternative approach
            try:
                if hasattr(message_or_query, "message"):
                    await message_or_query.message.edit_text(
                        text,
                        parse_mode="MarkdownV2",
                        reply_markup=keyboard,
                        disable_web_page_preview=True,
                    )
            except Exception:
                pass  # Silent fail for message update

    async def _show_repo_error(self, message, repo_name, error_type):
        """Show repository error with structured message and action buttons"""
        error_text = f"📂 **{repo_name}**\n\n"
        error_text += f"❌ **{error_type}**\n\n"

        if error_type == "Repository Not Found":
            error_text += f"Could not find repository: `{repo_name}`\n\n"
            error_text += f"**Possible causes:**\n"
            error_text += f"• Repository name is incorrect\n"
            error_text += f"• Repository is private\n"
            error_text += f"• Repository has been deleted\n"
            error_text += f"• Owner/organization name is wrong\n\n"
            error_text += f"💡 **Tip:** Check the repository name format (owner/repo)!"
        elif error_type == "Refresh Failed":
            error_text += f"Unable to refresh repository data.\n\n"
            error_text += f"**Possible causes:**\n"
            error_text += f"• Temporary network issue\n"
            error_text += f"• GitHub API temporarily unavailable\n"
            error_text += f"• Repository access changed\n\n"
            error_text += f"💡 **Tip:** Try again in a few moments!"
        else:
            error_text += f"Unable to fetch repository information.\n\n"
            error_text += f"**Possible causes:**\n"
            error_text += f"• Network connection issue\n"
            error_text += f"• GitHub API rate limit\n"
            error_text += f"• Temporary server error\n\n"
            error_text += f"💡 **Tip:** Please try again later!"

        keyboard = [
            [
                InlineKeyboardButton("🔄 Try Again", callback_data="refresh"),
                InlineKeyboardButton("🔍 New Search", callback_data="back_to_start"),
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
        except Exception:
            pass  # Silent fail for error display

    async def show_loading_repository(self, message, repo_name):
        """Show loading state for repository - useful for external calls"""
        await show_static_loading(
            message,
            f"📂 **{repo_name}**",
            "Loading repository",
            preserve_content=True,
            animation_type=self.REPO_ANIMATION,
        )

    def get_repo_summary(self, repo_data):
        """Get a quick repository summary for other components"""
        if not repo_data:
            return "Unknown Repository"

        name = repo_data.get("name", "Unknown")
        owner = repo_data.get("owner", {}).get("login", "Unknown")
        stars = repo_data.get("stargazers_count", 0)
        language = repo_data.get("language", "N/A")

        return f"{owner}/{name} • ⭐ {stars} • {language}"


# Create instance
repository_handler = RepositoryHandler()
