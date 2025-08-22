from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import aiohttp
import logging

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
        """Handle trending repositories for specific language with optional time range"""
        query = update.callback_query
        await query.answer()

        # Get language name
        lang_name = self.get_language_name(language)

        time_labels = {"daily": "Daily", "weekly": "Weekly", "monthly": "Monthly"}
        time_label = time_labels.get(time_range, "Weekly")

        # Show loading
        loading_text = (
            f"🔄 Fetching {time_label.lower()} trending {lang_name} repositories..."
        )
        await query.edit_message_text(loading_text, parse_mode=None)

        try:
            # Create session with better timeout handling
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                repos = await self.fetch_trending_repos(session, language, time_range)

            if not repos:
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "📊 Try Other Languages", callback_data="trending"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔄 Retry",
                            callback_data=f"trending_{language}_{time_range}",
                        )
                    ],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(
                    f"❌ No trending repositories found for {lang_name}.\n\n"
                    "This might be due to:\n"
                    "• Network connectivity issues\n"
                    "• GitHub API rate limits\n"
                    "• No repos matching the criteria\n\n"
                    "Try again or select a different language.",
                    parse_mode=None,
                    reply_markup=reply_markup,
                )
                return

            # Format trending repos with copyable names
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

            # Navigation buttons only
            keyboard = [
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
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=reply_markup,
                disable_web_page_preview=True,
            )

        except aiohttp.ClientConnectorError as e:
            logger.error(
                f"Network connection error for {language}_{time_range}: {str(e)}"
            )
            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔄 Try Again",
                        callback_data=f"trending_{language}_{time_range}",
                    )
                ],
                [InlineKeyboardButton("📊 Other Languages", callback_data="trending")],
                [
                    InlineKeyboardButton(
                        "⬅️ Back to Start", callback_data="back_to_start"
                    )
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                "🌐 Network Error\n\n"
                "Unable to connect to GitHub API.\n"
                "Please check your internet connection and try again.\n\n"
                "This could be:\n"
                "• Temporary network issue\n"
                "• DNS resolution problem\n"
                "• GitHub API temporarily unavailable",
                parse_mode=None,
                reply_markup=reply_markup,
            )

        except Exception as e:
            logger.error(
                f"Error in handle_trending_by_language for {language}_{time_range}: {str(e)}",
                exc_info=True,
            )

            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔄 Try Again",
                        callback_data=f"trending_{language}_{time_range}",
                    )
                ],
                [InlineKeyboardButton("📊 Other Languages", callback_data="trending")],
                [
                    InlineKeyboardButton(
                        "⬅️ Back to Start", callback_data="back_to_start"
                    )
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                "😔 Something went wrong while fetching repositories.\n\n"
                "Please try again or select a different language.",
                parse_mode=None,
                reply_markup=reply_markup,
            )

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


# Create instance
trending_handler = TrendingHandler()
