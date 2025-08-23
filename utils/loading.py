import asyncio
from telegram import InlineKeyboardMarkup
from telegram.error import BadRequest
import logging

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
#                    SIMPLE BALANCED LOADING ANIMATION
# ═══════════════════════════════════════════════════════════════════

DEFAULT_ANIMATION = "bounce"
ANIMATION_SPEED = 0.7

class LoadingAnimation:
    def __init__(self):
        # Simple icon transitions for smooth loading effect
        self.animations = {
            "dots": ["⏳", "⌛", "⏳", "⌛"],
            "spinner": ["🔄", "🔃", "🔄", "🔃"],
            "pulse": ["🔵", "🔷", "🔹", "🔷"],
            "wave": ["🌊", "〰️", "🌊", "〰️"],
            "stars": ["⭐", "🌟", "✨", "🌟"],
            "progress": ["▱", "▰", "▱", "▰"],
            "bounce": ["⚡", "💥", "⚡", "💥"],
            "fire": ["🔥", "🌋", "🔥", "🌋"],
            "rocket": ["🚀", "✨", "🚀", "✨"],
            "magic": ["🎭", "✨", "🎭", "✨"],
            "clock": ["🕐", "🕑", "🕒", "🕓"],
            "heart": ["💖", "💕", "💖", "💕"],
            "rainbow": ["🌈", "🌟", "🌈", "🌟"],
            "tech": ["⚙️", "🔧", "⚙️", "🔧"],
            "diamond": ["💎", "✨", "💎", "✨"],
        }

    def _find_tip_line(self, message_text):
        """Find the tip line and return its index and content"""
        lines = message_text.split('\n')

        for i, line in enumerate(lines):
            if "💡" in line and "tip" in line.lower():
                return i, line

        # If no tip line found, return last non-empty line
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip():
                return i, lines[i]

        return -1, ""

    def _create_balanced_loading_line(self, icon, action, page):
        """Create balanced loading line: 2 icons + text + 2 icons"""

        page_text = f" page {page}" if page else ""
        center_text = f"{action}{page_text}..."

        # Simple balanced format: icon icon text icon icon
        loading_line = f"{icon}{icon} {center_text} {icon}{icon}"

        return loading_line

    def _replace_tip_line(self, message_text, new_tip_line):
        """Replace tip line with new content"""
        lines = message_text.split('\n')
        tip_index, original_tip = self._find_tip_line(message_text)

        if tip_index >= 0:
            lines[tip_index] = new_tip_line
        else:
            lines.append(new_tip_line)

        return '\n'.join(lines)

    async def show_loading(
        self,
        message,
        title,
        action="Loading",
        page=None,
        animation_type=None,
        duration=None,
        preserve_content=True,
    ):
        """Show balanced loading animation with icon transitions"""

        final_animation = animation_type or DEFAULT_ANIMATION
        original_text = message.text if hasattr(message, "text") and message.text else f"{title}\n\n💡 **Tip:** Loading..."

        # Create animation task
        animation_task = asyncio.create_task(
            self._animate_balanced(
                message, original_text, action, page, final_animation, duration
            )
        )

        return animation_task

    async def _animate_balanced(self, message, original_text, action, page, animation_type, duration):
        """Animate with balanced layout and smooth icon transitions"""

        frames = self.animations.get(animation_type, self.animations[DEFAULT_ANIMATION])
        frame_index = 0
        start_time = asyncio.get_event_loop().time()

        try:
            while True:
                # Check duration
                if duration and (asyncio.get_event_loop().time() - start_time) > duration:
                    break

                # Get current icon for smooth transition
                current_icon = frames[frame_index % len(frames)]

                # Create balanced loading line
                loading_line = self._create_balanced_loading_line(
                    current_icon, action, page
                )

                # Replace tip line
                animated_text = self._replace_tip_line(original_text, loading_line)

                # Update message
                try:
                    await message.edit_text(
                        animated_text,
                        parse_mode="Markdown",
                        reply_markup=(
                            message.reply_markup
                            if hasattr(message, "reply_markup")
                            else None
                        ),
                        disable_web_page_preview=True,
                    )
                except BadRequest as e:
                    if "message is not modified" in str(e).lower():
                        pass
                    else:
                        logger.warning(f"Loading animation error: {e}")
                        break
                except Exception as e:
                    logger.error(f"Animation error: {e}")
                    break

                # Wait and advance to next frame for smooth transition
                await asyncio.sleep(ANIMATION_SPEED)
                frame_index += 1

        except asyncio.CancelledError:
            pass

    async def show_static_loading(
        self, message, title, action="Loading", page=None, preserve_content=True,
        animation_type=None
    ):
        """Show static balanced loading"""

        final_animation = animation_type or DEFAULT_ANIMATION
        original_text = message.text if hasattr(message, "text") and message.text else f"{title}\n\n💡 **Tip:** Loading..."

        # Get first icon
        static_icon = self.animations.get(final_animation, self.animations[DEFAULT_ANIMATION])[0]

        # Create balanced loading line
        loading_line = self._create_balanced_loading_line(
            static_icon, action, page
        )

        # Replace tip line
        loading_text = self._replace_tip_line(original_text, loading_line)

        # Update message
        try:
            await message.edit_text(
                loading_text,
                parse_mode="Markdown",
                reply_markup=(
                    message.reply_markup if hasattr(message, "reply_markup") else None
                ),
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.error(f"Static loading error: {e}")

    async def show_error(
        self,
        message,
        title,
        error_type="Network Error",
        details=None,
        preserve_content=False,
    ):
        """Show balanced error message"""

        original_text = message.text if hasattr(message, "text") and message.text else f"{title}\n\n💡 **Tip:** Something went wrong"

        # Create balanced error line
        error_line = f"❌❌ {error_type} - Try again ❌❌"

        # Replace tip line
        error_result = self._replace_tip_line(original_text, error_line)

        return error_result


# Create global instance
loading_animation = LoadingAnimation()

# Simple convenience functions
async def show_loading(
    message,
    title,
    action="Loading",
    page=None,
    animation_type=None,
    preserve_content=True,
):
    """Show balanced loading animation: icon icon text icon icon"""
    return await loading_animation.show_loading(
        message, title, action, page, animation_type, preserve_content
    )

async def show_static_loading(
    message, title, action="Loading", page=None, preserve_content=True,
    animation_type=None
):
    """Show static balanced loading"""
    await loading_animation.show_static_loading(
        message, title, action, page, preserve_content, animation_type
    )

async def show_error(
    message, title, error_type="Error", details=None, preserve_content=False
):
    """Show balanced error message"""
    return await loading_animation.show_error(
        message, title, error_type, details, preserve_content
    )
