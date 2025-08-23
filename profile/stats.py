from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import aiohttp
import logging
import asyncio
from datetime import datetime, timedelta

# Import the loading system
from utils.loading import show_loading, show_static_loading

logger = logging.getLogger(__name__)


class ProfileStats:
    def __init__(self):
        self.STATS_ANIMATION = "tech"  # Technical animation for stats

    async def show_contribution_stats(self, message, username, context):
        """Show user contribution statistics and activity with loading animation"""

        # Show static loading first to preserve the window
        await show_static_loading(
            message,
            f"📊 **{username}'s GitHub Statistics**",
            "Loading stats",
            preserve_content=True,
            animation_type=self.STATS_ANIMATION,
        )

        # Start animated loading
        loading_task = await show_loading(
            message,
            f"📊 **{username}'s GitHub Statistics**",
            "Loading stats",
            animation_type=self.STATS_ANIMATION,
        )

        try:
            from utils.git_api import _make_request_with_retry

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15, connect=5)
            ) as session:
                # Get user info for basic stats
                user_data = context.user_data.get("current_user")
                if not user_data:
                    user_data = await _make_request_with_retry(
                        session, f"/users/{username}", timeout=10
                    )

                if not user_data:
                    # Stop loading animation gracefully
                    await self._stop_loading_safely(loading_task)
                    await self._show_data_error(message, username, "user data")
                    return

                # Get recent events/activity
                events = await _make_request_with_retry(
                    session, f"/users/{username}/events/public",
                    params={"per_page": 30}, timeout=10
                )

                # Stop loading animation gracefully
                await self._stop_loading_safely(loading_task)

                # Process statistics
                stats = await self._process_user_stats(user_data, events)

                # Format stats display with visual separator
                text = f"📊 **{username}'s GitHub Statistics**\n"
                text += f"{'═' * 30}\n\n"

                # Add achievement badges
                achievements = []
                if user_data.get('public_repos', 0) > 50:
                    achievements.append("🏆 Repository Master")
                if user_data.get('followers', 0) > 100:
                    achievements.append("⭐ Popular Developer")
                if stats.get('commits', 0) > 20:
                    achievements.append("💻 Active Coder")
                if user_data.get('public_repos', 0) > 10 and user_data.get('followers', 0) > 50:
                    achievements.append("🌟 Rising Star")

                if achievements:
                    text += "🎯 **Achievements**\n"
                    for achievement in achievements:
                        text += f"• {achievement}\n"
                    text += "\n"

                # Basic stats
                text += "📈 **Profile Overview**\n"
                text += f"┌─ 📂 **{user_data.get('public_repos', 0):,}** public repositories\n"
                text += f"├─ 📄 **{user_data.get('public_gists', 0):,}** public gists\n"
                text += f"├─ 👥 **{user_data.get('followers', 0):,}** followers\n"
                text += f"└─ 👤 **{user_data.get('following', 0):,}** following\n\n"

                # Recent commits with actual work
                recent_commits = await self._get_recent_commits(session, username)
                if recent_commits:
                    text += "🔥 **Recent Work**\n"
                    for i, commit in enumerate(recent_commits[:4], 1):
                        repo_name = commit['repo'].split('/')[-1] if '/' in commit['repo'] else commit['repo']
                        commit_msg = commit['message']
                        # Clean up commit message
                        if len(commit_msg) > 45:
                            commit_msg = commit_msg[:45] + "..."
                        text += f"├─ **{repo_name}**: {commit_msg}\n"
                    text += "\n"

                # Activity stats
                if events:
                    text += "🎯 **Activity Summary** (Last 30 events)\n"
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
                    text += "🎯 **Recent Activity**\nNo recent public activity found.\n\n"

                # Account age and info
                created_at = user_data.get("created_at", "")
                years_on_github = 0
                if created_at:
                    try:
                        created_date = datetime.strptime(
                            created_at, "%Y-%m-%dT%H:%M:%SZ"
                        )
                        years_on_github = (datetime.now() - created_date).days // 365
                        text += f"📅 **Account Info**\n"
                        text += f"├─ **Age:** {years_on_github} years on GitHub\n"
                        text += f"└─ **Joined:** {created_date.strftime('%B %d, %Y')}\n\n"
                    except Exception:
                        # Silent fail for date parsing
                        pass

                # Additional insights
                if user_data.get("public_repos", 0) > 0:
                    text += f"💡 **Developer Insights**\n"

                    # Calculate engagement ratio
                    followers = user_data.get("followers", 0)
                    following = user_data.get("following", 0)
                    repos = user_data.get("public_repos", 0)

                    if followers > following * 3:
                        text += "• 🌟 High influence - More followers than following!\n"
                    elif followers > following:
                        text += "• ⭐ Popular developer - Good follower ratio!\n"

                    if repos > 50:
                        text += "• 💻 Very active coder with 50+ repositories!\n"
                    elif repos > 10:
                        text += "• ⚡ Active developer with multiple projects!\n"

                    if recent_commits:
                        text += f"• 🔥 Recently active - {len(recent_commits)} recent commits!\n"

                    # Repository per year ratio
                    if years_on_github > 0:
                        repos_per_year = repos / years_on_github
                        if repos_per_year > 10:
                            text += "• 🚀 Highly productive developer!\n"
                        elif repos_per_year > 5:
                            text += "• ⚡ Consistent contributor!\n"

                text += "\n💡 **Tip:** This shows your recent coding activity and GitHub presence!"

                keyboard = [
                    [
                        InlineKeyboardButton(
                            "🔄 Refresh Stats", callback_data=f"user_stats_{username}"
                        )
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
                    # Content will still be preserved from loading state

        except Exception as e:
            # Stop loading animation gracefully
            await self._stop_loading_safely(loading_task)

            # Log minimal error info
            logger.error(f"Stats error for {username}: {type(e).__name__}")
            await self._show_network_error(message, username)

    async def _stop_loading_safely(self, loading_task):
        """Safely stop loading animation"""
        if loading_task and not loading_task.done():
            loading_task.cancel()
            try:
                await asyncio.sleep(0.2)  # Give it time to cancel properly
                await loading_task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass  # Ignore other exceptions during cancellation

    async def _get_recent_commits(self, session, username):
        """Get recent commits with messages from push events"""
        try:
            from utils.git_api import _make_request_with_retry

            events = await _make_request_with_retry(
                session, f"/users/{username}/events/public",
                params={"per_page": 50}, timeout=10
            )

            commits = []
            for event in events or []:
                if event.get('type') == 'PushEvent':
                    payload = event.get('payload', {})
                    repo_name = event.get('repo', {}).get('name', 'Unknown')

                    # Get commits from this push event
                    for commit in payload.get('commits', []):
                        commit_message = commit.get('message', '').strip()

                        # Skip merge commits and empty messages
                        if (commit_message and
                            not commit_message.lower().startswith('merge') and
                            not commit_message.lower().startswith('update') and
                            len(commit_message) > 8):

                            commits.append({
                                'message': commit_message,
                                'repo': repo_name,
                                'date': event.get('created_at', '')
                            })

                            if len(commits) >= 6:  # Get enough commits
                                break

                    if len(commits) >= 6:
                        break

            return commits[:5]  # Return top 5 recent commits

        except Exception as e:
            logger.warning(f"Recent commits fetch error: {type(e).__name__}")
            return []

    async def _show_data_error(self, message, username, data_type):
        """Show data error inline with existing content"""
        # Get current text and modify it
        current_text = f"📊 **{username}'s GitHub Statistics**\n\n"
        current_text += f"❌ **Data Unavailable**\n\n"
        current_text += f"Could not load {data_type} for this user.\n\n"
        current_text += f"**Possible reasons:**\n"
        current_text += f"• User doesn't exist\n"
        current_text += f"• Profile is private\n"
        current_text += f"• GitHub API issues\n\n"
        current_text += f"💡 **Tip:** Check the username and try again!"

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 Retry Stats", callback_data=f"user_stats_{username}"
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
                current_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.warning(f"Error message update failed: {type(e).__name__}")

    async def _show_network_error(self, message, username):
        """Show network error inline"""
        error_text = f"📊 **{username}'s GitHub Statistics**\n\n"
        error_text += f"❌ **Connection Error**\n\n"
        error_text += f"Unable to connect to GitHub API.\n\n"
        error_text += f"**Try again in a moment!**\n\n"
        error_text += f"💡 **Tip:** The connection should work again soon!"

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 Retry Stats", callback_data=f"user_stats_{username}"
                ),
                InlineKeyboardButton(
                    "📂 View Repos", callback_data=f"user_repos_{username}"
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

        try:
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
        except Exception as e:
            # Log minimal error and return basic stats
            logger.warning(f"Stats processing error: {type(e).__name__}")

        return stats
