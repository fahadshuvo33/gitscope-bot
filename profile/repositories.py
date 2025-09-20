# profile/repositories.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import aiohttp
import logging
from datetime import datetime

# Import the loading system and formatting utilities
from utils.loading import with_loading
from utils.formatting import _escape_markdown_v2, add_admin_context

logger = logging.getLogger(__name__)


class ProfileRepositories:
    def __init__(self):
        self.REPOS_ANIMATION = "rocket"  # Rocket animation for repositories
        self.STARRED_ANIMATION = "stars"  # Stars animation for starred repos

    @with_loading("Loading repositories", 1.5)
    async def show_user_repos(self, update_or_message, username, context, page=1, is_admin_profile=False):
        """Show user's public repositories with loading animation and pagination"""
        per_page = 10
        
        # Get the loading message from context (set by decorator)
        message = context.user_data.get('_loading_message')
        if not message:
            message = update_or_message

        try:
            from utils.git_api import _make_request_with_retry

            # Use longer timeout for repositories
            timeout = aiohttp.ClientTimeout(total=15, connect=8)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Get user info first to check repo count
                user_info = await _make_request_with_retry(
                    session, f"/users/{username}", timeout=10
                )

                if not user_info:
                    await self._show_data_error(message, username, "repositories", page, is_admin_profile)
                    return

                total_repos = user_info.get("public_repos", 0)

                if total_repos == 0:
                    await self._show_no_repos(message, username, is_admin_profile)
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
                    await self._show_network_error(message, username, "repositories", page, is_admin_profile)
                    return

                # Calculate pagination
                total_pages = (total_repos + per_page - 1) // per_page
                start_index = (page - 1) * per_page + 1
                end_index = min(start_index + len(repos) - 1, total_repos)

                # Format repositories
                base_text = f"📂 **{_escape_markdown_v2(username)}'s Repositories**\n"
                base_text += f"📊 Showing {start_index}-{end_index} of {total_repos:,} total\n"
                if total_pages > 1:
                    base_text += f"📄 Page {page} of {total_pages}\n"
                base_text += "\n"

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
                            updated_date = datetime.strptime(updated, "%Y-%m-%dT%H:%M:%SZ")
                            updated_str = updated_date.strftime("%b %d")
                        except Exception:
                            pass

                    # Add repo info
                    repo_emoji = "🔒" if is_private else "🍴" if is_fork else "📦"
                    base_text += f"{repo_emoji} **{_escape_markdown_v2(name)}**\n"
                    base_text += f"   {_escape_markdown_v2(description)}\n"

                    # Stats line
                    stats_line = f"   ⭐ {stars}"
                    if forks > 0:
                        stats_line += f" • 🍴 {forks}"
                    if language != "Unknown":
                        stats_line += f" • 💻 {_escape_markdown_v2(language)}"
                    if updated_str:
                        stats_line += f" • 🕒 {updated_str}"
                    base_text += stats_line + "\n"
                    base_text += f"   `{username}/{name}`\n\n"

                base_text += "💡 **Tip:** Copy any repository name to explore!"

                # Add admin context if needed
                text = add_admin_context(base_text, username) if is_admin_profile else base_text

                # Create navigation buttons
                keyboard = self._create_repos_keyboard(username, page, total_pages, is_admin_profile)

                # Update with final content
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
            logger.error(f"Repos error for {username}: {type(e).__name__}")
            await self._show_network_error(message, username, "repositories", page, is_admin_profile)

    @with_loading("Loading starred repos", 1.3)
    async def show_starred_repos(self, update_or_message, username, context, page=1, is_admin_profile=False):
        """Show user's starred repositories with loading animation"""
        per_page = 10
        
        # Get the loading message from context (set by decorator)
        message = context.user_data.get('_loading_message')
        if not message:
            message = update_or_message

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

                if not starred or len(starred) == 0:
                    await self._show_no_starred(message, username, page, is_admin_profile)
                    return

                # Format starred repos
                base_text = f"⭐ **{_escape_markdown_v2(username)}'s Starred Repositories**\n"
                base_text += f"📊 Showing {len(starred)} repositories\n"
                if page > 1:
                    base_text += f"📄 Page {page}\n"
                base_text += "\n"

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

                    base_text += f"{i}. **{_escape_markdown_v2(name)}**\n"
                    base_text += f"   {_escape_markdown_v2(description)}\n"
                    base_text += f"   ⭐ {stars_fmt} • 💻 {_escape_markdown_v2(language)}\n"
                    base_text += f"   `{name}`\n\n"

                base_text += "💡 **Tip:** These are repositories that caught their attention!"

                # Add admin context if needed
                text = add_admin_context(base_text, username) if is_admin_profile else base_text

                keyboard = self._create_starred_keyboard(username, page, is_admin_profile)

                # Update with final content
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
            logger.error(f"Starred repos error for {username}: {type(e).__name__}")
            await self._show_starred_error(message, username, page, is_admin_profile)

    # ==================== ERROR HANDLERS ====================

    async def _show_data_error(self, message, username, data_type, page=1, is_admin_profile=False):
        """Show data error with action buttons"""
        base_text = (
            f"📂 **{_escape_markdown_v2(username)}'s Repositories**\n\n"
            f"❌ **Data Unavailable**\n\n"
            f"Unable to fetch repository information.\n\n"
            f"**Possible causes:**\n"
            f"• User profile not accessible\n"
            f"• API rate limiting\n"
            f"• Temporary server issues\n\n"
            f"💡 **Tip:** Try refreshing or check back later!"
        )

        error_text = add_admin_context(base_text, username) if is_admin_profile else base_text

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

        if is_admin_profile:
            keyboard.insert(0, [
                InlineKeyboardButton("📊 Admin Repo Stats", callback_data=f"admin_repo_stats_{username}"),
                InlineKeyboardButton("💾 Export Repos", callback_data=f"admin_export_repos_{username}")
            ])

        try:
            await message.edit_text(
                error_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.warning(f"Error message update failed: {type(e).__name__}")

    async def _show_network_error(self, message, username, data_type, page=1, is_admin_profile=False):
        """Show network error with structured message and action buttons"""
        base_text = (
            f"📂 **{_escape_markdown_v2(username)}'s Repositories**\n\n"
            f"❌ **Connection Error**\n\n"
            f"Unable to connect to GitHub API.\n\n"
            f"**Possible causes:**\n"
            f"• Network connection issues\n"
            f"• GitHub API temporarily unavailable\n"
            f"• Request timeout\n\n"
            f"💡 **Tip:** Check your connection and try again!"
        )

        error_text = add_admin_context(base_text, username) if is_admin_profile else base_text

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

    async def _show_starred_error(self, message, username, page=1, is_admin_profile=False):
        """Show starred repositories error"""
        base_text = (
            f"⭐ **{_escape_markdown_v2(username)}'s Starred Repositories**\n\n"
            f"❌ **Loading Error**\n\n"
            f"Unable to load starred repositories.\n\n"
            f"**Possible causes:**\n"
            f"• Network connection issues\n"
            f"• API rate limiting\n"
            f"• Server timeout\n\n"
            f"💡 **Tip:** Try again or check their repositories!"
        )

        error_text = add_admin_context(base_text, username) if is_admin_profile else base_text

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

    async def _show_no_repos(self, message, username, is_admin_profile=False):
        """Show no repositories message"""
        base_text = (
            f"📂 **{_escape_markdown_v2(username)}'s Repositories**\n\n"
            f"😔 @{username} has no public repositories yet.\n\n"
            f"💡 **Tip:** They might have private repos or be new to GitHub!"
        )

        text = add_admin_context(base_text, username) if is_admin_profile else base_text

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

    async def _show_no_starred(self, message, username, page=1, is_admin_profile=False):
        """Show no starred repositories message"""
        if page == 1:
            base_text = (
                f"⭐ **{_escape_markdown_v2(username)}'s Starred Repositories**\n\n"
                f"😔 No starred repositories found for @{username}\n\n"
                f"💡 **Tip:** They haven't starred any repositories yet!"
            )
        else:
            base_text = (
                f"⭐ **{_escape_markdown_v2(username)}'s Starred Repositories**\n"
                f"📄 Page {page}\n\n"
                f"😔 No more starred repositories to show.\n\n"
                f"You've reached the end!"
            )

        text = add_admin_context(base_text, username) if is_admin_profile else base_text

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

    # ==================== KEYBOARD GENERATORS ====================

    def _create_repos_keyboard(self, username, page, total_pages, is_admin_profile=False):
        """Create pagination keyboard for repositories"""
        keyboard = []

        # Admin buttons first
        if is_admin_profile:
            keyboard.append([
                InlineKeyboardButton("📊 Repo Analytics", callback_data=f"admin_repo_analytics_{username}"),
                InlineKeyboardButton("💾 Export List", callback_data=f"admin_export_repos_{username}")
            ])

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

    def _create_starred_keyboard(self, username, is_admin_profile=False):
        """Create keyboard for starred repositories"""
        keyboard = []

        # Admin buttons first
        if is_admin_profile:
            keyboard.append([
                InlineKeyboardButton("📊 Starred Analytics", callback_data=f"admin_starred_analytics_{username}"),
                InlineKeyboardButton("💾 Export Starred", callback_data=f"admin_export_starred_{username}")
            ])

        keyboard.extend([
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
        ])

        return keyboard

    # ==================== UTILITY METHODS ====================

    def format_repo_stats(self, repos_data):
        """Format repository statistics for quick display"""
        if not repos_data:
            return "No repositories data"
        
        total_stars = sum(repo.get('stargazers_count', 0) for repo in repos_data)
        total_forks = sum(repo.get('forks_count', 0) for repo in repos_data)
        languages = set(repo.get('language') for repo in repos_data if repo.get('language'))
        
        return f"📦 {len(repos_data)} repos • ⭐ {total_stars} stars • 🍴 {total_forks} forks • 💻 {len(languages)} languages"

    def get_top_languages(self, repos_data, limit=5):
        """Get top programming languages from repositories"""
        if not repos_data:
            return []
        
        language_count = {}
        for repo in repos_data:
            lang = repo.get('language')
            if lang and lang != 'Unknown':
                language_count[lang] = language_count.get(lang, 0) + 1
        
        # Sort by count and return top languages
        sorted_langs = sorted(language_count.items(), key=lambda x: x[1], reverse=True)
        return sorted_langs[:limit]

    def get_most_starred_repo(self, repos_data):
        """Get the most starred repository"""
        if not repos_data:
            return None
        
        return max(repos_data, key=lambda repo: repo.get('stargazers_count', 0))

    def calculate_repo_activity(self, repos_data):
        """Calculate repository activity metrics"""
        if not repos_data:
            return {"recent_activity": 0, "total_activity": 0}
        
        from datetime import datetime, timedelta
        
        now = datetime.now()
        recent_threshold = now - timedelta(days=30)
        recent_activity = 0
        
        for repo in repos_data:
            updated_at = repo.get('updated_at')
            if updated_at:
                try:
                    updated_date = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ")
                    if updated_date > recent_threshold:
                        recent_activity += 1
                except Exception:
                    continue
        
        return {
            "recent_activity": recent_activity,
            "total_repos": len(repos_data),
            "activity_percentage": (recent_activity / len(repos_data)) * 100 if repos_data else 0
        }

    async def get_repository_summary(self, username, limit=5):
        """Get a quick summary of user's top repositories"""
        try:
            from utils.git_api import _make_request_with_retry
            import aiohttp
            
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                repos = await _make_request_with_retry(
                    session,
                    f"/users/{username}/repos",
                    params={"sort": "stars", "per_page": limit, "type": "owner"},
                    timeout=8,
                )
                
                if repos:
                    return {
                        "count": len(repos),
                        "top_repo": self.get_most_starred_repo(repos),
                        "languages": self.get_top_languages(repos, 3),
                        "stats": self.format_repo_stats(repos)
                    }
                
                return None
                
        except Exception as e:
            logger.debug(f"Repository summary error for {username}: {type(e).__name__}")
            return None

    def format_repository_for_display(self, repo, index=None):
        """Format a single repository for display"""
        if not repo:
            return "Unknown repository"
        
        name = repo.get("name", "Unknown")
        description = repo.get("description", "No description")
        stars = repo.get("stargazers_count", 0)
        language = repo.get("language", "Unknown")
        is_fork = repo.get("fork", False)
        is_private = repo.get("private", False)
        
        # Truncate long descriptions
        if len(description) > 50:
            description = description[:50] + "..."
        
        # Format display
        prefix = f"{index}. " if index else ""
        repo_emoji = "🔒" if is_private else "🍴" if is_fork else "📦"
        
        formatted = f"{prefix}{repo_emoji} **{_escape_markdown_v2(name)}**\n"
        formatted += f"   {_escape_markdown_v2(description)}\n"
        formatted += f"   ⭐ {stars} • 💻 {_escape_markdown_v2(language)}"
        
        return formatted


# Create instance
profile_repositories = ProfileRepositories()
                