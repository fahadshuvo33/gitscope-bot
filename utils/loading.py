# loading.py
import asyncio
import random
from typing import Optional
from telegram import Message, Update, InlineKeyboardMarkup
from telegram.error import TelegramError
from telegram.ext import ContextTypes
import functools

class LoadingAnimator:
    """Advanced loading animator with colorful styles"""
    
    ANIMATIONS = {
        # Colorful emoji animations
        'rainbow': ["🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "🟤", "⚫", "⚪"],
        'hearts': ["❤️", "🧡", "💛", "💚", "💙", "💜", "🤎", "🖤", "🤍", "💗", "💖", "💕"],
        'stars': ["⭐", "🌟", "✨", "💫", "🌠", "🌌", "🌃", "🌆", "🌇"],
        'gems': ["💎", "💠", "🔷", "🔹", "🔸", "🔶", "♦️", "🔻", "🔺"],
        'flowers': ["🌸", "🌺", "🌻", "🌼", "🌷", "🌹", "🌵", "🌴", "🌿"],
        'fruits': ["🍎", "🍊", "🍋", "🍌", "🍉", "🍇", "🍓", "🫐", "🍒", "🍑"],
        'planets': ["🌍", "🌎", "🌏", "🌐", "🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"],
        'weather': ["☀️", "🌤️", "⛅", "🌥️", "☁️", "🌦️", "🌧️", "⛈️", "🌩️", "🌨️", "❄️", "🌈"],
        'fire': ["🔥", "🎆", "🎇", "✨", "🎉", "🎊", "🪩", "💥", "⚡"],
        'water': ["💧", "💦", "🌊", "🏄", "🏊", "🚣", "⛵", "🚤", "🛟"],
        'nature': ["🌱", "🌿", "🍀", "🌾", "🌳", "🌲", "🌴", "🍂", "🍁", "🍃"],
        'animals': ["🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐨", "🐯"],
        'butterflies': ["🦋", "🐛", "🪲", "🐞", "🪳", "🪰", "🪱", "🦟", "🦗"],
        'ocean': ["🐠", "🐟", "🐡", "🦈", "🐳", "🐋", "🐬", "🦭", "🐙", "🦑"],
        'birds': ["🦅", "🦆", "🦉", "🦇", "🦚", "🦜", "🦢", "🦩", "🕊️", "🐦"],
        
        # Colorful geometric animations
        'circles': ["🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "⚫", "⚪", "🟤"],
        'squares': ["🟥", "🟧", "🟨", "🟩", "🟦", "🟪", "⬛", "⬜", "🟫"],
        'diamonds': ["💠", "🔷", "🔹", "🔸", "🔶", "♦️", "💎", "🔻", "🔺"],
        
        # Animated sequences
        'rocket': ["🚀", "✨", "💫", "🌟", "⭐", "🌠", "🌌", "🪐", "🌍"],
        'magic': ["🎩", "🪄", "✨", "🎆", "🎇", "🎉", "🎊", "🎭", "🎪"],
        'music': ["🎵", "🎶", "🎼", "🎹", "🎸", "🎺", "🎷", "🥁", "🎻"],
        'sports': ["⚽", "🏀", "🏈", "⚾", "🎾", "🏐", "🏉", "🎱", "🏓"],
        'food': ["🍕", "🍔", "🍟", "🌭", "🍿", "🧂", "🥓", "🥚", "🧈"],
        'drinks': ["☕", "🍵", "🧃", "🥤", "🧋", "🍺", "🍻", "🥂", "🍷"],
        'celebration': ["🎈", "🎆", "🎇", "✨", "🎉", "🎊", "🎁", "🎀", "🪅"],
        
        # Moving patterns
        'wave_color': ["🟦", "🟦🟦", "🟦🟦🟦", "🟦🟦", "🟦"],
        'pulse': ["•", "◉", "◎", "◉", "•"],
        'loading_dots': ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
        'bounce_color': ["🔵", "🔵⚪", "🔵⚪⚪", "⚪🔵⚪", "⚪⚪🔵"],
        
        # Tech themed
        'tech': ["💻", "🖥️", "📱", "⌨️", "🖱️", "💾", "💿", "📀", "🔌"],
        'gaming': ["🎮", "🕹️", "👾", "🎯", "🎲", "🃏", "🀄", "🎴", "🎰"],
        
        # Seasonal
        'winter': ["❄️", "☃️", "⛄", "🎿", "🏂", "⛷️", "🏔️", "🎅", "🤶"],
        'spring': ["🌸", "🌼", "🌻", "🌺", "🌷", "🌹", "🌵", "🌾", "🌿"],
        'summer': ["☀️", "🌞", "🏖️", "🏝️", "⛱️", "🏄", "🏊", "🤿", "🌊"],
        'autumn': ["🍂", "🍁", "🍃", "🌾", "🌰", "🍄", "🎃", "🌽", "🍊"],
        
        # Special effects
        'sparkle': ["✨", "💫", "⭐", "🌟", "💥", "⚡", "🌠", "🎆", "🎇"],
        'neon': ["🟣", "🔵", "🟢", "🟡", "🟠", "🔴", "🟣", "🔵", "🟢"],
        'gradient': ["⬜", "🟦", "🟪", "🟣", "🔵", "🟢", "🟡", "🟠", "🔴"],
    }
    
    # Define which animations look best together
    COLORFUL_COMBINATIONS = [
        ['rainbow', 'stars', 'sparkle'],
        ['hearts', 'flowers', 'butterflies'],
        ['planets', 'rocket', 'stars'],
        ['ocean', 'water', 'weather'],
        ['fire', 'magic', 'celebration'],
        ['gems', 'diamonds', 'sparkle'],
        ['neon', 'gradient', 'circles'],
        ['fruits', 'flowers', 'nature'],
        ['music', 'celebration', 'magic'],
        ['gaming', 'tech', 'neon'],
    ]
    
    def __init__(self):
        self.active_animations = {}
        self.should_stop = {}
    
    def get_random_colorful_styles(self, count: int = 3) -> list:
        """Get random colorful animation styles that work well together"""
        # Pick a random combination
        combination = random.choice(self.COLORFUL_COMBINATIONS)
        # Return the requested number of styles from this combination
        return combination[:count]
    
    def get_random_styles(self, count: int = 3) -> list:
        """Get random animation styles with preference for colorful ones"""
        # 70% chance to get a pre-defined colorful combination
        if random.random() < 0.7:
            return self.get_random_colorful_styles(count)
        else:
            # Otherwise pick randomly from all animations
            all_styles = list(self.ANIMATIONS.keys())
            count = min(count, len(all_styles))
            return random.sample(all_styles, count)
    
    async def animate_multiple(
        self, 
        message: Message, 
        text: str = "Loading",
        styles: Optional[list] = None,
        append_to_text: bool = True,
        preserve_keyboard: bool = True,
        speed: float = 0.3
    ) -> None:
        """Animate loading with multiple colorful styles"""
        message_id = message.message_id
        self.active_animations[message_id] = True
        self.should_stop[message_id] = False
        
        # Get original content
        original_text = message.text or message.caption or ""
        original_keyboard = message.reply_markup if preserve_keyboard else None
        
        # Select animation styles
        if styles is None:
            styles = self.get_random_styles(3)
        
        frame_index = 0
        
        try:
            while self.active_animations.get(message_id, False) and not self.should_stop.get(message_id, False):
                # Build animated text with multiple animations
                animation_parts = []
                for i, style in enumerate(styles):
                    frames = self.ANIMATIONS.get(style, self.ANIMATIONS['rainbow'])
                    # Offset each animation slightly for more dynamic effect
                    offset_index = (frame_index + i * 2) % len(frames)
                    frame = frames[offset_index]
                    animation_parts.append(frame)
                
                # Join animations with some spacing
                all_animations = " ".join(animation_parts)
                
                # Build final text
                if append_to_text and original_text.strip() and original_text != ".":
                    animated_text = f"{original_text}\n\n🎨 {text} {all_animations}"
                else:
                    animated_text = f"🎨 {text} {all_animations}"
                
                # Check if we should stop before editing
                if self.should_stop.get(message_id, False):
                    break
                
                try:
                    await message.edit_text(
                        animated_text,
                        parse_mode="Markdown",
                        reply_markup=original_keyboard,
                        disable_web_page_preview=True
                    )
                except TelegramError as e:
                    if "message is not modified" not in str(e).lower():
                        print(f"Animation error: {e}")
                
                frame_index += 1
                await asyncio.sleep(speed)
                
        finally:
            self.active_animations[message_id] = False
            if message_id in self.should_stop:
                del self.should_stop[message_id]
    
    def stop(self, message_id: int):
        """Stop animation for a specific message"""
        self.should_stop[message_id] = True
        self.active_animations[message_id] = False

# Global animator instance
animator = LoadingAnimator()

# Simple wrapper for updating message after animation
async def update_with_animation(
    message: Message,
    final_text: str,
    loading_text: str = "Loading",
    keyboard: Optional[InlineKeyboardMarkup] = None,
    parse_mode: str = "MarkdownV2",
    animation_duration: float = 1.5,
    styles: Optional[list] = None
):
    """Show colorful animation then update with final content"""
    # Start animation
    animation_task = asyncio.create_task(
        animator.animate_multiple(
            message=message,
            text=loading_text,
            styles=styles,
                        speed=0.25
        )
    )
    
    # Wait for specified duration
    await asyncio.sleep(animation_duration)
    
    # Stop animation
    animator.stop(message.message_id)
    
    # Wait a bit for animation to stop
    await asyncio.sleep(0.2)
    
    # Cancel the animation task
    animation_task.cancel()
    try:
        await animation_task
    except asyncio.CancelledError:
        pass
    
    # Now update with final content
    await message.edit_text(
        final_text,
        parse_mode=parse_mode,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

# Simplified decorator
def with_loading(
    text: str = "𝕃𝕠𝕒𝕕𝕚𝕟𝕘",
    duration: float = 1.0,
    styles: Optional[list] = None  # None means random colorful combination
):
    """Simplified loading decorator with colorful animations"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            message = None
            
            try:
                # Get or create message
                if update.callback_query:
                    await update.callback_query.answer()
                    message = update.callback_query.message
                elif update.message:
                    message = await update.message.reply_text(".")
                
                if not message:
                    return await func(update, context, *args, **kwargs)
                
                # Store in context
                context.user_data['_loading_message'] = message
                context.user_data['_animation_done'] = False
                
                # Start animation in background
                async def run_animation():
                    await animator.animate_multiple(
                        message=message,
                        text=text,
                        styles=styles,
                        speed=0.25
                    )
                    context.user_data['_animation_done'] = True
                
                animation_task = asyncio.create_task(run_animation())
                
                # Wait for the specified duration
                await asyncio.sleep(duration)
                
                # Stop animation
                animator.stop(message.message_id)
                
                # Wait for animation to actually stop
                await asyncio.sleep(0.3)
                
                # Cancel task if still running
                if not animation_task.done():
                    animation_task.cancel()
                    try:
                        await animation_task
                    except asyncio.CancelledError:
                        pass
                
                # Now run the actual function
                result = await func(update, context, *args, **kwargs)
                
                return result
                
            finally:
                # Cleanup
                if '_loading_message' in context.user_data:
                    del context.user_data['_loading_message']
                if '_animation_done' in context.user_data:
                    del context.user_data['_animation_done']
        
        return wrapper
    
    # Allow using decorator without parentheses
    if callable(text):
        func = text
        text = "𝕃𝕠𝕒𝕕𝕚𝕟𝕘"
        duration = 1.0
        return decorator(func)
    
    return decorator

# Pre-defined colorful loading styles for easy use
class LoadingStyles:
    """Pre-defined colorful loading style combinations"""
    
    RAINBOW = ['rainbow', 'stars', 'sparkle']
    LOVE = ['hearts', 'flowers', 'butterflies']
    SPACE = ['planets', 'rocket', 'stars']
    OCEAN = ['ocean', 'water', 'weather']
    FIRE = ['fire', 'magic', 'celebration']
    GEMS = ['gems', 'diamonds', 'sparkle']
    NEON = ['neon', 'gradient', 'circles']
    NATURE = ['fruits', 'flowers', 'nature']
    PARTY = ['music', 'celebration', 'magic']
    TECH = ['gaming', 'tech', 'neon']
    
    @classmethod
    def get_random(cls):
        """Get a random pre-defined style"""
        all_styles = [
            cls.RAINBOW, cls.LOVE, cls.SPACE, cls.OCEAN, 
            cls.FIRE, cls.GEMS, cls.NEON, cls.NATURE, 
            cls.PARTY, cls.TECH
        ]
        return random.choice(all_styles)