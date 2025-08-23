from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import aiohttp
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ProfileStats:
    def __init__(self):
        pass

    async def show_contribution_stats(self, message, username, context):
        """Show user contribution statistics and activity"""
        await message.edit_text(
            f"🔄 Loading {username}'s activity stats...", parse_mode=None
        )

        try:
            from utils.git_api import _make_request_with_retry

            async with aiohttp.ClientSession() as session:
                # Get user info for basic stats
                user_data = context.user_data.get("current_user")
                if not user_data:
                    user_data = await _make_request_with_retry(
                        session, f"/users/{username}"
                    )

                if not user_data:
                    await message.edit_text("❌ Could not load user data")
                    return

                # Get recent events/activity
                events = await _make_request_with_retry(
                    session, f"/users/{username}/events/public", params={"per_page": 30}
                )

                # Process statistics
                stats = await self._process_user_stats(user_data, events)

                # Format stats display
                text = f"📊 **{username}'s GitHub Statistics**\n\n"

                # Basic stats
                text += "📈 **Profile Stats**\n"
                text += f"┌─ 📂 **{user_data.get('public_repos', 0):,}** public repositories\n"
                text += f"├─ 📄 **{user_data.get('public_gists', 0):,}** public gists\n"
                text += f"├─ 👥 **{user_data.get('followers', 0):,}** followers\n"
                text += f"└─ 👤 **{user_data.get('following', 0):,}** following\n\n"

                # Activity stats
                if events:
                    text += "🎯 **Recent Activity** (Last 30 events)\n"
                    text += f"┌─ 📝 **{stats['commits']}** commits\n"
                    text += f"├─ 🔀 **{stats['pull_requests']}** pull requests\n"
                    text += f"├─ 🐛 **{stats['issues']}** issues created\n"
                    text += f"├─ ⭐ **{stats['stars']}** repositories starred\n"
                    text += f"├─ 🍴 **{stats['forks']}** forks created\n"
                    text += f"└─ 🎉 **{stats['releases']}** releases published\n\n"

                    # Most active repositories
                    if stats["top_repos"]:
                        text += "🔥 **Most Active Repositories**\n"
                        for i, (repo, count) in enumerate(stats["top_repos"][:3], 1):
                            text += f"{i}. **{repo}** ({count} events)\n"
                        text += "\n"
                else:
                    text += (
                        "🎯 **Recent Activity**\nNo recent public activity found.\n\n"
                    )

                # Account age and info
                created_at = user_data.get("created_at", "")
                if created_at:
                    try:
                        created_date = datetime.strptime(
                            created_at, "%Y-%m-%dT%H:%M:%SZ"
                        )
                        years_on_github = (datetime.now() - created_date).days // 365
                        text += (
                            f"📅 **Account Age:** {years_on_github} years on GitHub\n"
                        )
                        text += (
                            f"🗓️ **Joined:** {created_date.strftime('%B %d, %Y')}\n\n"
                        )
                    except:
                        pass

                # Additional insights
                if user_data.get("public_repos", 0) > 0:
                    avg_stars = (
                        sum(repo.get("stargazers_count", 0) for repo in [])
                        / max(user_data.get("public_repos", 1), 1)
                        if events
                        else 0
                    )
                    text += f"💡 **Insights**\n"
                    if user_data.get("followers", 0) > user_data.get("following", 0):
                        text += (
                            "• More followers than following - Popular developer! 🌟\n"
                        )
                    if user_data.get("public_repos", 0) > 50:
                        text += "• Very active coder with 50+ repositories! 💻\n"
                    elif user_data.get("public_repos", 0) > 10:
                        text += "• Active developer with multiple projects! ⚡\n"

                keyboard = [
                    [
                        InlineKeyboardButton(
                            "🔄 Refresh", callback_data=f"user_stats_{username}"
                        )
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
            logger.error(f"Error fetching stats for {username}: {e}")
            await message.edit_text(
                f"❌ Error loading statistics for @{username}",
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

    async def _process_user_stats(self, user_data, events):
        """Process user events to generate statistics"""
        stats = {
            "commits": 0,
            "pull_requests": 0,
            "issues": 0,
            "stars": 0,
            "forks": 0,
            "releases": 0,
            "top_repos": [],
        }

        if not events:
            return stats

        repo_activity = {}

        for event in events:
            event_type = event.get("type", "")
            repo_name = event.get("repo", {}).get("name", "Unknown")

            # Count repository activity
            if repo_name != "Unknown":
                repo_activity[repo_name] = repo_activity.get(repo_name, 0) + 1

            # Count different types of activities
            if event_type == "PushEvent":
                # Count commits in push
                payload = event.get("payload", {})
                commits = len(payload.get("commits", []))
                stats["commits"] += commits
            elif event_type == "PullRequestEvent":
                stats["pull_requests"] += 1
            elif event_type == "IssuesEvent":
                stats["issues"] += 1
            elif event_type == "WatchEvent":
                stats["stars"] += 1
            elif event_type == "ForkEvent":
                stats["forks"] += 1
            elif event_type == "ReleaseEvent":
                stats["releases"] += 1

        # Get top repositories by activity
        stats["top_repos"] = sorted(
            repo_activity.items(), key=lambda x: x[1], reverse=True
        )

        return stats
