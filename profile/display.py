from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import logging
import asyncio
import aiohttp

# Import the loading system
from utils.loading import show_loading, show_error, show_static_loading

logger = logging.getLogger(__name__)


class ProfileDisplay:
    def __init__(self):
        self.PROFILE_ANIMATION = "magic"  # Magic animation for profile loading

    async def show_user_profile(self, message, user_data, context, username=None):
        """Display beautiful user profile with loading animation and error handling"""

        # Extract username for loading display
        display_username = username or user_data.get("login", "Unknown User")

        # Show static loading first to preserve the window
        await show_static_loading(
            message,
            f"👤 **{display_username}'s Profile**",
            "Loading profile",
            preserve_content=True,
            animation_type=self.PROFILE_ANIMATION,
        )

        # Start animated loading
        loading_task = await show_loading(
            message,
            f"👤 **{display_username}'s Profile**",
            "Loading profile",
            animation_type=self.PROFILE_ANIMATION,
        )

        try:
            # Process the user data (no separate image)
            profile_content = await self._build_profile_content(user_data, context)

            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

            if not profile_content:
                await self._show_profile_error(message, display_username, "Invalid Data")
                return

            profile_text, keyboard = profile_content

            # Update with final content
            try:
                await message.edit_text(
                    profile_text,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    disable_web_page_preview=True,
                )
            except Exception as edit_error:
                logger.warning(f"Profile edit failed: {type(edit_error).__name__}")

        except Exception as e:
            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

            logger.error(f"Profile display error for {display_username}: {type(e).__name__}")
            await self._show_profile_error(message, display_username, "Display Error")

    async def refresh_user_profile(self, message, username, context):
        """Refresh user profile with loading animation"""

        # Show static loading first to preserve the window
        await show_static_loading(
            message,
            f"👤 **{username}'s Profile**",
            "Refreshing profile",
            preserve_content=True,
            animation_type=self.PROFILE_ANIMATION,
        )

        # Start animated loading
        loading_task = await show_loading(
            message,
            f"👤 **{username}'s Profile**",
            "Refreshing profile",
            animation_type=self.PROFILE_ANIMATION,
        )

        try:
            # Fetch fresh user data
            from utils.git_api import _make_request_with_retry

            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                user_data = await _make_request_with_retry(
                    session, f"/users/{username}", timeout=8
                )

                # Stop loading animation gracefully
                if loading_task and not loading_task.done():
                    loading_task.cancel()
                    try:
                        await loading_task
                    except asyncio.CancelledError:
                        pass

                if not user_data:
                    await self._show_profile_error(message, username, "Refresh Failed")
                    return

                # Update context with fresh data
                context.user_data["current_user"] = user_data

                # Show the updated profile
                await self.show_user_profile(message, user_data, context, username)

        except Exception as e:
            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

            # Log minimal error info
            logger.error(f"Profile refresh error for {username}: {type(e).__name__}")
            await self._show_profile_error(message, username, "Refresh Error")

    async def _build_profile_content(self, user_data, context):
        """Build enhanced profile content from user data"""
        try:
            if not user_data or not isinstance(user_data, dict):
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
                except Exception:
                    joined = "Unknown"
                    years_on_github = 0
            else:
                joined = "Unknown"

            # Build beautiful profile - REMOVED CLICKABLE USERNAME
            profile_text = f"👤 **{name}**\n"
            profile_text += f"🏷️ **{username}**"

            # Add profile indicators
            if company:
                profile_text += " 🏢"
            if location:
                profile_text += " 📍"
            if blog:
                profile_text += " 🌐"
            if twitter:
                profile_text += " 🐦"
            if readme_info.get('telegram'):
                profile_text += " ✈️"
            if avatar_url:  # Show photo indicator if avatar exists
                profile_text += " 📸"

            profile_text += "\n\n"  # FIXED: This was inside the if statement

            if bio:
                profile_text += f"📝 _{bio[:150]}{'...' if len(bio) > 150 else ''}_\n\n"

            # Stats section
            profile_text += "📊 **GitHub Stats**\n"
            profile_text += f"┌─ 📂 **{public_repos:,}** public repositories\n"
            profile_text += f"├─ 👥 **{followers:,}** followers\n"
            profile_text += f"├─ 👤 **{following:,}** following\n"
            profile_text += f"└─ 📄 **{public_gists:,}** public gists\n\n"

            # Details section
            profile_text += "ℹ️ **Profile Details**\n"
            if company:
                profile_text += f"🏢 {company}\n"
            if location:
                profile_text += f"📍 {location}\n"
            if blog:
                if not blog.startswith(("http://", "https://")):
                    blog = f"https://{blog}"
                profile_text += f"🌐 [Website]({blog})\n"
            if twitter:
                profile_text += f"🐦 [@{twitter}](https://twitter.com/{twitter})\n"

            # Add social links if found
            if readme_info.get('telegram'):
                profile_text += f"✈️ [Telegram]({readme_info['telegram']})\n"

            if readme_info.get('cv'):
                profile_text += f"📄 [CV/Resume]({readme_info['cv']})\n"

            profile_text += f"📅 Joined {joined}"
            if years_on_github > 0:
                profile_text += f" ({years_on_github} years ago)"
            profile_text += "\n"

            profile_text += f"\n🔗 [View on GitHub](https://github.com/{username})"
            profile_text += f"\n\n💡 **Tip:** Use the 📸 button to view the profile picture!"

            # Create action buttons with avatar button
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
            logger.warning(f"Profile content build error: {type(e).__name__}")
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
                    except Exception as decode_error:
                        # Log but don't raise - just return empty info
                        logger.debug(f"README decode error for {username}: {type(decode_error).__name__}")
                else:
                    # No README found or invalid response - this is normal, not an error
                    logger.debug(f"No README found for {username}")

        except Exception as e:
            # Any error in fetching README should not break profile display
            logger.debug(f"README fetch error for {username}: {type(e).__name__}")
            # Return default empty info - don't raise

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

    async def _show_profile_error(self, message, username, error_type):
        """Show profile error with structured message and action buttons"""
        error_text = f"👤 **{username}'s Profile**\n\n"
        error_text += f"❌ **{error_type}**\n\n"
        error_text += f"Unable to display profile information.\n\n"
        error_text += f"**Possible causes:**\n"
        error_text += f"• Profile data incomplete\n"
        error_text += f"• Display formatting error\n"
        error_text += f"• Connection timeout\n\n"
        error_text += f"💡 **Tip:** Try refreshing the profile!"

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
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.warning(f"Error display failed: {type(e).__name__}")

    async def show_loading_profile(self, message, username):
        """Show loading state for profile - useful for external calls"""
        await show_static_loading(
            message,
            f"👤 **{username}'s Profile**",
            "Loading profile",
            preserve_content=True,
            animation_type=self.PROFILE_ANIMATION,
        )

    def get_profile_summary(self, user_data):
        """Get a quick profile summary for other components"""
        if not user_data:
            return "Unknown User"

        name = user_data.get("name") or user_data.get("login", "Unknown")
        username = user_data.get("login", "Unknown")
        repos = user_data.get("public_repos", 0)
        followers = user_data.get("followers", 0)

        return f"{name} (@{username}) • {repos} repos • {followers} followers"
