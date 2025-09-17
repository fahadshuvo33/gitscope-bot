"""
Universal refresh handler utility for Telegram bot messages.

This utility provides a consistent way to handle refresh operations that might 
cause 'Message not modified' errors by adding temporary timestamps.
"""

import asyncio
from datetime import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import logging
from typing import Optional, Dict
import re

logger = logging.getLogger(__name__)


class RefreshHandler:
    """Handles message refresh operations with timestamp approach to prevent 'Message not modified' errors."""
    
    # Class-level configuration
    DEFAULT_CLEANUP_DELAY = 2
    MIN_REFRESH_INTERVAL = 0.5
    CACHE_CLEANUP_INTERVAL = 3600  # 1 hour
    
    # Rate limiting cache
    _last_refresh_times: Dict[str, float] = {}
    _cleanup_task: Optional[asyncio.Task] = None
    
    @staticmethod
    def escape_markdown_v2(text: str) -> str:
        """Escape special characters for MarkdownV2."""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    @staticmethod
    async def _ensure_cleanup_task():
        """Ensure the cleanup task is running."""
        if RefreshHandler._cleanup_task is None or RefreshHandler._cleanup_task.done():
            RefreshHandler._cleanup_task = asyncio.create_task(
                RefreshHandler._periodic_cleanup()
            )
    
    @staticmethod
    async def _periodic_cleanup():
        """Periodically clean up old entries from rate limiting cache."""
        while True:
            try:
                await asyncio.sleep(RefreshHandler.CACHE_CLEANUP_INTERVAL)
                current_time = asyncio.get_event_loop().time()
                cutoff_time = current_time - RefreshHandler.CACHE_CLEANUP_INTERVAL
                
                RefreshHandler._last_refresh_times = {
                    k: v for k, v in RefreshHandler._last_refresh_times.items() 
                    if v > cutoff_time
                }
                logger.debug(f"Cleaned up rate limiting cache, {len(RefreshHandler._last_refresh_times)} entries remaining")
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    @staticmethod
    async def _apply_rate_limiting(message) -> None:
        """Apply rate limiting to prevent too frequent refreshes."""
        key = f"{message.chat_id}:{message.message_id}"
        now = asyncio.get_event_loop().time()
        
        if key in RefreshHandler._last_refresh_times:
            elapsed = now - RefreshHandler._last_refresh_times[key]
            if elapsed < RefreshHandler.MIN_REFRESH_INTERVAL:
                wait_time = RefreshHandler.MIN_REFRESH_INTERVAL - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s before refresh")
                await asyncio.sleep(wait_time)
        
        RefreshHandler._last_refresh_times[key] = now
    
    @staticmethod
    async def refresh_message(
        message, 
        content: str, 
        keyboard: InlineKeyboardMarkup = None,
        parse_mode: str = "MarkdownV2",
        disable_web_page_preview: bool = True,
        cleanup_delay: Optional[int] = None,
        apply_rate_limit: bool = True
    ):
        """
        Refresh a message with timestamp approach to avoid 'Message not modified' error.
        
        Args:
            message: Telegram message object to edit
            content: The content to display
            keyboard: Inline keyboard markup (optional)
            parse_mode: Parse mode for the message (default: MarkdownV2)
            disable_web_page_preview: Whether to disable web page preview
            cleanup_delay: Seconds to wait before removing timestamp (default: class default)
            apply_rate_limit: Whether to apply rate limiting (default: True)
        """
        # Ensure cleanup task is running
        await RefreshHandler._ensure_cleanup_task()
        
        # Apply rate limiting if enabled
        if apply_rate_limit:
            await RefreshHandler._apply_rate_limiting(message)
        
        # Use class default if cleanup_delay not specified
        if cleanup_delay is None:
            cleanup_delay = RefreshHandler.DEFAULT_CLEANUP_DELAY
        
        try:
            # First try to update normally
            await message.edit_text(
                content,
                parse_mode=parse_mode,
                reply_markup=keyboard,
                disable_web_page_preview=disable_web_page_preview
            )
        except Exception as edit_error:
            # If it's a "not modified" error, use timestamp approach
            if "not modified" in str(edit_error).lower():
                await RefreshHandler._handle_with_timestamp(
                    message, content, keyboard, parse_mode, 
                    disable_web_page_preview, cleanup_delay
                )
            else:
                # Re-raise other errors
                raise edit_error
    
    @staticmethod
    async def _handle_with_timestamp(
        message, 
        content: str, 
        keyboard: InlineKeyboardMarkup,
        parse_mode: str,
        disable_web_page_preview: bool,
        cleanup_delay: int
    ):
        """Handle message refresh with timestamp approach."""
        try:
            # Add timestamp to make content unique
            refresh_time = datetime.now().strftime("%H:%M:%S")
            
            # Format timestamp based on parse mode
            if parse_mode == "MarkdownV2":
                # Escape special characters in timestamp
                refresh_time_escaped = RefreshHandler.escape_markdown_v2(refresh_time)
                timestamped_content = f"{content}\n\n🔄 *Refreshed at {refresh_time_escaped}*"
            elif parse_mode == "HTML":
                timestamped_content = f"{content}\n\n🔄 <b>Refreshed at {refresh_time}</b>"
            else:  # Markdown or None
                timestamped_content = f"{content}\n\n🔄 *Refreshed at {refresh_time}*"
            
            # Update with timestamped content
            await message.edit_text(
                timestamped_content,
                parse_mode=parse_mode,
                reply_markup=keyboard,
                disable_web_page_preview=disable_web_page_preview
            )
            
            # Clean up timestamp after delay
            if cleanup_delay > 0:
                await asyncio.sleep(cleanup_delay)
                try:
                    await message.edit_text(
                        content,
                        parse_mode=parse_mode,
                        reply_markup=keyboard,
                        disable_web_page_preview=disable_web_page_preview
                    )
                except Exception as cleanup_error:
                    # If cleanup fails, log it but don't raise
                    logger.debug(f"Timestamp cleanup failed (acceptable): {cleanup_error}")
        
        except Exception as timestamp_error:
            logger.error(f"Timestamp refresh failed: {timestamp_error}")
            raise timestamp_error
    
    @staticmethod
    async def refresh_callback_query(
        query, 
        content: str, 
        keyboard: InlineKeyboardMarkup = None,
        parse_mode: str = "MarkdownV2",
        disable_web_page_preview: bool = True,
        cleanup_delay: Optional[int] = None,
        answer_callback: bool = True,
        answer_text: Optional[str] = None,
        show_alert: bool = False
    ):
        """
        Refresh a callback query message with timestamp approach.
        
        Args:
            query: CallbackQuery object
            content: The content to display
            keyboard: Inline keyboard markup (optional)
            parse_mode: Parse mode for the message (default: MarkdownV2)
            disable_web_page_preview: Whether to disable web page preview
            cleanup_delay: Seconds to wait before removing timestamp (default: class default)
            answer_callback: Whether to answer the callback query (default: True)
            answer_text: Text to show in callback answer (optional)
            show_alert: Whether to show an alert for callback answer (default: False)
        """
        if answer_callback:
            await query.answer(text=answer_text, show_alert=show_alert)
        
        await RefreshHandler.refresh_message(
            query.message, content, keyboard, parse_mode, 
            disable_web_page_preview, cleanup_delay
        )
    
    @staticmethod
    async def show_refresh_error(
        message, 
        error_title: str,
        error_description: str,
        retry_callback: Optional[str] = None,
        back_callback: Optional[str] = None,
        parse_mode: str = "MarkdownV2"
    ):
        """
        Show an error message with retry/back buttons that includes a timestamp to avoid duplication.
        
        Args:
            message: Message object to edit
            error_title: Title of the error
            error_description: Description of the error
            retry_callback: Callback data for retry button (optional)
            back_callback: Callback data for back button (optional)
            parse_mode: Parse mode for the message
        """
        # Add timestamp to error to make it unique
        error_time = datetime.now().strftime("%H:%M:%S")
        
        # Escape text for MarkdownV2 if needed
        if parse_mode == "MarkdownV2":
            error_title_escaped = RefreshHandler.escape_markdown_v2(error_title)
            error_description_escaped = RefreshHandler.escape_markdown_v2(error_description)
            error_time_escaped = RefreshHandler.escape_markdown_v2(error_time)
            error_content = f"❌ *{error_title_escaped}* _{error_time_escaped}_\n\n{error_description_escaped}"
        elif parse_mode == "HTML":
            error_content = f"❌ <b>{error_title}</b> <i>{error_time}</i>\n\n{error_description}"
        else:
            error_content = f"❌ **{error_title}** _{error_time}_\n\n{error_description}"
        
        # Create keyboard with retry/back buttons
        buttons = []
        if retry_callback and back_callback:
            buttons.append([
                InlineKeyboardButton("🔄 Retry", callback_data=retry_callback),
                InlineKeyboardButton("⬅️ Back", callback_data=back_callback)
            ])
        elif retry_callback:
            buttons.append([
                InlineKeyboardButton("🔄 Retry", callback_data=retry_callback)
            ])
        elif back_callback:
            buttons.append([
                InlineKeyboardButton("⬅️ Back", callback_data=back_callback)
            ])
        
        keyboard = InlineKeyboardMarkup(buttons) if buttons else None
        
        # Use regular edit since error messages with timestamps are always unique
        await message.edit_text(
            error_content,
            parse_mode=parse_mode,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
    
    @staticmethod
    async def force_refresh_message(
        message, 
        content: str,
        keyboard: InlineKeyboardMarkup = None,
        parse_mode: str = "MarkdownV2",
        disable_web_page_preview: bool = True
    ):
        """
        Force refresh by deleting and sending new message (use sparingly).
        
        This should only be used when normal refresh fails consistently.
        
        Args:
            message: Message object to replace
            content: The content to display
            keyboard: Inline keyboard markup (optional)
            parse_mode: Parse mode for the message
            disable_web_page_preview: Whether to disable web page preview
        
        Returns:
            The new message object
        """
        try:
            chat_id = message.chat_id
            await message.delete()
            return await message.chat.send_message(
                content,
                parse_mode=parse_mode,
                reply_markup=keyboard,
                disable_web_page_preview=disable_web_page_preview
            )
        except Exception as e:
            logger.error(f"Force refresh failed: {e}")
            # Fallback to regular refresh
            await RefreshHandler.refresh_message(
                message, content, keyboard, parse_mode, 
                disable_web_page_preview
            )
            return message
    
    @staticmethod
    def set_default_cleanup_delay(delay: int):
        """Set the default cleanup delay for all refreshes."""
        RefreshHandler.DEFAULT_CLEANUP_DELAY = delay
    
    @staticmethod
    def set_min_refresh_interval(interval: float):
        """Set the minimum interval between refreshes."""
        RefreshHandler.MIN_REFRESH_INTERVAL = interval


# Convenience function for backward compatibility
async def refresh_message_content(
    message, 
    content: str, 
    keyboard: InlineKeyboardMarkup = None,
    parse_mode: str = "MarkdownV2"
):
    """
    Convenience function for refreshing message content.
    
    This is a backward-compatible function that uses the RefreshHandler class.
    """
    await RefreshHandler.refresh_message(message, content, keyboard, parse_mode)