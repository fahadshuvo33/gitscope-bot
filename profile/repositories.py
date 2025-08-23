from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import aiohttp
import logging
import asyncio

# Import the loading system
from utils.loading import show_loading, show_error, show_static_loading

logger = logging.getLogger(__name__)


class ProfileRepositories:
    def __init__(self):
        self.REPOS_ANIMATION = "rocket"  # Rocket animation for repositories
        self.STARRED_ANIMATION = "stars"  # Stars animation for starred repos

    async def show_user_repos(self, message, username, context, page=1):
        """Show user's public repositories with loading animation and pagination"""
        per_page = 10

        # Show static loading first to preserve the window
        await show_static_loading(
            message,
            f"📂 **{username}'s Repositories**",
            "Loading repositories",
            page,
            preserve_content=True,
            animation_type=self.REPOS_ANIMATION,
        )

        # Start animated loading
        loading_task = await show_loading(
            message,
            f"📂 **{username}'s Repositories**",
            "Loading repositories",
            page,
            animation_type=self.REPOS_ANIMATION,
        )

        try:
            from utils.git_api import _make_request_with_retry

            # Use longer timeout for repositories
            timeout = aiohttp.ClientTimeout(total=15, connect=8)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Get user info first to check repo count
                user_info = await _make_request_with_retry(
                    session, f"/users/{username}", timeout=10
                )

                # Stop loading animation gracefully
                if loading_task and not loading_task.done():
                    loading_task.cancel()
                    try:
                        await loading_task
                    except asyncio.CancelledError:
                        pass

                if not user_info:
                    await self._show_data_error(message, username, "repositories", page)
                    return

                total_repos = user_info.get("public_repos", 0)

                if total_repos == 0:
                    await self._show_no_repos(message, username)
                    return

                # Get repositories with multiple sort options
                sort_options = ["updated", "stars", "created"]
                repos = None

                for sort_by in sort_options:
                    try:
                        repos = await _make_request_with_retry(
                            session,
                            f"/users/{username}/repos",
                            params={
                                "sort": sort_by,
                                "per_page": per_page,
                                "page": page,
                                "type": "owner",  # Only show owned repos
                            },
                            timeout=12,
                        )
                        if repos:
                            break
                    except Exception:
                        continue

                if not repos:
                    await self._show_network_error(message, username, "repositories", page)
                    return

                # Calculate pagination
                total_pages = (total_repos + per_page - 1) // per_page
                start_index = (page - 1) * per_page + 1
                end_index = min(start_index + len(repos) - 1, total_repos)

                # Format repositories
                text = f"📂 **{username}'s Repositories**\n"
                text += f"📊 Showing {start_index}-{end_index} of {total_repos:,} total\n"
                if total_pages > 1:
                    text += f"📄 Page {page} of {total_pages}\n"
                text += "\n"

                for i, repo in enumerate(repos, 1):
                    name = repo.get("name", "Unknown")
                    description = repo.get("description", "No description")
                    stars = repo.get("stargazers_count", 0)
                    forks = repo.get("forks_count", 0)
                    language = repo.get("language", "Unknown")
                    updated = repo.get("updated_at", "")
                    is_private = repo.get("private", False)
                    is_fork = repo.get("fork", False)

                    # Truncate description
                    if description and len(description) > 60:
                        description = description[:60] + "..."

                    # Format updated date
                    updated_str = ""
                    if updated:
                        try:
                            from datetime import datetime
                            updated_date = datetime.strptime(updated, "%Y-%m-%dT%H:%M:%SZ")
                            updated_str = updated_date.strftime("%b %d")
                        except Exception:
                            pass

                    # Add repo info
                    repo_emoji = "🔒" if is_private else "🍴" if is_fork else "📦"
                    text += f"{repo_emoji} **{name}**\n"
                    text += f"   {description}\n"

                    # Stats line
                    stats_line = f"   ⭐ {stars}"
                    if forks > 0:
                        stats_line += f" • 🍴 {forks}"
                    if language != "Unknown":
                        stats_line += f" • 💻 {language}"
                    if updated_str:
                        stats_line += f" • 🕒 {updated_str}"
                    text += stats_line + "\n"
                    text += f"   `{username}/{name}`\n\n"

                text += "💡 **Tip:** Copy any repository name to explore!"

                # Create navigation buttons
                keyboard = self._create_repos_keyboard(username, page, total_pages)

                # Update with final content while preserving the window
                try:
                    await message.edit_text(
                        text,
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        disable_web_page_preview=True,
                    )
                except Exception as edit_error:
                    logger.warning(f"Message edit failed: {type(edit_error).__name__}")

        except Exception as e:
            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

            # Log minimal error info
            logger.error(f"Repos error for {username}: {type(e).__name__}")
            await self._show_network_error(message, username, "repositories", page)

    async def show_starred_repos(self, message, username, context, page=1):
        """Show user's starred repositories with loading animation"""
        per_page = 10

        # Show static loading first to preserve the window
        await show_static_loading(
            message,
            f"⭐ **{username}'s Starred Repositories**",
            "Loading starred repos",
            page,
            preserve_content=True,
            animation_type=self.STARRED_ANIMATION,
        )

        # Start animated loading
        loading_task = await show_loading(
            message,
            f"⭐ **{username}'s Starred Repositories**",
            "Loading starred repos",
            page,
            animation_type=self.STARRED_ANIMATION,
        )

        try:
            from utils.git_api import _make_request_with_retry

            timeout = aiohttp.ClientTimeout(total=15, connect=8)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Get starred repos
                starred = await _make_request_with_retry(
                    session,
                    f"/users/{username}/starred",
                    params={"per_page": per_page, "page": page},
                    timeout=12,
                )

                # Stop loading animation gracefully
                if loading_task and not loading_task.done():
                    loading_task.cancel()
                    try:
                        await loading_task
                    except asyncio.CancelledError:
                        pass

                if not starred or len(starred) == 0:
                    await self._show_no_starred(message, username, page)
                    return

                # Format starred repos
                text = f"⭐ **{username}'s Starred Repositories**\n"
                text += f"📊 Showing {len(starred)} repositories\n"
                if page > 1:
                    text += f"📄 Page {page}\n"
                text += "\n"

                for i, repo in enumerate(starred, 1):
                    name = repo.get("full_name", "Unknown")
                    description = repo.get("description", "No description")
                    stars = repo.get("stargazers_count", 0)
                    language = repo.get("language", "Unknown")

                    # Truncate description
                    if description and len(description) > 50:
                        description = description[:50] + "..."

                    # Format stars
                    if stars >= 1000:
                        stars_fmt = f"{stars/1000:.1f}k"
                    else:
                        stars_fmt = str(stars)

                    text += f"{i}. **{name}**\n"
                    text += f"   {description}\n"
                    text += f"   ⭐ {stars_fmt} • 💻 {language}\n"
                    text += f"   `{name}`\n\n"

                text += "💡 **Tip:** These are repositories that caught their attention!"

                keyboard = [
                    [
                        InlineKeyboardButton(
                            "🔄 Refresh", callback_data=f"user_starred_{username}"
                        ),
                        InlineKeyboardButton(
                            "📂 Repositories", callback_data=f"user_repos_{username}"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ Back to Profile", callback_data="back_to_profile"
                        )
                    ],
                ]

                # Update with final content while preserving the window
                try:
                    await message.edit_text(
                        text,
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        disable_web_page_preview=True,
                    )
                except Exception as edit_error:
                    logger.warning(f"Message edit failed: {type(edit_error).__name__}")

        except Exception as e:
            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

            # Log minimal error info
            logger.error(f"Starred repos error for {username}: {type(e).__name__}")
            await self._show_starred_error(message, username, page)

    async def _show_data_error(self, message, username, data_type, page=1):
        """Show data error with action buttons"""
        error_text = await show_error(
            message,
            f"📂 **{username}'s Repositories**",
            "Data Unavailable",
            preserve_content=True,
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 Try Again", callback_data=f"user_repos_{username}"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back to Profile", callback_data="back_to_profile"
                )
            ],
        ]

        try:
            await message.edit_text(
                error_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.warning(f"Error message update failed: {type(e).__name__}")

    async def _show_network_error(self, message, username, data_type, page=1):
        """Show network error with structured message and action buttons"""
        error_text = await show_error(
            message,
            f"📂 **{username}'s Repositories**",
            "Connection Error",
            preserve_content=True,
        )

        callback_suffix = f"_page_{page}" if page > 1 else ""
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 Retry", callback_data=f"user_repos_{username}{callback_suffix}"
                ),
                InlineKeyboardButton(
                    "⭐ Try Starred", callback_data=f"user_starred_{username}"
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back to Profile", callback_data="back_to_profile"
                )
            ],
        ]

        try:
            await message.edit_text(
                error_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.warning(f"Error display failed: {type(e).__name__}")

    async def _show_starred_error(self, message, username, page=1):
        """Show starred repositories error"""
        error_text = await show_error(
            message,
            f"⭐ **{username}'s Starred Repositories**",
            "Loading Error",
            preserve_content=True,
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 Retry", callback_data=f"user_starred_{username}"
                ),
                InlineKeyboardButton(
                    "📂 Try Repos", callback_data=f"user_repos_{username}"
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back to Profile", callback_data="back_to_profile"
                )
            ],
        ]

        try:
            await message.edit_text(
                error_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.warning(f"Starred error display failed: {type(e).__name__}")

    async def _show_no_repos(self, message, username):
        """Show no repositories message"""
        text = (
            f"📂 **{username}'s Repositories**\n\n"
            f"😔 @{username} has no public repositories yet.\n\n"
            f"💡 **Tip:** They might have private repos or be new to GitHub!"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "⭐ Check Starred", callback_data=f"user_starred_{username}"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back to Profile", callback_data="back_to_profile"
                )
            ],
        ]

        try:
            await message.edit_text(
                text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.warning(f"No repos message failed: {type(e).__name__}")

    async def _show_no_starred(self, message, username, page=1):
        """Show no starred repositories message"""
        if page == 1:
            text = (
                f"⭐ **{username}'s Starred Repositories**\n\n"
                f"😔 No starred repositories found for @{username}\n\n"
                f"💡 **Tip:** They haven't starred any repositories yet!"
            )
        else:
            text = (
                f"⭐ **{username}'s Starred Repositories**\n"
                f"📄 Page {page}\n\n"
                f"😔 No more starred repositories to show.\n\n"
                f"You've reached the end!"
            )

        keyboard = [
            [
                InlineKeyboardButton(
                    "📂 Check Repos", callback_data=f"user_repos_{username}"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back to Profile", callback_data="back_to_profile"
                )
            ],
        ]

        if page > 1:
            keyboard.insert(0, [
                InlineKeyboardButton(
                    "⬅️ Previous Page",
                    callback_data=f"user_starred_{username}_page_{page-1}"
                )
            ])

        try:
            await message.edit_text(
                text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.warning(f"No starred message failed: {type(e).__name__}")

    def _create_repos_keyboard(self, username, page, total_pages):
        """Create pagination keyboard for repositories"""
        keyboard = []

        # Pagination buttons
        if total_pages > 1:
            nav_buttons = []
            if page > 1:
                nav_buttons.append(
                    InlineKeyboardButton(
                        "⬅️ Previous",
                        callback_data=f"user_repos_{username}_page_{page-1}",
                    )
                )
            if page < total_pages:
                nav_buttons.append(
                    InlineKeyboardButton(
                        "➡️ Next",
                        callback_data=f"user_repos_{username}_page_{page+1}",
                    )
                )
            if nav_buttons:
                keyboard.append(nav_buttons)

        # Quick jump for large lists
        if total_pages > 3:
            jump_buttons = []
            if page > 2:
                jump_buttons.append(
                    InlineKeyboardButton(
                        "⏮️ First", callback_data=f"user_repos_{username}_page_1"
                    )
                )
            if page < total_pages - 1:
                jump_buttons.append(
                    InlineKeyboardButton(
                        "⏭️ Last",
                        callback_data=f"user_repos_{username}_page_{total_pages}",
                    )
                )
            if jump_buttons:
                keyboard.append(jump_buttons)

        # Action buttons
        keyboard.extend([
            [
                InlineKeyboardButton(
                    "🔄 Refresh", callback_data=f"user_repos_{username}"
                ),
                InlineKeyboardButton(
                    "⭐ Starred", callback_data=f"user_starred_{username}"
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back to Profile", callback_data="back_to_profile"
                )
            ],
        ])

        return keyboard
