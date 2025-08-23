from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import aiohttp
import logging
import asyncio

# Import the loading system
from utils.loading import show_loading, show_error, show_static_loading

logger = logging.getLogger(__name__)


class ProfileSocial:
    def __init__(self):
        self.FOLLOWERS_ANIMATION = "stars"
        self.FOLLOWING_ANIMATION = "pulse"

    async def show_followers(self, message, username, context, page=1):
        """Show user's followers with smooth loading animation"""
        per_page = 15

        # Show static loading first to preserve the window
        await show_static_loading(
            message,
            f"👥 **{username}'s Followers**",
            "Loading",
            page,
            preserve_content=True,
            animation_type=self.FOLLOWERS_ANIMATION,
        )

        # Start animated loading animation
        loading_task = await show_loading(
            message,
            f"👥 **{username}'s Followers**",
            "Loading",
            page,
            animation_type=self.FOLLOWERS_ANIMATION,
        )

        try:
            # Fetch data
            followers_data = await self._fetch_with_retry(
                username, "followers", page, per_page
            )

            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

            if followers_data is None:
                await self._show_network_error_inline(
                    message, username, "followers", page
                )
                return

            user_info, followers = followers_data
            total_followers = (
                user_info.get("followers", 0) if user_info else len(followers)
            )

            if not followers or len(followers) == 0:
                await self._show_empty_result(
                    message, username, "followers", page, total_followers
                )
                return

            # Calculate pagination info
            start_index = (page - 1) * per_page + 1
            end_index = min(start_index + len(followers) - 1, total_followers)
            total_pages = max(1, (total_followers + per_page - 1) // per_page)

            # Format followers
            text = f"👥 **{username}'s Followers**\n"
            if total_followers > 0:
                text += f"📊 Showing {start_index}-{end_index} of {total_followers:,} total\n"
            text += f"📄 Page {page} of {total_pages}\n\n"

            # Group followers in rows of 3
            for i, follower in enumerate(followers, 1):
                login = follower.get("login", "Unknown")
                follower_type = follower.get("type", "User")
                emoji = "🏢" if follower_type == "Organization" else "👤"
                text += f"{emoji} `{login}`"
                if i % 3 == 0:
                    text += "\n"
                else:
                    text += "  "

            text += f"\n\n💡 **Tip:** Copy any username to explore their profile!"

            # Create navigation buttons
            keyboard = self._create_pagination_keyboard(
                username, "followers", page, total_pages
            )

            # Update with final content while preserving the window
            try:
                await message.edit_text(
                    text,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    disable_web_page_preview=True,
                )
            except Exception as edit_error:
                logger.warning(f"Failed to edit message: {edit_error}")
                # Fallback: try to send the content anyway
                pass

        except Exception as e:
            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

            logger.error(
                f"Error in show_followers for {username} page {page}: {e}",
                exc_info=True,
            )
            await self._show_network_error_inline(message, username, "followers", page)

    async def show_following(self, message, username, context, page=1):
        """Show users that the user is following with smooth loading"""
        per_page = 15

        # Show static loading first to preserve the window
        await show_static_loading(
            message,
            f"👤 **Users {username} is Following**",
            "Loading",
            page,
            preserve_content=True,
            animation_type=self.FOLLOWING_ANIMATION,
        )

        # Start animated loading animation
        loading_task = await show_loading(
            message,
            f"👤 **Users {username} is Following**",
            "Loading",
            page,
            animation_type=self.FOLLOWING_ANIMATION,
        )

        try:
            # Fetch data
            following_data = await self._fetch_with_retry(
                username, "following", page, per_page
            )

            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

            if following_data is None:
                await self._show_network_error_inline(
                    message, username, "following", page
                )
                return

            user_info, following = following_data
            total_following = (
                user_info.get("following", 0) if user_info else len(following)
            )

            if not following or len(following) == 0:
                await self._show_empty_result(
                    message, username, "following", page, total_following
                )
                return

            # Calculate pagination info
            start_index = (page - 1) * per_page + 1
            end_index = min(start_index + len(following) - 1, total_following)
            total_pages = max(1, (total_following + per_page - 1) // per_page)

            # Format following
            text = f"👤 **Users {username} is Following**\n"
            if total_following > 0:
                text += f"📊 Showing {start_index}-{end_index} of {total_following:,} total\n"
            text += f"📄 Page {page} of {total_pages}\n\n"

            # Group following in rows of 3
            for i, user in enumerate(following, 1):
                login = user.get("login", "Unknown")
                user_type = user.get("type", "User")
                emoji = "🏢" if user_type == "Organization" else "👤"
                text += f"{emoji} `{login}`"
                if i % 3 == 0:
                    text += "\n"
                else:
                    text += "  "

            text += f"\n\n💡 **Tip:** Copy any username to explore their profile!"

            # Create navigation buttons
            keyboard = self._create_pagination_keyboard(
                username, "following", page, total_pages
            )

            # Update with final content while preserving the window
            try:
                await message.edit_text(
                    text,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    disable_web_page_preview=True,
                )
            except Exception as edit_error:
                logger.warning(f"Failed to edit message: {edit_error}")
                # Fallback: try to send the content anyway
                pass

        except Exception as e:
            # Stop loading animation gracefully
            if loading_task and not loading_task.done():
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass

            logger.error(
                f"Error in show_following for {username} page {page}: {e}",
                exc_info=True,
            )
            await self._show_network_error_inline(message, username, "following", page)

    async def _show_network_error_inline(self, message, username, endpoint, page):
        """Show network error with clean formatting"""
        title = (
            f"👥 **{username}'s Followers**"
            if endpoint == "followers"
            else f"👤 **Users {username} is Following**"
        )

        error_text = await show_error(
            message,
            title,
            "Network Error",
            "**Possible causes:**\n• Connection timeout\n• GitHub API issues\n• DNS problems\n\n💡 Try again in a moment!",
            preserve_content=False,
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    f"🔄 Try Page {page} Again",
                    callback_data=f"user_{endpoint}_{username}_page_{page}",
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
            )
        except Exception as e:
            logger.warning(f"Failed to show error message: {e}")

    # Keep all your existing helper methods (_fetch_with_retry, _create_pagination_keyboard, etc.)
    # ... rest of your existing methods remain the same

    async def _fetch_with_retry(
        self, username, endpoint, page, per_page, max_retries=3
    ):
        """Fetch data with multiple retry strategies"""
        from utils.git_api import _make_request_with_retry

        retry_timeouts = [8, 12, 20]  # Progressive timeout

        for attempt in range(max_retries):
            try:
                timeout = aiohttp.ClientTimeout(
                    total=retry_timeouts[attempt],
                    connect=5,
                    sock_read=retry_timeouts[attempt] - 2,
                )

                async with aiohttp.ClientSession(timeout=timeout) as session:
                    # Get user info and endpoint data
                    user_info_task = _make_request_with_retry(
                        session, f"/users/{username}", timeout=retry_timeouts[attempt]
                    )

                    endpoint_task = _make_request_with_retry(
                        session,
                        f"/users/{username}/{endpoint}",
                        params={"per_page": per_page, "page": page},
                        timeout=retry_timeouts[attempt],
                    )

                    # Wait for both requests with timeout
                    try:
                        user_info, endpoint_data = await asyncio.wait_for(
                            asyncio.gather(
                                user_info_task, endpoint_task, return_exceptions=True
                            ),
                            timeout=retry_timeouts[attempt],
                        )

                        # Check if either request failed
                        if isinstance(user_info, Exception):
                            user_info = None
                        if isinstance(endpoint_data, Exception):
                            endpoint_data = None

                        if endpoint_data is not None:
                            return user_info, endpoint_data

                    except asyncio.TimeoutError:
                        logger.warning(
                            f"Attempt {attempt + 1} timed out for {username} {endpoint}"
                        )

            except Exception as e:
                logger.warning(
                    f"Attempt {attempt + 1} failed for {username} {endpoint}: {e}"
                )

            # Wait before retry
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)  # Exponential backoff

        return None

    def _create_pagination_keyboard(self, username, endpoint, page, total_pages):
        """Create pagination keyboard"""
        keyboard = []

        # Navigation buttons
        nav_buttons = []
        if page > 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    "⬅️ Previous",
                    callback_data=f"user_{endpoint}_{username}_page_{page-1}",
                )
            )
        if page < total_pages:
            nav_buttons.append(
                InlineKeyboardButton(
                    "➡️ Next", callback_data=f"user_{endpoint}_{username}_page_{page+1}"
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
                        "⏮️ First", callback_data=f"user_{endpoint}_{username}_page_1"
                    )
                )
            if page < total_pages - 1:
                jump_buttons.append(
                    InlineKeyboardButton(
                        "⏭️ Last",
                        callback_data=f"user_{endpoint}_{username}_page_{total_pages}",
                    )
                )
            if jump_buttons:
                keyboard.append(jump_buttons)

        # Action buttons
        other_endpoint = "following" if endpoint == "followers" else "followers"
        keyboard.extend(
            [
                [
                    InlineKeyboardButton(
                        "🔄 Refresh", callback_data=f"user_{endpoint}_{username}"
                    ),
                    InlineKeyboardButton(
                        f"👥 {other_endpoint.title()}",
                        callback_data=f"user_{other_endpoint}_{username}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "⬅️ Back to Profile", callback_data="back_to_profile"
                    )
                ],
            ]
        )

        return keyboard

    async def _show_empty_result(self, message, username, endpoint, page, total_count):
        """Show empty result message"""
        if endpoint == "followers":
            if page == 1:
                text = f"👥 **{username}'s Followers**\n\n😔 @{username} has no followers yet.\n\n💡 Follow them to be the first!"
            else:
                text = f"👥 **{username}'s Followers**\n📄 Page {page}\n\n😔 No more followers to show.\n\nYou've reached the end!"
        else:  # following
            if page == 1:
                text = f"👤 **Users {username} is Following**\n\n😔 @{username} is not following anyone yet.\n\n💡 They might be new to GitHub!"
            else:
                text = f"👤 **Users {username} is Following**\n📄 Page {page}\n\n😔 No more users to show.\n\nYou've reached the end!"

        keyboard = [
            [InlineKeyboardButton("⬅️ Back to Profile", callback_data="back_to_profile")]
        ]

        if page > 1:
            other_endpoint = "following" if endpoint == "followers" else "followers"
            keyboard.insert(
                0,
                [
                    InlineKeyboardButton(
                        "⬅️ Previous Page",
                        callback_data=f"user_{endpoint}_{username}_page_{page-1}",
                    ),
                    InlineKeyboardButton(
                        f"👥 {other_endpoint.title()}",
                        callback_data=f"user_{other_endpoint}_{username}",
                    ),
                ],
            )

        try:
            await message.edit_text(
                text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.warning(f"Failed to show empty result: {e}")
