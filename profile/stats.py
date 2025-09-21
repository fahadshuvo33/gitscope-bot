# profile/stats.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import aiohttp
import logging
import asyncio
from datetime import datetime, timedelta

# Import the loading system and formatting utilities
from utils.loading import with_loading
from utils.formatting import _escape_markdown_v2, add_admin_context

logger = logging.getLogger(__name__)


class ProfileStats:
    def __init__(self):
        self.STATS_ANIMATION = "tech"  # Technical animation for stats

    @with_loading("Loading statistics", 2.0)
    async def show_contribution_stats(self, update_or_message, username, context, is_admin_profile=False):
        """Show user contribution statistics and activity with loading animation"""
        
        # Get the loading message from context (set by decorator)
        message = context.user_data.get('_loading_message')
        if not message:
            message = update_or_message

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
                    await self._show_data_error(message, username, "user data", is_admin_profile)
                    return

                # Get recent events/activity
                events = await _make_request_with_retry(
                    session, f"/users/{username}/events/public",
                    params={"per_page": 30}, timeout=10
                )
                if not isinstance(events, list):
                    events = []
                else:
                    events = [e for e in events if isinstance(e, dict)]

                # Get additional repository stats
                repos = await _make_request_with_retry(
                    session, f"/users/{username}/repos",
                    params={"per_page": 100, "sort": "updated"}, timeout=12
                )
                if not isinstance(repos, list):
                    repos = []
                else:
                    repos = [r for r in repos if isinstance(r, dict)]

                # Process statistics
                stats = await self._process_user_stats(user_data, events, repos)
                language_stats = self._analyze_languages(repos) if repos else {}

                # Format stats display (no decorative line under the title)
                base_text = f"📊 **{_escape_markdown_v2(username)}'s GitHub Statistics**\n\n"

                # Add achievement badges
                achievements = self._generate_achievements(user_data, stats, language_stats)
                if achievements:
                    base_text += "🏆 **Achievements**\n"
                    for achievement in achievements:
                        base_text += f"• {achievement}\n"
                    base_text += "\n"

                # (Developer Score removed as requested)

                # Basic stats with enhanced formatting
                # Safely coerce numeric fields
                public_repos = int((user_data.get('public_repos', 0) or 0))
                public_gists = int((user_data.get('public_gists', 0) or 0))
                followers = int((user_data.get('followers', 0) or 0))
                following = int((user_data.get('following', 0) or 0))

                base_text += f"📈 **Profile Overview**\n"
                base_text += f"┌─ 📂 **{public_repos:,}** public repositories\n"
                base_text += f"├─ 📄 **{public_gists:,}** public gists\n"
                base_text += f"├─ 👥 **{followers:,}** followers\n"
                base_text += f"├─ 👤 **{following:,}** following\n"
                
                # Add engagement ratio
                if following > 0:
                    ratio = followers / following
                    base_text += f"└─ 📊 **{ratio:.1f}** engagement ratio\n\n"
                else:
                    base_text += f"└─ 📊 **∞** engagement ratio (celebrity mode!)\n\n"

                # Language statistics
                if language_stats:
                    base_text += "💻 **Programming Languages**\n"
                    for i, (lang, percentage) in enumerate(language_stats['top_languages'][:4], 1):
                        bar_length = int(percentage / 5)  # Scale to 20 chars max
                        bar = '█' * bar_length + '░' * (20 - bar_length)
                        base_text += f"{i}. **{_escape_markdown_v2(lang)}** {percentage:.1f}%\n"
                        base_text += f"   {bar}\n"
                    base_text += f"**Diversity:** {language_stats['diversity_score']}/10 languages used\n\n"

                # Repository insights
                if repos:
                    repo_insights = self._analyze_repositories(repos)
                    base_text += "📊 **Repository Insights**\n"
                    base_text += f"┌─ ⭐ **{repo_insights['total_stars']:,}** total stars earned\n"
                    base_text += f"├─ 🍴 **{repo_insights['total_forks']:,}** total forks received\n"
                    base_text += f"├─ 👁️ **{repo_insights['total_watchers']:,}** total watchers\n"
                    base_text += f"├─ 📊 **{repo_insights['avg_stars']:.1f}** average stars per repo\n"
                    base_text += f"└─ 🔥 **{repo_insights['active_repos']}** recently active repos\n\n"

                    # Most popular repository
                    if repo_insights['most_starred']:
                        most_starred = repo_insights['most_starred']
                        base_text += f"🌟 **Most Popular:** {_escape_markdown_v2(most_starred['name'])}\n"
                        base_text += f"   ⭐ {most_starred['stars']:,} stars • 🍴 {most_starred['forks']:,} forks\n\n"

                # Recent commits with actual work
                recent_commits = await self._get_recent_commits(session, username)
                if recent_commits:
                    base_text += "🔥 **Recent Work**\n"
                    for i, commit in enumerate(recent_commits[:4], 1):
                        repo_name = commit['repo'].split('/')[-1] if '/' in commit['repo'] else commit['repo']
                        commit_msg = _escape_markdown_v2(commit['message'])
                        # Clean up commit message
                        if len(commit_msg) > 45:
                            commit_msg = commit_msg[:45] + "..."
                        base_text += f"├─ **{_escape_markdown_v2(repo_name)}**: {commit_msg}\n"
                    base_text += "\n"

                # Activity stats
                if events:
                    base_text += "🎯 **Recent Activity** (Last 30 events)\n"
                    base_text += f"┌─ 📝 **{stats['commits']}** commits pushed\n"
                    base_text += f"├─ 🔀 **{stats['pull_requests']}** pull requests\n"
                    base_text += f"├─ 🐛 **{stats['issues']}** issues created\n"
                    base_text += f"├─ ⭐ **{stats['stars']}** repositories starred\n"
                    base_text += f"├─ 🍴 **{stats['forks']}** repositories forked\n"
                    base_text += f"├─ 🎉 **{stats['releases']}** releases published\n"
                    base_text += f"└─ 💬 **{stats['comments']}** comments made\n\n"

                    # Most active repositories
                    if stats["top_repos"]:
                        base_text += "🔥 **Most Active Repositories**\n"
                        for i, (repo, count) in enumerate(stats["top_repos"][:3], 1):
                            repo_display = repo.split('/')[-1] if '/' in repo else repo
                            base_text += f"{i}. **{_escape_markdown_v2(repo_display)}** ({count} events)\n"
                        base_text += "\n"
                else:
                    base_text += "🎯 **Recent Activity**\n"
                    base_text += "No recent public activity found.\n\n"

                # Time-based analysis
                time_analysis = self._analyze_activity_patterns(events) if events else {}
                if time_analysis:
                    base_text += "⏰ **Activity Patterns**\n"
                    base_text += f"├─ 🌅 **Most Active:** {time_analysis['most_active_period']}\n"
                    base_text += f"├─ 📅 **Recent Days:** {time_analysis['active_days']}/7 days active\n"
                    base_text += f"└─ 🔄 **Consistency:** {time_analysis['consistency_score']}/10\n\n"

                # Account age and info
                created_at = user_data.get("created_at", "")
                years_on_github = 0
                if created_at:
                    try:
                        created_date = datetime.strptime(
                            created_at, "%Y-%m-%dT%H:%M:%SZ"
                        )
                        years_on_github = (datetime.now() - created_date).days // 365
                        months_on_github = ((datetime.now() - created_date).days % 365) // 30
                        
                        base_text += f"📅 **Account Information**\n"
                        base_text += f"├─ 🎂 **Age:** {years_on_github} years, {months_on_github} months\n"
                        base_text += f"├─ 📅 **Joined:** {created_date.strftime('%B %d, %Y')}\n"
                        
                        # Productivity metrics
                        if years_on_github > 0:
                            repos_per_year = user_data.get('public_repos', 0) / years_on_github
                            base_text += f"└─ 📊 **Productivity:** {repos_per_year:.1f} repos/year\n\n"
                        else:
                            base_text += f"└─ 🌱 **Status:** New to GitHub!\n\n"
                    except Exception:
                        base_text += f"📅 **Account:** Long-time GitHub user\n\n"

                # Developer insights with personality analysis
                insights = self._generate_developer_insights(user_data, stats, repos, years_on_github)
                if insights:
                    base_text += f"🧠 **Developer Insights**\n"
                    for insight in insights:
                        base_text += f"• {insight}\n"
                    base_text += "\n"

                # Contribution calendar simulation
                if events:
                    contribution_level = self._calculate_contribution_level(stats)
                    base_text += f"📈 **Contribution Level: {contribution_level}**\n"
                    base_text += self._generate_contribution_visual(stats) + "\n\n"

                base_text += "💡 **Tip:** This analysis is based on your public GitHub activity!"

                # Add admin context if needed
                text = add_admin_context(base_text, username) if is_admin_profile else base_text

                # Ensure we don't exceed Telegram's ~4096 character limit
                text = self._truncate_markdown(text, 3900)

                keyboard = self._create_stats_keyboard(username, is_admin_profile)

                # Update with final content
                try:
                    await message.edit_text(
                        text,
                        parse_mode="MarkdownV2",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        disable_web_page_preview=True,
                    )
                except Exception as edit_error:
                    logger.warning(f"Message edit failed: {type(edit_error).__name__}")
                    # Fallback: try to send as a new message
                    try:
                        await message.reply_text(
                            text,
                            parse_mode="MarkdownV2",
                            reply_markup=InlineKeyboardMarkup(keyboard),
                            disable_web_page_preview=True,
                        )
                        return
                    except Exception as send_error:
                        logger.warning(f"Stats send fallback failed: {type(send_error).__name__}")

        except Exception as e:
            logger.error(f"Stats error for {username}: {type(e).__name__} - {e}", exc_info=True)
            await self._show_network_error(message, username, is_admin_profile)

    # ==================== ANALYSIS METHODS ====================

    def _generate_achievements(self, user_data, stats, language_stats):
        """Generate achievement badges based on user activity"""
        achievements = []
        
        repos = user_data.get('public_repos', 0)
        followers = user_data.get('followers', 0)
        commits = stats.get('commits', 0)
        
        # Repository achievements
        if repos >= 100:
            achievements.append("🏆 Repository Master (100+ repos)")
        elif repos >= 50:
            achievements.append("🥉 Repository Expert (50+ repos)")
        elif repos >= 20:
            achievements.append("🥈 Active Developer (20+ repos)")
        elif repos >= 10:
            achievements.append("🥇 Getting Started (10+ repos)")
        
        # Social achievements
        if followers >= 1000:
            achievements.append("⭐ Influencer (1K+ followers)")
        elif followers >= 500:
            achievements.append("🌟 Popular Developer (500+ followers)")
        elif followers >= 100:
            achievements.append("👥 Community Member (100+ followers)")
        
        # Activity achievements
        if commits >= 50:
            achievements.append("💻 Code Warrior (50+ recent commits)")
        elif commits >= 20:
            achievements.append("⚡ Active Coder (20+ recent commits)")
        
        # Language diversity
        if language_stats and language_stats.get('diversity_score', 0) >= 7:
            achievements.append("🌈 Polyglot (7+ languages)")
        elif language_stats and language_stats.get('diversity_score', 0) >= 5:
            achievements.append("🔧 Multi-lingual (5+ languages)")
        
        # Special combinations
        if repos >= 20 and followers >= 100 and commits >= 30:
            achievements.append("🚀 GitHub All-Star")
        
        return achievements[:5]  # Limit to top 5 achievements

    def _calculate_profile_score(self, user_data, stats):
        """Calculate a comprehensive profile score out of 100"""
        def safe_float(val):
            try:
                return float(val)
            except (TypeError, ValueError):
                return 0.0

        def safe_int(val):
            try:
                return int(val)
            except (TypeError, ValueError):
                return 0

        score = 0.0
        
        # Repository contribution (30 points max)
        repos = safe_float(user_data.get('public_repos', 0))
        score += min(30.0, repos * 0.5)
        
        # Social influence (25 points max)
        followers = safe_float(user_data.get('followers', 0))
        score += min(25.0, followers * 0.05)
        
        # Recent activity (20 points max)
        commits = safe_float(stats.get('commits', 0))
        score += min(20.0, commits * 2.0)
        
        # Engagement (15 points max)
        prs = safe_float(stats.get('pull_requests', 0))
        issues = safe_float(stats.get('issues', 0))
        score += min(15.0, (prs + issues) * 1.5)
        
        # Consistency bonus (10 points max)
        top_repos = stats.get('top_repos') or []
        score += min(10.0, float(len(top_repos)) * 2.0)
        
        return min(100, int(score))

    def _analyze_languages(self, repos):
        """Analyze programming languages used"""
        if not repos:
            return {}
        
        language_count = {}
        total_repos = 0
        
        for repo in repos:
            lang = repo.get('language')
            if lang and lang != 'Unknown':
                language_count[lang] = language_count.get(lang, 0) + 1
                total_repos += 1
        
        if not language_count:
            return {}
        
        # Calculate percentages
        language_percentages = []
        for lang, count in language_count.items():
            percentage = (count / total_repos) * 100
            language_percentages.append((lang, percentage))
        
        # Sort by usage
        language_percentages.sort(key=lambda x: x[1], reverse=True)
        
        return {
            'top_languages': language_percentages,
            'diversity_score': len(language_count),
            'most_used': language_percentages[0][0] if language_percentages else 'Unknown'
        }

    def _analyze_repositories(self, repos):
        """Analyze repository statistics"""
        if not repos:
            return {}
        
        def safe_int(val):
            try:
                return int(val)
            except (TypeError, ValueError):
                return 0

        total_stars = sum(safe_int(repo.get('stargazers_count')) for repo in repos)
        total_forks = sum(safe_int(repo.get('forks_count')) for repo in repos)
        total_watchers = sum(safe_int(repo.get('watchers_count')) for repo in repos)
        
        # Find most starred repository (guard empty)
        most_starred = None
        if repos:
            try:
                most_starred = max(repos, key=lambda x: safe_int(x.get('stargazers_count')))
            except Exception:
                most_starred = None
        
        # Count recently active repos (updated in last 6 months)
        six_months_ago = datetime.now() - timedelta(days=180)
        active_repos = 0
        
        for repo in repos:
            updated_at = repo.get('updated_at')
            if updated_at:
                try:
                    updated_date = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ")
                    if updated_date > six_months_ago:
                        active_repos += 1
                except:
                    continue
        
        return {
            'total_stars': total_stars,
            'total_forks': total_forks,
            'total_watchers': total_watchers,
            'avg_stars': total_stars / len(repos) if repos else 0,
            'most_starred': ({
                'name': most_starred.get('name', 'Unknown'),
                'stars': safe_int(most_starred.get('stargazers_count')),
                'forks': safe_int(most_starred.get('forks_count'))
            } if most_starred else None),
            'active_repos': active_repos
        }

    def _analyze_activity_patterns(self, events):
        """Analyze user activity patterns"""
        if not events:
            return {}
        
        # Analyze time patterns
        hour_activity = {}
        day_activity = {}
        recent_days = set()
        
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        
        for event in events:
            created_at = event.get('created_at')
            if created_at:
                try:
                    event_date = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                    hour = event_date.hour
                    day_name = event_date.strftime('%A')
                    
                    hour_activity[hour] = hour_activity.get(hour, 0) + 1
                    day_activity[day_name] = day_activity.get(day_name, 0) + 1
                    
                    # Check if event is within last week
                    if event_date > week_ago:
                        recent_days.add(event_date.date())
                        
                except:
                    continue
        
        # Determine most active period
        if hour_activity:
            most_active_hour = max(hour_activity.items(), key=lambda x: x[1])[0]
            if 6 <= most_active_hour <= 12:
                most_active_period = "Morning (6-12)"
            elif 12 <= most_active_hour <= 18:
                most_active_period = "Afternoon (12-18)"
            elif 18 <= most_active_hour <= 24:
                most_active_period = "Evening (18-24)"
            else:
                most_active_period = "Night (0-6)"
        else:
            most_active_period = "Unknown"
        
        # Calculate consistency score
        consistency_score = min(10, len(day_activity) * 2)  # Max 10 if active all days
        
        return {
            'most_active_period': most_active_period,
            'active_days': len(recent_days),
            'consistency_score': consistency_score,
            'hour_distribution': hour_activity,
            'day_distribution': day_activity
        }

    def _generate_developer_insights(self, user_data, stats, repos, years_on_github):
        """Generate personality insights about the developer"""
        insights = []
        
        followers = user_data.get('followers', 0)
        following = user_data.get('following', 0)
        public_repos = user_data.get('public_repos', 0)
        commits = stats.get('commits', 0)
        
        # Social behavior analysis
        if following > followers * 2:
            insights.append("🤝 Social networker - Actively follows other developers!")
        elif followers > following * 3:
            insights.append("🌟 Influencer - More people follow you than you follow!")
        elif abs(followers - following) < followers * 0.3:
            insights.append("⚖️ Balanced networker - Maintains healthy follow ratio!")
        
        # Productivity insights
        if years_on_github > 0:
            repos_per_year = public_repos / years_on_github
            if repos_per_year > 15:
                insights.append("🚀 Highly productive - Creates lots of projects!")
            elif repos_per_year > 8:
                insights.append("⚡ Consistent creator - Steady project development!")
            elif repos_per_year > 3:
                insights.append("🎯 Focused developer - Quality over quantity approach!")
        
        # Activity insights
        if commits > 40:
            insights.append("💻 Very active coder - Lots of recent commits!")
        elif commits > 20:
            insights.append("⚡ Regular contributor - Consistent coding activity!")
        
        # Repository insights
        if repos and public_repos > 0:
            avg_stars = sum(repo.get('stargazers_count', 0) for repo in repos) / len(repos)
            if avg_stars > 10:
                insights.append("🌟 Creates popular projects - High average stars!")
            elif avg_stars > 5:
                insights.append("👍 Well-received code - Good community response!")
        
        # Pull request behavior
        if stats.get('pull_requests', 0) > 10:
            insights.append("🤝 Collaborative developer - Active in open source!")
        
        # Issue reporting
        if stats.get('issues', 0) > 5:
            insights.append("🐛 Quality focused - Actively reports issues!")
        
        return insights[:4]  # Limit to top 4 insights

    def _calculate_contribution_level(self, stats):
        """Calculate contribution level"""
        total_activity = (
            stats.get('commits', 0) * 2 +
            stats.get('pull_requests', 0) * 3 +
            stats.get('issues', 0) * 1 +
            stats.get('releases', 0) * 4
        )
        
        if total_activity >= 100:
            return "🔥 Extremely Active"
        elif total_activity >= 50:
            return "⚡ Very Active"
        elif total_activity >= 20:
            return "📈 Active"
        elif total_activity >= 10:
            return "🌱 Getting Started"
        else:
            return "😴 Quiet"

    def _generate_contribution_visual(self, stats):
        """Generate a simple visual representation of contributions"""
        commits = stats.get('commits', 0)
        prs = stats.get('pull_requests', 0)
        issues = stats.get('issues', 0)
        
        # Simple bar representation
        max_val = max(commits, prs, issues, 1)
        
        commit_bar = '█' * min(10, int(commits / max_val * 10))
        pr_bar = '█' * min(10, int(prs / max_val * 10))
        issue_bar = '█' * min(10, int(issues / max_val * 10))
        
        visual = f"📝 Commits: {commit_bar} ({commits})\n"
        visual += f"🔀 PRs: {pr_bar} ({prs})\n"
        visual += f"🐛 Issues: {issue_bar} ({issues})"
        
        return visual

    # ==================== DATA FETCHING ====================

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

    async def _process_user_stats(self, user_data, events, repos):
        """Process user events to generate comprehensive statistics"""
        stats = {
            "commits": 0,
            "pull_requests": 0,
            "issues": 0,
            "stars": 0,
            "forks": 0,
            "releases": 0,
            "comments": 0,
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
                elif event_type in ["IssueCommentEvent", "PullRequestReviewCommentEvent", "CommitCommentEvent"]:
                    stats["comments"] += 1

            # Get top repositories by activity
            stats["top_repos"] = sorted(
                repo_activity.items(), key=lambda x: x[1], reverse=True
            )
        except Exception as e:
            logger.warning(f"Stats processing error: {type(e).__name__}")

        return stats

    # ==================== KEYBOARD AND ERROR HANDLING ====================

    def _create_stats_keyboard(self, username, is_admin_profile=False):
        """Create keyboard for stats display"""
        keyboard = []
        
        # Admin buttons first
        if is_admin_profile:
            keyboard.append([
                InlineKeyboardButton("📊 Deep Analytics", callback_data=f"admin_deep_analytics_{username}"),
                InlineKeyboardButton("💾 Export Stats", callback_data=f"admin_export_stats_{username}")
            ])
        
        keyboard.extend([
            [
                InlineKeyboardButton(
                    "🔄 Refresh Stats", callback_data=f"user_stats_{username}"
                ),
                InlineKeyboardButton(
                    "📂 View Repos", callback_data=f"user_repos_{username}"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back to Profile", callback_data="back_to_profile"
                )
            ],
        ])
        
        return keyboard

    async def _show_data_error(self, message, username, data_type, is_admin_profile=False):
        """Show data error inline with existing content"""
        base_text = f"📊 **{_escape_markdown_v2(username)}'s GitHub Statistics**\n\n"
        base_text += f"❌ **Data Unavailable**\n\n"
        base_text += f"Could not load {data_type} for this user.\n\n"
        base_text += f"**Possible reasons:**\n"
        base_text += f"• User doesn't exist\n"
        base_text += f"• Profile is private\n"
        base_text += f"• GitHub API issues\n\n"
        base_text += f"💡 **Tip:** Check the username and try again!"

        error_text = add_admin_context(base_text, username) if is_admin_profile else base_text

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
                error_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.warning(f"Error message update failed: {type(e).__name__}")

    async def _show_network_error(self, message, username, is_admin_profile=False):
        """Show network error inline"""
        base_text = f"📊 **{_escape_markdown_v2(username)}'s GitHub Statistics**\n\n"
        base_text += f"❌ **Connection Error**\n\n"
        base_text += f"Unable to connect to GitHub API.\n\n"
        base_text += f"**Try again in a moment!**\n\n"
        base_text += f"💡 **Tip:** The connection should work again soon!"

        error_text = add_admin_context(base_text, username) if is_admin_profile else base_text

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

        if is_admin_profile:
            keyboard.insert(0, [
                InlineKeyboardButton("📊 Admin Override", callback_data=f"admin_stats_override_{username}"),
                InlineKeyboardButton("🔍 Debug Stats", callback_data=f"admin_debug_stats_{username}")
            ])

        try:
            await message.edit_text(
                error_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.warning(f"Error display failed: {type(e).__name__}")

    # ==================== UTILITY METHODS ====================

    def get_stats_summary(self, user_data):
        """Get a quick stats summary for other components"""
        if not user_data:
            return "No statistics available"
        
        repos = user_data.get('public_repos', 0)
        followers = user_data.get('followers', 0)
        gists = user_data.get('public_gists', 0)
        
        return f"📊 {repos} repos • 👥 {followers} followers • 📄 {gists} gists"

    def _truncate_markdown(self, text: str, limit: int = 3900) -> str:
        """Truncate long markdown text at a newline boundary and append ellipsis."""
        try:
            if len(text) <= limit:
                return text
            cutoff = text.rfind('\n', 0, limit)
            if cutoff == -1:
                cutoff = limit
            return text[:cutoff] + "\n\n…"
        except Exception:
            return text[:limit]

    async def get_developer_rank(self, user_data, stats):
        """Calculate developer rank based on various metrics"""
        try:
            score = self._calculate_profile_score(user_data, stats)
            
            if score >= 90:
                return {"rank": "Elite Developer", "percentile": 95, "badge": "🏆"}
            elif score >= 75:
                return {"rank": "Senior Developer", "percentile": 85, "badge": "🥇"}
            elif score >= 60:
                return {"rank": "Experienced Developer", "percentile": 70, "badge": "🥈"}
            elif score >= 40:
                return {"rank": "Intermediate Developer", "percentile": 50, "badge": "🥉"}
            elif score >= 25:
                return {"rank": "Junior Developer", "percentile": 30, "badge": "📈"}
            else:
                return {"rank": "Beginner Developer", "percentile": 10, "badge": "🌱"}
        except Exception as e:
            logger.debug(f"Developer rank calculation error: {type(e).__name__}")
            return {"rank": "Developer", "percentile": 50, "badge": "👨‍💻"}

    def format_activity_summary(self, stats):
        """Format activity summary for quick display"""
        if not stats:
            return "No recent activity"
        
        commits = stats.get('commits', 0)
        prs = stats.get('pull_requests', 0)
        issues = stats.get('issues', 0)
        
        summary_parts = []
        if commits > 0:
            summary_parts.append(f"📝 {commits} commits")
        if prs > 0:
            summary_parts.append(f"🔀 {prs} PRs")
        if issues > 0:
            summary_parts.append(f"🐛 {issues} issues")
        
        return " • ".join(summary_parts) if summary_parts else "No recent activity"

    def calculate_productivity_metrics(self, user_data, repos):
        """Calculate productivity metrics"""
        try:
            if not repos or not user_data:
                return {}
            
            created_at = user_data.get('created_at')
            if not created_at:
                return {}
            
            # Calculate account age
            created_date = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
            account_age_days = (datetime.now() - created_date).days
            account_age_years = account_age_days / 365.25
            
            # Calculate metrics
            total_repos = len(repos)
            total_stars = sum(repo.get('stargazers_count', 0) for repo in repos)
            total_forks = sum(repo.get('forks_count', 0) for repo in repos)
            
            # Productivity ratios
            repos_per_year = total_repos / account_age_years if account_age_years > 0 else 0
            stars_per_repo = total_stars / total_repos if total_repos > 0 else 0
            
            # Activity metrics
            recent_repos = sum(1 for repo in repos 
                             if self._is_recently_updated(repo.get('updated_at'), days=180))
            
            return {
                'account_age_years': account_age_years,
                'repos_per_year': repos_per_year,
                'stars_per_repo': stars_per_repo,
                'total_impact': total_stars + total_forks,
                'recent_activity_ratio': recent_repos / total_repos if total_repos > 0 else 0,
                'productivity_score': self._calculate_productivity_score(
                    repos_per_year, stars_per_repo, recent_repos / total_repos if total_repos > 0 else 0
                )
            }
            
        except Exception as e:
            logger.debug(f"Productivity metrics calculation error: {type(e).__name__}")
            return {}

    def _is_recently_updated(self, updated_at_str, days=180):
        """Check if repository was updated recently"""
        if not updated_at_str:
            return False
        
        try:
            updated_date = datetime.strptime(updated_at_str, "%Y-%m-%dT%H:%M:%SZ")
            threshold_date = datetime.now() - timedelta(days=days)
            return updated_date > threshold_date
        except:
            return False

    def _calculate_productivity_score(self, repos_per_year, stars_per_repo, activity_ratio):
        """Calculate overall productivity score"""
        try:
            # Normalize metrics (0-10 scale each)
            repo_score = min(10, repos_per_year * 2)  # 5+ repos/year = max score
            quality_score = min(10, stars_per_repo)   # 10+ stars/repo = max score
            activity_score = activity_ratio * 10      # 100% active = max score
            
            # Weighted average
            total_score = (repo_score * 0.4 + quality_score * 0.4 + activity_score * 0.2)
            return round(total_score, 1)
        except:
            return 0.0

    async def generate_stats_report(self, username):
        """Generate a comprehensive stats report"""
        try:
            from utils.git_api import _make_request_with_retry
            import aiohttp
            
            timeout = aiohttp.ClientTimeout(total=20, connect=8)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Fetch all necessary data
                user_data = await _make_request_with_retry(
                    session, f"/users/{username}", timeout=10
                )
                events = await _make_request_with_retry(
                    session, f"/users/{username}/events/public",
                    params={"per_page": 100}, timeout=12
                )
                repos = await _make_request_with_retry(
                    session, f"/users/{username}/repos",
                    params={"per_page": 100}, timeout=12
                )
                
                if not user_data:
                    return None
                
                # Process all statistics
                stats = await self._process_user_stats(user_data, events, repos)
                language_stats = await self._analyze_languages(repos) if repos else {}
                productivity = self.calculate_productivity_metrics(user_data, repos)
                developer_rank = await self.get_developer_rank(user_data, stats)
                
                return {
                    'user_data': user_data,
                    'activity_stats': stats,
                    'language_stats': language_stats,
                    'productivity_metrics': productivity,
                    'developer_rank': developer_rank,
                    'profile_score': self._calculate_profile_score(user_data, stats),
                    'achievements': self._generate_achievements(user_data, stats, language_stats),
                    'insights': self._generate_developer_insights(user_data, stats, repos, 
                                                               productivity.get('account_age_years', 0))
                }
                
        except Exception as e:
            logger.error(f"Stats report generation error for {username}: {type(e).__name__}")
            return None

    def format_stats_for_export(self, stats_report):
        """Format stats report for export/sharing"""
        if not stats_report:
            return "No statistics available for export"
        
        user_data = stats_report['user_data']
        username = user_data.get('login', 'Unknown')
        
        export_text = f"📊 GitHub Statistics Report for @{username}\n"
        export_text += f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        export_text += "=" * 50 + "\n\n"
        
        # Basic info
        export_text += "PROFILE OVERVIEW:\n"
        export_text += f"• Repositories: {user_data.get('public_repos', 0):,}\n"
        export_text += f"• Followers: {user_data.get('followers', 0):,}\n"
        export_text += f"• Following: {user_data.get('following', 0):,}\n"
        export_text += f"• Public Gists: {user_data.get('public_gists', 0):,}\n"
        export_text += f"• Profile Score: {stats_report['profile_score']}/100\n\n"
        
        # Developer rank
        rank_info = stats_report.get('developer_rank', {})
        if rank_info:
            export_text += "DEVELOPER RANKING:\n"
            export_text += f"• Rank: {rank_info['rank']}\n"
            export_text += f"• Percentile: {rank_info['percentile']}%\n\n"
        
        # Activity stats
        activity = stats_report['activity_stats']
        if activity:
            export_text += "RECENT ACTIVITY:\n"
            export_text += f"• Commits: {activity.get('commits', 0)}\n"
            export_text += f"• Pull Requests: {activity.get('pull_requests', 0)}\n"
            export_text += f"• Issues: {activity.get('issues', 0)}\n"
            export_text += f"• Stars Given: {activity.get('stars', 0)}\n\n"
        
        # Top languages
        lang_stats = stats_report.get('language_stats', {})
        if lang_stats and lang_stats.get('top_languages'):
            export_text += "PROGRAMMING LANGUAGES:\n"
            for lang, percentage in lang_stats['top_languages'][:5]:
                export_text += f"• {lang}: {percentage:.1f}%\n"
            export_text += "\n"
        
        # Achievements
        achievements = stats_report.get('achievements', [])
        if achievements:
            export_text += "ACHIEVEMENTS:\n"
            for achievement in achievements:
                # Remove emojis for plain text export
                clean_achievement = ''.join(char for char in achievement if ord(char) < 128)
                export_text += f"• {clean_achievement.strip()}\n"
            export_text += "\n"
        
        export_text += "Report generated by GitHub Statistics Bot\n"
        
        return export_text


# Create instance
profile_stats = ProfileStats()