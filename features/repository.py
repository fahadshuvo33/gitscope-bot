from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
import aiohttp
import asyncio

class RepositoryHandler:

    async def show_repository_info(self, message_or_query, repo_name, context, is_admin_repo: bool = False):
        """Show repository information"""
        # Store current repo in user data
        context.user_data["current_repo"] = repo_name

        try:
            from utils.git_api import fetch_repo_info
            from utils.formatting import format_repo_info

            async with aiohttp.ClientSession() as session:
                repo_data = await fetch_repo_info(session, repo_name)

            if not repo_data:
                error_text = (
                    f"❌ **Repository not found\\!**\n\n"
                    f"Could not find: `{escape_markdown(repo_name, 2)}`\n"
                    "Please check the repository name and try again\\."
                )

                if hasattr(message_or_query, 'edit_message_text'):
                    await message_or_query.edit_message_text(error_text, parse_mode="MarkdownV2")
                else:
                    await message_or_query.edit_text(error_text, parse_mode="MarkdownV2")
                return

            # Format and send repository information
            repo_info = format_repo_info(repo_data, is_admin_repo=is_admin_repo)
            keyboard = self.create_repo_keyboard()

            if hasattr(message_or_query, 'edit_message_text'):
                await message_or_query.edit_message_text(
                    repo_info,
                    parse_mode="MarkdownV2",
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )
            else:
                await message_or_query.edit_text(
                    repo_info,
                    parse_mode="MarkdownV2",
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )

        except Exception as e:
            error_text = (
                f"❌ **Error occurred\\!**\n\n"
                f"Failed to fetch: `{escape_markdown(repo_name, 2)}`\n"
                "Please try again later\\."
            )

            if hasattr(message_or_query, 'edit_message_text'):
                await message_or_query.edit_message_text(error_text, parse_mode="MarkdownV2")
            else:
                await message_or_query.edit_text(error_text, parse_mode="MarkdownV2")

    def create_repo_keyboard(self):
        """Create inline keyboard for repository actions"""
        keyboard = [
            [
                InlineKeyboardButton("👥 Contributors", callback_data="contributors"),
                InlineKeyboardButton("🔀 Pull Requests", callback_data="prs")
            ],
            [
                InlineKeyboardButton("🐛 Issues", callback_data="issues"),
                InlineKeyboardButton("💻 Languages", callback_data="languages")
            ],
            [
                InlineKeyboardButton("🏷️ Releases", callback_data="releases"),
                InlineKeyboardButton("📖 README", callback_data="readme")
            ],
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
        """Handle repository-related callbacks"""
        query = update.callback_query

        if action == "refresh":
            repo = context.user_data.get("current_repo")
            if repo:
                await query.answer()
                await query.edit_message_text("🔄 *Loading\\.\\.\\.*", parse_mode="MarkdownV2")
                await self.show_repository_info(query, repo, context)
            else:
                await query.answer("❌ No repository to refresh")
            return

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
            await handler(update, context)
        else:
            await query.answer("❌ Unknown action")

# Create instance
repository_handler = RepositoryHandler()
