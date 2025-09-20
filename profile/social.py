# profile/social.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import aiohttp
import logging
import asyncio

# Import the loading system and formatting utilities
from utils.loading import with_loading
from utils.formatting import _escape_markdown_v2, add_admin_context

logger = logging.getLogger(__name__)


class ProfileSocial:
    def __init__(self):
        self.FOLLOWERS_ANIMATION = "stars"
        self.FOLLOWING_ANIMATION = "pulse"

    @with_loading("Loading followers", 1.4)
    async def show_followers(self, update_or_message, username, context, page=1, is_admin_profile=False):
        """Show user's followers with loading animation"""
        per_page = 15
        
        # Get the loading message from context (set by decorator)
        message = context.user_data.get('_loading_message')
        if not message:
            message = update_or_message

        try:
            # Fetch data
            followers_data = await self._fetch_with_retry(
                username, "followers", page, per_page
            )

            if followers_data is None:
                await self._show_network_error_inline(
                    message, username, "followers", page, is_admin_profile
                )
                return

            user_info, followers = followers_data
            total_followers = (
                user_info.get("followers", 0) if user_info else len(followers)
            )

            if not followers or len(followers) == 0:
                await self._show_empty_result(
                    message, username, "followers", page, total_followers, is_admin_profile
                )
                return

            # Calculate pagination info
            start_index = (page - 1) * per_page + 1
            end_index = min(start_index + len(followers) - 1, total_followers)
            total_pages = max(1, (total_followers + per_page - 1) // per_page)

            # Format followers
            base_text = f"👥 **{_escape_markdown_v2(username)}'s Followers**\n"
            if total_followers > 0:
                base_text += f"📊 Showing {start_index}-{end_index} of {total_followers:,} total\n"
            base_text += f"📄 Page {page} of {total_pages}\n\n"

            # Group followers in rows of 3
            for i, follower in enumerate(followers, 1):
                login = follower.get("login", "Unknown")
                follower_type = follower.get("type", "User")
                emoji = "🏢" if follower_type == "Organization" else "👤"
                base_text += f"{emoji} `{login}`"
                if i % 3 == 0:
                    base_text += "\n"
                else:
                    base_text += "  "

            base_text += f"\n\n💡 **Tip:** Copy any username to explore their profile!"

            # Add admin context if needed
            text = add_admin_context(base_text, username) if is_admin_profile else base_text

            # Create navigation buttons
            keyboard = self._create_pagination_keyboard(
                username, "followers", page, total_pages, is_admin_profile
            )

            # Update with final content
            try:
                await message.edit_text(
                    text,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    disable_web_page_preview=True,
                )
            except Exception as edit_error:
                logger.warning(f"Failed to edit message: {edit_error}")

        except Exception as e:
            logger.error(
                f"Error in show_followers for {username} page {page}: {e}",
                exc_info=True,
            )
            await self._show_network_error_inline(message, username, "followers", page, is_admin_profile)

    @with_loading("Loading following", 1.4)
    async def show_following(self, update_or_message, username, context, page=1, is_admin_profile=False):
        """Show users that the user is following with loading animation"""
        per_page = 15
        
        # Get the loading message from context (set by decorator)
        message = context.user_data.get('_loading_message')
        if not message:
            message = update_or_message

        try:
            # Fetch data
            following_data = await self._fetch_with_retry(
                username, "following", page, per_page
            )

            if following_data is None:
                await self._show_network_error_inline(
                    message, username, "following", page, is_admin_profile
                )
                return

            user_info, following = following_data
            total_following = (
                user_info.get("following", 0) if user_info else len(following)
            )

            if not following or len(following) == 0:
                await self._show_empty_result(
                    message, username, "following", page, total_following, is_admin_profile
                )
                return

            # Calculate pagination info
            start_index = (page - 1) * per_page + 1
            end_index = min(start_index + len(following) - 1, total_following)
            total_pages = max(1, (total_following + per_page - 1) // per_page)

            # Format following
            base_text = f"👤 **Users {_escape_markdown_v2(username)} is Following**\n"
            if total_following > 0:
                base_text += f"📊 Showing {start_index}-{end_index} of {total_following:,} total\n"
            base_text += f"📄 Page {page} of {total_pages}\n\n"

            # Group following in rows of 3
            for i, user in enumerate(following, 1):
                login = user.get("login", "Unknown")
                user_type = user.get("type", "User")
                emoji = "🏢" if user_type == "Organization" else "👤"
                base_text += f"{emoji} `{login}`"
                if i % 3 == 0:
                    base_text += "\n"
                else:
                    base_text += "  "

            base_text += f"\n\n💡 **Tip:** Copy any username to explore their profile!"

            # Add admin context if needed
            text = add_admin_context(base_text, username) if is_admin_profile else base_text

            # Create navigation buttons
            keyboard = self._create_pagination_keyboard(
                username, "following", page, total_pages, is_admin_profile
            )

            # Update with final content
            try:
                await message.edit_text(
                    text,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    disable_web_page_preview=True,
                )
            except Exception as edit_error:
                logger.warning(f"Failed to edit message: {edit_error}")

        except Exception as e:
            logger.error(
                f"Error in show_following for {username} page {page}: {e}",
                exc_info=True,
            )
            await self._show_network_error_inline(message, username, "following", page, is_admin_profile)

    # ==================== ERROR HANDLERS ====================

    async def _show_network_error_inline(self, message, username, endpoint, page, is_admin_profile=False):
        """Show network error with clean formatting"""
        title = (
            f"👥 **{_escape_markdown_v2(username)}'s Followers**"
            if endpoint == "followers"
            else f"👤 **Users {_escape_markdown_v2(username)} is Following**"
        )

        base_text = (
            f"{title}\n\n"
            f"❌ **Network Error**\n\n"
            f"Unable to load {endpoint} data.\n\n"
            f"**Possible causes:**\n"
            f"• Connection timeout\n"
            f"• GitHub API issues\n"
            f"• DNS problems\n\n"
            f"💡 **Tip:** Try again in a moment!"
        )

        error_text = add_admin_context(base_text, username) if is_admin_profile else base_text

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

        # Add admin buttons if needed
        if is_admin_profile:
            keyboard.insert(0, [
                InlineKeyboardButton(f"📊 {endpoint.title()} Analytics", callback_data=f"admin_{endpoint}_analytics_{username}"),
                InlineKeyboardButton(f"💾 Export {endpoint.title()}", callback_data=f"admin_export_{endpoint}_{username}")
            ])

        try:
            await message.edit_text(
                error_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.warning(f"Failed to show error message: {e}")

    async def _show_empty_result(self, message, username, endpoint, page, total_count, is_admin_profile=False):
        """Show empty result message"""
        if endpoint == "followers":
            if page == 1:
                base_text = f"👥 **{_escape_markdown_v2(username)}'s Followers**\n\n😔 @{username} has no followers yet.\n\n💡 **Tip:** Follow them to be the first!"
            else:
                base_text = f"👥 **{_escape_markdown_v2(username)}'s Followers**\n📄 Page {page}\n\n😔 No more followers to show.\n\n✅ You've reached the end!"
        else:  # following
            if page == 1:
                base_text = f"👤 **Users {_escape_markdown_v2(username)} is Following**\n\n😔 @{username} is not following anyone yet.\n\n💡 **Tip:** They might be new to GitHub!"
            else:
                base_text = f"👤 **Users {_escape_markdown_v2(username)} is Following**\n📄 Page {page}\n\n😔 No more users to show.\n\n✅ You've reached the end!"

        text = add_admin_context(base_text, username) if is_admin_profile else base_text

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

        # Add admin buttons if needed
        if is_admin_profile:
            keyboard.insert(-1, [
                InlineKeyboardButton(f"📊 {endpoint.title()} Stats", callback_data=f"admin_{endpoint}_stats_{username}"),
                InlineKeyboardButton(f"🔍 Deep Analysis", callback_data=f"admin_{endpoint}_analysis_{username}")
            ])

        try:
            await message.edit_text(
                text, 
                parse_mode="Markdown", 
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.warning(f"Failed to show empty result: {e}")

    # ==================== DATA FETCHING ====================

    async def _fetch_with_retry(self, username, endpoint, page, per_page, max_retries=3):
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

    # ==================== KEYBOARD GENERATION ====================

    def _create_pagination_keyboard(self, username, endpoint, page, total_pages, is_admin_profile=False):
        """Create pagination keyboard with admin support"""
        keyboard = []

        # Admin buttons first
        if is_admin_profile:
            keyboard.append([
                InlineKeyboardButton(f"📊 {endpoint.title()} Analytics", callback_data=f"admin_{endpoint}_analytics_{username}"),
                InlineKeyboardButton(f"💾 Export {endpoint.title()}", callback_data=f"admin_export_{endpoint}_{username}")
            ])

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

    # ==================== UTILITY METHODS ====================

    def format_social_stats(self, user_data):
        """Format social statistics for quick display"""
        if not user_data:
            return "No social data available"
        
        followers = user_data.get('followers', 0)
        following = user_data.get('following', 0)
        
        # Calculate follow ratio
        follow_ratio = followers / following if following > 0 else followers
        
        return f"👥 {followers:,} followers • 👤 {following:,} following • 📊 {follow_ratio:.1f} ratio"

    def get_social_influence_level(self, followers_count):
        """Determine social influence level based on followers"""
        if followers_count >= 10000:
            return "🌟 High Influence"
        elif followers_count >= 1000:
            return "⭐ Notable"
        elif followers_count >= 100:
            return "📈 Growing"
        elif followers_count >= 10:
            return "🌱 Emerging"
        else:
            return "🆕 New"

    async def get_social_summary(self, username):
        """Get a quick summary of user's social stats"""
        try:
            from utils.git_api import _make_request_with_retry
            import aiohttp
            
            timeout = aiohttp.ClientTimeout(total=8, connect=4)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                user_data = await _make_request_with_retry(
                    session, f"/users/{username}", timeout=6
                )
                
                if user_data:
                    followers = user_data.get('followers', 0)
                    following = user_data.get('following', 0)
                    
                    return {
                        "followers": followers,
                        "following": following,
                        "influence": self.get_social_influence_level(followers),
                        "stats": self.format_social_stats(user_data)
                    }
                
                return None
                
        except Exception as e:
            logger.debug(f"Social summary error for {username}: {type(e).__name__}")
            return None

    def format_user_list_compact(self, users, max_display=10):
        """Format user list in compact format"""
        if not users:
            return "No users found"
        
        display_users = users[:max_display]
        formatted = []
        
        for user in display_users:
            login = user.get('login', 'Unknown')
            user_type = user.get('type', 'User')
            emoji = "🏢" if user_type == "Organization" else "👤"
            formatted.append(f"{emoji} `{login}`")
        
        result = " • ".join(formatted)
        
        if len(users) > max_display:
            remaining = len(users) - max_display
            result += f" • ... and {remaining} more"
        
        return result

    def calculate_social_engagement(self, followers, following):
        """Calculate social engagement metrics"""
        if followers == 0 and following == 0:
            return {"level": "inactive", "ratio": 0, "description": "No social activity"}
        
        if following == 0:
            ratio = float('inf')
            level = "celebrity"
            description = "Only followed, never follows back"
        else:
            ratio = followers / following
        
        if ratio >= 10:
            level = "influencer"
            description = "High influence, selective following"
        elif ratio >= 2:
            level = "popular"
            description = "More followers than following"
        elif ratio >= 0.5:
            level = "balanced"
            description = "Balanced social engagement"
        else:
            level = "explorer"
            description = "Actively following others"
        
        return {
            "level": level,
            "ratio": ratio if ratio != float('inf') else followers,
            "description": description
        }

    async def analyze_social_network(self, username, sample_size=50):
        """Analyze user's social network patterns"""
        try:
            from utils.git_api import _make_request_with_retry
            import aiohttp
            
            timeout = aiohttp.ClientTimeout(total=15, connect=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Get a sample of followers and following
                followers_task = _make_request_with_retry(
                    session, f"/users/{username}/followers",
                    params={"per_page": min(sample_size, 100)}, timeout=10
                )
                following_task = _make_request_with_retry(
                    session, f"/users/{username}/following",
                    params={"per_page": min(sample_size, 100)}, timeout=10
                )
                
                followers, following = await asyncio.gather(
                    followers_task, following_task, return_exceptions=True
                )
                
                if isinstance(followers, Exception):
                    followers = []
                if isinstance(following, Exception):
                    following = []
                
                # Analyze patterns
                analysis = {
                    "followers_sample": len(followers) if followers else 0,
                    "following_sample": len(following) if following else 0,
                    "org_followers": sum(1 for u in (followers or []) if u.get('type') == 'Organization'),
                    "org_following": sum(1 for u in (following or []) if u.get('type') == 'Organization'),
                    "mutual_connections": 0,  # Would need more API calls to determine
                    "network_diversity": "mixed" if followers and following else "limited"
                }
                
                return analysis
                
        except Exception as e:
            logger.debug(f"Social network analysis error for {username}: {type(e).__name__}")
            return None


# Create instance
profile_social = ProfileSocial()