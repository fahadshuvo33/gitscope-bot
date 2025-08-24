from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import aiohttp
import logging
import asyncio

# Import the loading system
from utils.loading import show_loading, show_static_loading

logger = logging.getLogger(__name__)


class TrendingHandler:

    def __init__(self):
        # Single centralized language mapping
        self.languages = {
            "python": {"display": "🐍 Python", "search": "Python"},
            "javascript": {"display": "☕ JavaScript", "search": "JavaScript"},
            "typescript": {"display": "⚡ TypeScript", "search": "TypeScript"},
            "java": {"display": "☕ Java", "search": "Java"},
            "cpp": {"display": "🔧 C++", "search": "C++"},  # GitHub search term
            "go": {"display": "🐹 Go", "search": "Go"},
            "rust": {"display": "🦀 Rust", "search": "Rust"},
            "ruby": {"display": "💎 Ruby", "search": "Ruby"},
            "php": {"display": "🐘 PHP", "search": "PHP"},
            "swift": {"display": "🍎 Swift", "search": "Swift"},
            "kotlin": {"display": "🟣 Kotlin", "search": "Kotlin"},
            "csharp": {"display": "💜 C#", "search": "C#"},  # GitHub search term
            "dart": {"display": "🎯 Dart", "search": "Dart"},
            "scala": {"display": "🔴 Scala", "search": "Scala"},
        }

        self.TRENDING_ANIMATION = "fire"  # Fire animation for trending repositories

    def get_language_name(self, language):
        """Get display name for language"""
        if language == "all":
            return "All Languages"
        return self.languages.get(language, {}).get("display", language.title())

    def get_search_term(self, language):
        """Get GitHub search term for language"""
        if language == "all":
            return None
        return self.languages.get(language, {}).get("search", language.title())

    async def handle_trending_by_language(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        language: str,
        time_range: str = "weekly",
    ):
        """Handle trending repositories for specific language with loading animation"""
        query = update.callback_query
        await query.answer()

        # Get language name
        lang_name = self.get_language_name(language)

        time_labels = {"daily": "Daily", "weekly": "Weekly", "monthly": "Monthly"}
        time_label = time_labels.get(time_range, "Weekly")

        # Show static loading first to preserve the window
        await show_static_loading(
            query.message,
            f"📈 **{time_label} Trending {lang_name}**",
            "Loading trending repositories",
            preserve_content=True,
            animation_type=self.TRENDING_ANIMATION,
        )

        # Start animated loading
        loading_task = await show_loading(
            query.message,
            f"📈 **{time_label} Trending {lang_name}**",
            "Loading trending repositories",
            animation_type=self.TRENDING_ANIMATION,
        )

        try:
            # Create session with better timeout handling
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                repos = await self.fetch_trending_repos(session, language, time_range)

            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

            if not repos:
                await self._show_trending_error(
                    query.message, lang_name, time_label, language, time_range, "No Repositories Found"
                )
                return

            # Format and display trending repos
            text = self._build_trending_content(repos, lang_name, time_label)
            keyboard = self._build_trending_keyboard(language, time_range)

            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True,
            )

        except aiohttp.ClientConnectorError as e:
            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

            logger.error(f"Network connection error for {language}_{time_range}: {str(e)}")
            await self._show_trending_error(
                query.message, lang_name, time_label, language, time_range, "Network Error"
            )

        except Exception as e:
            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

            logger.error(f"Error in handle_trending_by_language for {language}_{time_range}: {str(e)}", exc_info=True)
            await self._show_trending_error(
                query.message, lang_name, time_label, language, time_range, "Fetch Error"
            )

    def _build_trending_content(self, repos, lang_name, time_label):
        """Build the trending repositories content"""
        text = f"📈 {time_label} Trending {lang_name}\n\n"
        text += f"🔥 Copy any repository name to explore it:\n\n"

        for i, repo in enumerate(repos[:8], 1):
            name = repo.get("full_name", "Unknown")
            description = repo.get("description", "No description")
            stars = repo.get("stargazers_count", 0)
            language_used = repo.get("language", "Unknown")

            # Truncate description
            if description and len(description) > 60:
                description = description[:60] + "..."

            # Format stars
            if stars >= 1000000:
                stars_fmt = f"{stars/1000000:.1f}M"
            elif stars >= 1000:
                stars_fmt = f"{stars/1000:.1f}K"
            else:
                stars_fmt = str(stars)

            # Add to text display with copyable repo name
            text += f"{i}. `{name}`\n"
            text += f"   {description}\n"
            text += f"   ⭐ {stars_fmt} • 💻 {language_used}\n\n"

        return text

    def _build_trending_keyboard(self, language, time_range):
        """Build the trending repositories keyboard"""
        return [
            [
                InlineKeyboardButton(
                    "🔄 Refresh", callback_data=f"trending_{language}"
                ),
                InlineKeyboardButton("📊 Languages", callback_data="trending"),
            ],
            [
                InlineKeyboardButton(
                    "📊 Daily", callback_data=f"trending_{language}_daily"
                ),
                InlineKeyboardButton(
                    "📈 Weekly", callback_data=f"trending_{language}_weekly"
                ),
                InlineKeyboardButton(
                    "📅 Monthly", callback_data=f"trending_{language}_monthly"
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back to Start", callback_data="back_to_start"
                )
            ],
        ]

    async def _show_trending_error(self, message, lang_name, time_label, language, time_range, error_type):
        """Show trending error with structured message and action buttons"""
        error_text = f"📈 **{time_label} Trending {lang_name}**\n\n"
        error_text += f"❌ **{error_type}**\n\n"

        if error_type == "No Repositories Found":
            error_text += f"No trending repositories found for {lang_name}.\n\n"
            error_text += f"**Possible causes:**\n"
            error_text += f"• Limited repositories in this language\n"
            error_text += f"• GitHub API rate limits\n"
            error_text += f"• Network connectivity issues\n"
            error_text += f"• No repos matching the criteria\n\n"
            error_text += f"💡 **Tip:** Try a different language or time range!"
        elif error_type == "Network Error":
            error_text += f"Unable to connect to GitHub API.\n\n"
            error_text += f"**Possible causes:**\n"
            error_text += f"• Temporary network issue\n"
            error_text += f"• DNS resolution problem\n"
            error_text += f"• GitHub API temporarily unavailable\n\n"
            error_text += f"💡 **Tip:** Check your connection and try again!"
        else:
            error_text += f"Unable to fetch trending repositories.\n\n"
            error_text += f"**Possible causes:**\n"
            error_text += f"• GitHub API temporarily unavailable\n"
            error_text += f"• Rate limit exceeded\n"
            error_text += f"• Server error\n\n"
            error_text += f"💡 **Tip:** Try again in a few moments!"

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 Try Again",
                    callback_data=f"trending_{language}_{time_range}",
                ),
                InlineKeyboardButton("📊 Other Languages", callback_data="trending"),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back to Start", callback_data="back_to_start"
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
        except Exception:
            pass  # Silent fail for error display

    async def fetch_trending_repos(self, session, language, time_range="weekly"):
        """Fetch trending repositories with network error handling"""
        try:
            from utils.git_api import search_repositories
            from datetime import datetime, timedelta

            # Get search term using centralized mapping
            actual_lang = self.get_search_term(language)

            # Simpler, more reliable search strategies
            if time_range == "daily":
                days_back = 7
                min_stars = 50
            elif time_range == "weekly":
                days_back = 30
                min_stars = 100
            else:  # monthly
                days_back = 365
                min_stars = 500

            recent_date = (datetime.now() - timedelta(days=days_back)).strftime(
                "%Y-%m-%d"
            )

            if actual_lang:
                strategies = [
                    f"language:{actual_lang} stars:>{min_stars}",
                    f"language:{actual_lang} stars:>{min_stars//2}",
                    f"language:{actual_lang}",
                ]
            else:
                strategies = [
                    f"stars:>{min_stars}",
                    f"stars:>{min_stars//2}",
                    "stars:>50",
                ]

            # Try each strategy
            for i, query in enumerate(strategies):
                try:
                    repos = await search_repositories(
                        session, query, limit=10, sort="stars"
                    )
                    if repos and len(repos) >= 3:
                        return repos
                except Exception as e:
                    logger.warning(f"Search strategy {i+1} failed: {e}")
                    continue

            return None

        except Exception as e:
            logger.error(f"Error in fetch_trending_repos: {e}")
            return None

    async def show_loading_trending(self, message, lang_name, time_label):
        """Show loading state for trending - useful for external calls"""
        await show_static_loading(
            message,
            f"📈 **{time_label} Trending {lang_name}**",
            "Loading trending repositories",
            preserve_content=True,
            animation_type=self.TRENDING_ANIMATION,
        )


# Create instance
trending_handler = TrendingHandler()
