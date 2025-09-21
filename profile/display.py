# profile/display.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import logging
import asyncio
import aiohttp

# Import the loading system and formatting utilities
from utils.loading import with_loading
from utils.formatting import (
    _escape_markdown_v2, add_admin_context, format_admin_header, 
    format_admin_footer, format_loading_text, escape_markdown_v2_url
)

logger = logging.getLogger(__name__)


class ProfileDisplay:
    def __init__(self):
        self.PROFILE_ANIMATION = "magic"  # Magic animation for profile loading

    @with_loading("Loading profile", 1.5)
    async def show_user_profile(self, update_or_message, context, user_data=None, username=None, is_admin_profile: bool = False):
        """Display beautiful user profile with loading animation and error handling"""
        
        # Get the loading message from context (set by decorator)
        message = context.user_data.get('_loading_message')
        if not message:
            # Fallback to passed message
            message = update_or_message
        
        if not user_data:
            user_data = context.user_data.get("current_user")
        
        # Extract username for loading display
        display_username = username or user_data.get("login", "Unknown User") if user_data else "Unknown User"

        try:
            # Process the user data
            profile_content = await self._build_profile_content(user_data, context, is_admin_profile=is_admin_profile)

            if not profile_content:
                logger.error(f"_build_profile_content returned None for {display_username}")
                await self._show_profile_error(message, display_username, "Invalid Data", is_admin_profile)
                return

            profile_text, keyboard = profile_content

            # Update with final content
            try:
                await message.edit_text(
                    profile_text,
                    parse_mode="MarkdownV2",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    disable_web_page_preview=True,
                )
            except Exception as edit_error:
                logger.warning(f"Profile edit failed: {type(edit_error).__name__}")

        except Exception as e:
            logger.error(f"Profile display error for {display_username}: {type(e).__name__}", exc_info=True)
            await self._show_profile_error(message, display_username, "Display Error", is_admin_profile)

    @with_loading("Refreshing profile", 1.2)
    async def refresh_user_profile(self, update_or_message, username, context, is_admin_profile: bool = False):
        """Refresh user profile with loading animation"""
        
        # Get the loading message from context (set by decorator)
        message = context.user_data.get('_loading_message')
        if not message:
            # Fallback to passed message
            message = update_or_message

        try:
            # Fetch fresh user data
            from utils.git_api import _make_request_with_retry

            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                user_data = await _make_request_with_retry(
                    session, f"/users/{username}", timeout=8
                )

                if not user_data:
                    await self._show_profile_error(message, username, "Refresh Failed", is_admin_profile)
                    return

                # Update context with fresh data
                context.user_data["current_user"] = user_data
                context.user_data["is_admin_profile"] = is_admin_profile

                # Build and show the updated profile
                profile_content = await self._build_profile_content(user_data, context, is_admin_profile=is_admin_profile)
                
                if profile_content:
                    profile_text, keyboard = profile_content
                    await message.edit_text(
                        profile_text,
                        parse_mode="MarkdownV2",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        disable_web_page_preview=True,
                    )
                else:
                    await self._show_profile_error(message, username, "Refresh Error", is_admin_profile)

        except Exception as e:
            logger.error(f"Profile refresh error for {username}: {type(e).__name__}", exc_info=True)
            await self._show_profile_error(message, username, "Refresh Error", is_admin_profile)

    async def _build_profile_content(self, user_data, context, is_admin_profile: bool = False):
        """Build enhanced profile content from user data"""
        logger.debug(f"_build_profile_content: Received user_data type: {type(user_data)}")
        
        try:
            if not user_data or not isinstance(user_data, dict):
                logger.error(f"_build_profile_content: Invalid user_data received: {user_data}")
                return None

            # Get user info safely
            name = user_data.get("name") or user_data.get("login", "Unknown")
            username = user_data.get("login", "Unknown")
            avatar_url = user_data.get("avatar_url", "")
            bio = user_data.get("bio", "")
            company = user_data.get("company", "")
            location = user_data.get("location", "")
            blog = user_data.get("blog", "")
            twitter = user_data.get("twitter_username", "")

            public_repos = user_data.get("public_repos", 0)
            followers = user_data.get("followers", 0)
            following = user_data.get("following", 0)
            public_gists = user_data.get("public_gists", 0)
            
            logger.debug(f"_build_profile_content: Extracted name: {name}, username: {username}")

            # Clean location and company
            location = self._clean_text_field(location)
            company = self._clean_text_field(company)

            # Get additional info from README
            readme_info = await self._get_readme_info(username)

            # Format join date
            created_at = user_data.get("created_at", "")
            years_on_github = 0
            if created_at:
                try:
                    created_date = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                    joined = created_date.strftime("%B %d, %Y")
                    years_on_github = datetime.now().year - created_date.year
                except Exception as date_error:
                    logger.error(f"Date parsing error for '{created_at}': {date_error}")
                    joined = "Unknown"
                    years_on_github = 0
            else:
                joined = "Unknown"

            # Build beautiful profile
            profile_text = f"👤 **{_escape_markdown_v2(name)}**\n"
            profile_text += f"🏷️ **{_escape_markdown_v2(username)}**"

            # Add profile indicators
            indicators = []
            if company:
                indicators.append("🏢")
            if location:
                indicators.append("📍")
            if blog:
                indicators.append("🌐")
            if twitter:
                indicators.append("🐦")
            if readme_info.get('telegram'):
                indicators.append("✈️")
            if avatar_url:
                indicators.append("📸")
            
            if indicators:
                profile_text += " " + " ".join(indicators)

            profile_text += "\n\n"

            if bio:
                profile_text += f"📝 _{_escape_markdown_v2(bio[:150])}{'...' if len(bio) > 150 else ''}_\n\n"

            # Stats section
            profile_text += "📊 **GitHub Stats**\n"
            profile_text += f"┌─ 📂 **{public_repos:,}** public repositories\n"
            profile_text += f"├─ 👥 **{followers:,}** followers\n"
            profile_text += f"├─ 👤 **{following:,}** following\n"
            profile_text += f"└─ 📄 **{public_gists:,}** public gists\n\n"

            # Details section
            profile_text += "ℹ️ **Profile Details**\n"
            if company:
                profile_text += f"🏢 {_escape_markdown_v2(company)}\n"
            if location:
                profile_text += f"📍 {_escape_markdown_v2(location)}\n"
            if blog:
                if not blog.startswith(("http://", "https://")):
                    blog = f"https://{blog}"
                safe_url = escape_markdown_v2_url(blog)
                profile_text += f"🌐 [{_escape_markdown_v2(blog[:30])}{'...' if len(blog) > 30 else ''}]({safe_url})\n"
            if twitter:
                tw_url = escape_markdown_v2_url(f"https://twitter.com/{twitter}")
                profile_text += f"🐦 [@{_escape_markdown_v2(twitter)}]({tw_url})\n"

            # Add social links if found
            if readme_info.get('telegram'):
                tg_url = escape_markdown_v2_url(readme_info['telegram'])
                profile_text += f"✈️ [Telegram]({tg_url})\n"

            if readme_info.get('cv'):
                cv_url = escape_markdown_v2_url(readme_info['cv'])
                profile_text += f"📄 [CV/Resume]({cv_url})\n"

            profile_text += f"📅 Joined {_escape_markdown_v2(joined)}"
            if years_on_github > 0:
                profile_text += f" ({years_on_github} years ago)"
            profile_text += "\n"

            gh_url = escape_markdown_v2_url(f"https://github.com/{username}")
            profile_text += f"\n🔗 [View on GitHub]({gh_url})"
            profile_text += f"\n\n💡 **Tip:** Use the 📸 button to view the profile picture!"

            # Add admin context if needed (don't escape username for admin functions)
            if is_admin_profile:
                profile_text = add_admin_context(profile_text, username)
            
            # Create action buttons - DON'T ESCAPE USERNAME IN CALLBACK DATA
            keyboard = [
                [
                    InlineKeyboardButton(
                        "📸 View Avatar", callback_data=f"show_avatar_{username}"
                    ),
                    InlineKeyboardButton(
                        "📂 Repositories", callback_data=f"user_repos_{username}"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "⭐ Starred", callback_data=f"user_starred_{username}"
                    ),
                    InlineKeyboardButton(
                        f"👥 Followers ({followers:,})",
                        callback_data=f"user_followers_{username}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        f"👤 Following ({following:,})",
                        callback_data=f"user_following_{username}",
                    ),
                    InlineKeyboardButton(
                        "📊 Stats & Activity", callback_data=f"user_stats_{username}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔄 Refresh", callback_data=f"refresh_user_{username}"
                    ),
                    InlineKeyboardButton("⬅️ Back", callback_data="back_to_start"),
                ],
            ]

            return profile_text, keyboard

        except Exception as e:
            logger.warning(f"Profile content build error: {type(e).__name__} - {e}", exc_info=True)
            return None

    async def _get_readme_info(self, username):
        """Get additional info from user's README"""
        info = {'telegram': None, 'cv': None}

        try:
            from utils.git_api import _make_request_with_retry

            timeout = aiohttp.ClientTimeout(total=5, connect=3)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Try to get README from profile repo
                readme = await _make_request_with_retry(
                    session, f"/repos/{username}/{username}/readme", timeout=4
                )

                # If README exists and has content, extract info
                if readme and isinstance(readme, dict) and readme.get('content'):
                    import base64
                    try:
                        content = base64.b64decode(readme['content']).decode('utf-8', errors='ignore')
                        info = self._extract_social_links(content)
                    except Exception:
                        # Silently ignore README decode issues
                        pass
                else:
                    # Silently ignore when no README is found
                    pass

        except Exception:
            # Silently ignore README fetch errors
            pass

        return info

    def _extract_social_links(self, content):
        """Extract social links from README content using simple string operations"""
        info = {'telegram': None, 'cv': None}

        content_lower = content.lower()

        # Look for Telegram links (simple approach)
        if 't.me/' in content_lower:
            try:
                start_pos = content_lower.find('t.me/')
                # Find the end of the link
                end_pos = start_pos + 5  # Start after 't.me/'
                while end_pos < len(content) and content[end_pos] not in [' ', '\n', ')', ']', '>', '\t']:
                    end_pos += 1

                telegram_username = content[start_pos + 5:end_pos]
                if telegram_username and len(telegram_username) > 3:
                    info['telegram'] = f"https://t.me/{telegram_username}"
            except Exception:
                pass

        # Look for CV/Resume links
        cv_keywords = ['resume', 'cv', 'curriculum']
        for keyword in cv_keywords:
            if keyword in content_lower:
                lines = content.split('\n')
                for line in lines:
                    line_lower = line.lower()
                    if keyword in line_lower and 'http' in line_lower and '.pdf' in line_lower:
                        # Simple extraction - find first http link in this line
                        words = line.split()
                        for word in words:
                            if word.startswith('http') and '.pdf' in word:
                                # Clean up the URL
                                cv_url = word.rstrip('.,;:!)(]>')
                                if len(cv_url) > 10:
                                    info['cv'] = cv_url
                                    break
                        if info['cv']:
                            break
                if info['cv']:
                    break

        return info

    def _clean_text_field(self, value):
        """Clean text fields like location and company"""
        if not value:
            return ""

        # Remove common prefixes
        value = value.strip()
        prefixes = ['@', 'at ', 'in ', 'from ', 'based in ', 'working at ']

        for prefix in prefixes:
            if value.lower().startswith(prefix.lower()):
                value = value[len(prefix):].strip()
                break

        # Remove emojis and special characters from the beginning
        while value and ord(value[0]) > 127:
            value = value[1:].strip()

        # Clean up whitespace and limit length
        value = ' '.join(value.split())
        return value[:50] if value else ""

    async def _show_profile_error(self, message, username, error_type, is_admin_profile: bool = False):
        """Show profile error with structured message and action buttons"""
        base_error_text = (
            f"👤 **{_escape_markdown_v2(username)}'s Profile**\n\n"
            f"❌ **{error_type}**\n\n"
            f"Unable to display profile information.\n\n"
            f"**Possible causes:**\n"
            f"• Profile data incomplete\n"
            f"• Display formatting error\n"
            f"• Connection timeout\n\n"
            f"💡 **Tip:** Try refreshing the profile!"
        )

        # Admin context if needed
        error_text = add_admin_context(base_error_text, username) if is_admin_profile else base_error_text

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 Try Again", callback_data=f"refresh_user_{username}"
                ),
                InlineKeyboardButton(
                    "⬅️ Back to Start", callback_data="back_to_start"
                ),
            ]
        ]

        try:
            await message.edit_text(
                error_text,
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.warning(f"Error display failed: {type(e).__name__}")

    def get_profile_summary(self, user_data):
        """Get a quick profile summary for other components"""
        if not user_data:
            return "Unknown User"

        name = user_data.get("name") or user_data.get("login", "Unknown")
        username = user_data.get("login", "Unknown")
        repos = user_data.get("public_repos", 0)
        followers = user_data.get("followers", 0)

        return f"{name} (@{username}) • {repos} repos • {followers} followers"

    def format_user_stats_summary(self, user_data):
        """Format user stats for quick display"""
        if not user_data:
            return "No stats available"
        
        repos = user_data.get("public_repos", 0)
        followers = user_data.get("followers", 0) 
        following = user_data.get("following", 0)
        gists = user_data.get("public_gists", 0)
        
        return f"📂 {repos} repos • 👥 {followers} followers • 👤 {following} following • 📄 {gists} gists"


# Create instance
profile_display = ProfileDisplay()