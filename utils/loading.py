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
        # Keep all your existing animations...
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
        'circles': ["🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "⚫", "⚪", "🟤"],
        'squares': ["🟥", "🟧", "🟨", "🟩", "🟦", "🟪", "⬛", "⬜", "🟫"],
        'diamonds': ["💠", "🔷", "🔹", "🔸", "🔶", "♦️", "💎", "🔻", "🔺"],
        'rocket': ["🚀", "✨", "💫", "🌟", "⭐", "🌠", "🌌", "🪐", "🌍"],
        'magic': ["🎩", "🪄", "✨", "🎆", "🎇", "🎉", "🎊", "🎭", "🎪"],
        'music': ["🎵", "🎶", "🎼", "🎹", "🎸", "🎺", "🎷", "🥁", "🎻"],
        'sports': ["⚽", "🏀", "🏈", "⚾", "🎾", "🏐", "🏉", "🎱", "🏓"],
        'food': ["🍕", "🍔", "🍟", "🌭", "🍿", "🧂", "🥓", "🥚", "🧈"],
        'drinks': ["☕", "🍵", "🧃", "🥤", "🧋", "🍺", "🍻", "🥂", "🍷"],
        'celebration': ["🎈", "🎆", "🎇", "✨", "🎉", "🎊", "🎁", "🎀", "🪅"],
        'tech': ["💻", "🖥️", "📱", "⌨️", "🖱️", "💾", "💿", "📀", "🔌"],
        'gaming': ["🎮", "🕹️", "👾", "🎯", "🎲", "🃏", "🀄", "🎴", "🎰"],
        'sparkle': ["✨", "💫", "⭐", "🌟", "💥", "⚡", "🌠", "🎆", "🎇"],
        'neon': ["🟣", "🔵", "🟢", "🟡", "🟠", "🔴", "🟣", "🔵", "🟢"],
    }
    
    COLORFUL_COMBINATIONS = [
        ['rainbow', 'stars'],
        ['hearts', 'flowers'],
        ['planets', 'rocket'],
        ['ocean', 'water'],
        ['fire', 'magic'],
        ['gems', 'diamonds'],
        ['neon', 'gradient'],
        ['fruits', 'flowers'],
        ['music', 'celebration'],
        ['gaming', 'tech'],
    ]
    
    def __init__(self):
        self.active_animations = {}
        self.should_stop = {}
        self.original_content = {}
    
    def get_random_styles(self) -> list:
        """Get exactly 2 random animation styles"""
        if random.random() < 0.7:
            combination = random.choice(self.COLORFUL_COMBINATIONS)
            return combination[:2]
        else:
            all_styles = list(self.ANIMATIONS.keys())
            return random.sample(all_styles, 2)
    
    def stop_all_animations_for_message(self, message_id: int):
        """Stop all animations for a specific message"""
        self.should_stop[message_id] = True
        self.active_animations[message_id] = False
    
    async def animate_multiple(
        self, 
        message: Message, 
        text: str = "𝕃𝕠𝕒𝕕𝕚𝕟𝕘",
        speed: float = 0.25,
        append_to_text: bool = True
    ) -> None:
        """Animate loading with exactly 2 icons before and after text"""
        message_id = message.message_id
        
        # Store original content
        if message_id not in self.original_content:
            self.original_content[message_id] = {
                'text': message.text or "",
                'keyboard': message.reply_markup
            }
        
        original_text = self.original_content[message_id]['text']
        original_keyboard = self.original_content[message_id]['keyboard']
        
        # Stop any existing animation
        self.stop_all_animations_for_message(message_id)
        self.active_animations[message_id] = True
        self.should_stop[message_id] = False
        
        # Get exactly 2 animation styles
        styles = self.get_random_styles()
        frame_index = 0
        
        try:
            while self.active_animations.get(message_id, False) and not self.should_stop.get(message_id, False):
                # Get frames for both styles
                icons = []
                for i, style in enumerate(styles):
                    frames = self.ANIMATIONS.get(style, self.ANIMATIONS['rainbow'])
                    offset_index = (frame_index + i * 3) % len(frames)
                    icons.append(frames[offset_index])
                
                # Format: icon1 icon2 text icon2 icon1
                loading_line = f"{icons[0]} {icons[1]} {text} {icons[1]} {icons[0]}"
                
                # Append to original text or show alone
                if append_to_text and original_text and "𝕃𝕠𝕒𝕕𝕚𝕟𝕘" not in original_text:
                    full_text = f"{original_text}\n\n{loading_line}"
                else:
                    full_text = loading_line
                
                if self.should_stop.get(message_id, False):
                    break
                
                try:
                    await message.edit_text(
                        full_text,
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
            if message_id in self.original_content:
                del self.original_content[message_id]
    
    def stop(self, message_id: int):
        """Stop animation for a specific message"""
        self.should_stop[message_id] = True
        self.active_animations[message_id] = False

# Global animator instance
animator = LoadingAnimator()
active_loadings = {}
loading_in_progress = set()  # Track which messages have loading in progress

def with_loading(text: str = "𝕃𝕠𝕒𝕕𝕚𝕟𝕘", duration: float = 1.0):
    """Loading decorator that works for both functions and bound methods"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*call_args, **kwargs):
            # Normalize arguments for functions vs bound methods
            self_obj = None
            update = None
            context = None
            extra_args = []

            # Helpers to identify types without importing telegram classes here
            def is_update(obj):
                return obj is not None and (hasattr(obj, 'callback_query') or hasattr(obj, 'message'))

            def is_message(obj):
                return obj is not None and hasattr(obj, 'message_id') and hasattr(obj, 'chat')

            def is_context(obj):
                return obj is not None and hasattr(obj, 'user_data')

            # Try to map arguments
            if len(call_args) >= 3 and is_update(call_args[1]) and is_context(call_args[2]):
                # Bound method with Update and Context
                self_obj = call_args[0]
                update = call_args[1]
                context = call_args[2]
                extra_args = list(call_args[3:])
            elif len(call_args) >= 3 and is_message(call_args[1]):
                # Bound method with Message passed instead of Update
                self_obj = call_args[0]
                message_arg = call_args[1]
                # Find context among the rest
                ctx_idx = None
                for idx in range(2, len(call_args)):
                    if is_context(call_args[idx]):
                        context = call_args[idx]
                        ctx_idx = idx
                        break
                # If no context, just run function as-is
                if context is None:
                    return await func(*call_args, **kwargs)
                extra_args = list(call_args[2:ctx_idx]) + list(call_args[ctx_idx+1:])
                update = None
            elif len(call_args) >= 2 and is_update(call_args[0]) and is_context(call_args[1]):
                # Function with Update and Context
                update = call_args[0]
                context = call_args[1]
                extra_args = list(call_args[2:])
            elif len(call_args) >= 2 and is_message(call_args[0]) and is_context(call_args[1]):
                # Function with Message and Context
                update = None
                context = call_args[1]
                extra_args = list(call_args[2:])
            else:
                # Unknown pattern - run without loading
                return await func(*call_args, **kwargs)

            message = None
            animation_task = None
            message_id = None

            try:
                # Get message if update is a proper Update-like object
                if update is not None and hasattr(update, 'callback_query') and update.callback_query:
                    await update.callback_query.answer()
                    message = update.callback_query.message
                    message_id = message.message_id

                    if message_id in loading_in_progress:
                        # Just run the function without new loading animation
                        if self_obj is not None:
                            return await func(self_obj, update, context, *extra_args, **kwargs)
                        else:
                            return await func(update, context, *extra_args, **kwargs)

                    loading_in_progress.add(message_id)
                    append_loading = True

                elif update is not None and hasattr(update, 'message') and update.message:
                    # For new messages, create with animation
                    styles = animator.get_random_styles()
                    first_frame = []
                    for style in styles:
                        frames = animator.ANIMATIONS.get(style, animator.ANIMATIONS['rainbow'])
                        first_frame.append(frames[0])
                    initial_text = f"{first_frame[0]} {first_frame[1]} {text} {first_frame[1]} {first_frame[0]}"
                    message = await update.message.reply_text(initial_text)
                    message_id = message.message_id
                    loading_in_progress.add(message_id)
                    append_loading = False

                # If a Message object was passed directly (bound or function form)
                if message is None:
                    # Detect message in arguments again
                    msg_obj = None
                    if len(call_args) >= 1 and is_message(call_args[0]):
                        msg_obj = call_args[0]
                    if len(call_args) >= 2 and is_message(call_args[1]):
                        msg_obj = call_args[1]

                    if msg_obj is not None:
                        message = msg_obj
                        message_id = message.message_id
                        loading_in_progress.add(message_id)
                        append_loading = True

                # If we still don't have message or context, just run the function
                if not message or context is None:
                    if self_obj is not None:
                        return await func(self_obj, update, context, *extra_args, **kwargs)
                    else:
                        return await func(update, context, *extra_args, **kwargs)

                # Store in context
                context.user_data['_loading_message'] = message

                # Cancel any existing animation
                if message_id in active_loadings:
                    old_task = active_loadings[message_id]
                    if not old_task.done():
                        old_task.cancel()
                        try:
                            await old_task
                        except asyncio.CancelledError:
                            pass
                    del active_loadings[message_id]

                # Start animation
                animation_task = asyncio.create_task(
                    animator.animate_multiple(
                        message=message,
                        text=text,
                        speed=0.25,
                        append_to_text=append_loading
                    )
                )
                active_loadings[message_id] = animation_task

                # Wait for the specified duration
                await asyncio.sleep(duration)

                # Stop animation
                animator.stop(message_id)

                # Wait for animation to stop
                await asyncio.sleep(0.2)

                # Cancel task if still running
                if animation_task and not animation_task.done():
                    animation_task.cancel()
                    try:
                        await animation_task
                    except asyncio.CancelledError:
                        pass

                # Clean up from active loadings
                if message_id in active_loadings:
                    del active_loadings[message_id]

                # Now run the actual function
                if self_obj is not None:
                    result = await func(self_obj, update, context, *extra_args, **kwargs)
                else:
                    result = await func(update, context, *extra_args, **kwargs)

                return result

            except Exception:
                # Cleanup on error
                if message:
                    animator.stop(message.message_id)
                    if message.message_id in active_loadings:
                        del active_loadings[message.message_id]
                if animation_task and not animation_task.done():
                    animation_task.cancel()
                    try:
                        await animation_task
                    except asyncio.CancelledError:
                        pass
                raise

            finally:
                # Cleanup
                if message_id and message_id in loading_in_progress:
                    loading_in_progress.remove(message_id)
                if context and '_loading_message' in context.user_data:
                    del context.user_data['_loading_message']

        return wrapper
    
    # Allow using decorator without parentheses
    if callable(text):
        func = text
        text = "𝕃𝕠𝕒𝕕𝕚𝕟𝕘"
        duration = 1.0
        return decorator(func)
    
    return decorator

# Alternative decorator for navigation (without loading)
def without_loading(func):
    """Decorator for functions that should not show loading when called from other functions"""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # Check if this is being called from another command with loading
        if context.user_data.get('_loading_message'):
            # Don't add another loading animation
            return await func(update, context, *args, **kwargs)
        else:
            # Normal execution with loading
            return await with_loading()(func)(update, context, *args, **kwargs)
    return wrapper