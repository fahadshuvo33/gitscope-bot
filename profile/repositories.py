from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import aiohttp
import logging

logger = logging.getLogger(__name__)


class ProfileRepositories:
    def __init__(self):
        pass

    async def show_user_repos(self, message, username, context, page=1):
        """Show user's public repositories with better loading and pagination"""
        per_page = 10
        await message.edit_text(
            f"🔄 Loading {username}'s repositories...", parse_mode=None
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
                if not user_info:
                    await message.edit_text("❌ Could not load user information")
                    return

                total_repos = user_info.get("public_repos", 0)

                if total_repos == 0:
                    await message.edit_text(
                        f"📂 **{username}'s Repositories**\n\n"
                        f"😔 @{username} has no public repositories yet.\n\n"
                        f"💡 They might have private repos or be new to GitHub!",
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup(
                            [
                                [
                                    InlineKeyboardButton(
                                        "⬅️ Back to Profile",
                                        callback_data="back_to_profile",
                                    )
                                ]
                            ]
                        ),
                    )
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
                    except Exception as e:
                        logger.warning(f"Failed to load repos with sort={sort_by}: {e}")
                        continue

                if not repos:
                    await message.edit_text(
                        f"❌ **Could not load repositories**\n\n"
                        f"Unable to fetch repositories for @{username}\n\n"
                        f"**Possible reasons:**\n"
                        f"• Network timeout\n"
                        f"• GitHub API issues\n"
                        f"• All repositories are private\n\n"
                        f"Try again in a moment.",
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup(
                            [
                                [
                                    InlineKeyboardButton(
                                        "🔄 Try Again",
                                        callback_data=f"user_repos_{username}",
                                    ),
                                    InlineKeyboardButton(
                                        "⬅️ Back to Profile",
                                        callback_data="back_to_profile",
                                    ),
                                ]
                            ]
                        ),
                    )
                    return

                # Calculate pagination
                total_pages = (total_repos + per_page - 1) // per_page
                start_index = (page - 1) * per_page + 1
                end_index = min(start_index + len(repos) - 1, total_repos)

                # Format repositories
                text = f"📂 **{username}'s Repositories**\n"
                text += (
                    f"📊 Showing {start_index}-{end_index} of {total_repos:,} total\n"
                )
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

                            updated_date = datetime.strptime(
                                updated, "%Y-%m-%dT%H:%M:%SZ"
                            )
                            updated_str = updated_date.strftime("%b %d")
                        except:
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

                # Create navigation buttons
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

                # Action buttons
                keyboard.extend(
                    [
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
                    ]
                )

                reply_markup = InlineKeyboardMarkup(keyboard)

                await message.edit_text(
                    text,
                    parse_mode="Markdown",
                    reply_markup=reply_markup,
                    disable_web_page_preview=True,
                )

        except Exception as e:
            logger.error(f"Error fetching repos for {username}: {e}", exc_info=True)
            await message.edit_text(
                f"❌ **Error loading repositories**\n\n"
                f"Could not fetch repositories for @{username}\n\n"
                f"**Error:** {str(e)[:100]}...",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🔄 Try Again", callback_data=f"user_repos_{username}"
                            ),
                            InlineKeyboardButton(
                                "⬅️ Back to Profile", callback_data="back_to_profile"
                            ),
                        ]
                    ]
                ),
            )

    async def show_starred_repos(self, message, username, context, page=1):
        """Show user's starred repositories with pagination"""
        per_page = 10
        await message.edit_text(
            f"🔄 Loading {username}'s starred repositories...", parse_mode=None
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

                if not starred:
                    await message.edit_text(
                        f"⭐ **{username}'s Starred Repositories**\n\n"
                        f"😔 No starred repositories found for @{username}",
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup(
                            [
                                [
                                    InlineKeyboardButton(
                                        "⬅️ Back to Profile",
                                        callback_data="back_to_profile",
                                    )
                                ]
                            ]
                        ),
                    )
                    return

                # Format starred repos
                text = f"⭐ **{username}'s Starred Repositories**\n"
                text += f"📊 Showing {len(starred)} repositories\n\n"

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
                reply_markup = InlineKeyboardMarkup(keyboard)

                await message.edit_text(
                    text,
                    parse_mode="Markdown",
                    reply_markup=reply_markup,
                    disable_web_page_preview=True,
                )

        except Exception as e:
            logger.error(f"Error fetching starred repos for {username}: {e}")
            await message.edit_text(
                f"❌ Error loading starred repositories for @{username}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⬅️ Back to Profile", callback_data="back_to_profile"
                            )
                        ]
                    ]
                ),
            )
