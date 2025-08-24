import aiohttp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from utils.git_api import fetch_readme

# Import the loading system
from utils.loading import show_loading, show_static_loading

# Constants for pagination
PAGE_SIZE = 3000  # Characters per page (leaving room for headers/footers)

async def handle_readme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle README display with loading animation"""
    query = update.callback_query
    await query.answer()

    repo = context.user_data.get("current_repo")
    if not repo:
        await query.edit_message_text("❌ _No repo selected\\. Send me a repository first\\._", parse_mode="MarkdownV2")
        return

    # Reset page to 0 when loading new README
    context.user_data['readme_page'] = 0

    # Show static loading first to preserve the window
    await show_static_loading(
        query.message,
        f"📖 **{escape_markdown(repo, 2)} README**",
        "Loading README file",
        preserve_content=True,
        animation_type="progress",
    )

    # Start animated loading
    loading_task = await show_loading(
        query.message,
        f"📖 **{escape_markdown(repo, 2)} README**",
        "Loading README file",
        animation_type="progress",
    )

    try:
        async with aiohttp.ClientSession() as session:
            text = await fetch_readme(session, repo)

        # Stop loading animation gracefully
        if loading_task and not loading_task.done():
            loading_task.cancel()
            try:
                await loading_task
            except asyncio.CancelledError:
                pass

        if not text:
            repo_escaped = escape_markdown(repo, 2)
            error_text = f"📖 *{repo_escaped} README*\n\n"
            error_text += "❌ *No README Found*\n\n"
            error_text += "This repository does not have a README file\\.\n\n"
            error_text += "💡 *Tip:* A good README helps others understand your project\\!"

            back_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")]
            ])

            await query.edit_message_text(
                error_text,
                parse_mode="MarkdownV2",
                reply_markup=back_keyboard
            )
            return

        # Store full README in context for pagination
        context.user_data['full_readme'] = text

        # Display the first page
        await _display_readme_page(query, context, repo, 0)

    except Exception as e:
        # Stop loading animation gracefully
        if loading_task and not loading_task.done():
            loading_task.cancel()
            try:
                await loading_task
            except asyncio.CancelledError:
                pass

        # Simple error message
        repo_escaped = escape_markdown(repo, 2)
        error_text = f"📖 *{repo_escaped} README*\n\n"
        error_text += "❌ *Fetch Error*\n\n"
        error_text += "Unable to fetch README file\\.\n\n"
        error_text += "💡 *Tip:* Try again in a few moments\\!"

        back_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 Try Again", callback_data="readme"),
                InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")
            ]
        ])

        await query.edit_message_text(
            error_text,
            parse_mode="MarkdownV2",
            reply_markup=back_keyboard
        )


async def handle_readme_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle README page navigation"""
    query = update.callback_query
    await query.answer()

    # Get current state
    repo = context.user_data.get("current_repo")
    full_readme = context.user_data.get("full_readme")
    current_page = context.user_data.get("readme_page", 0)

    if not repo or not full_readme:
        await query.edit_message_text(
            "❌ _README data not found\\. Please reload the repository\\._",
            parse_mode="MarkdownV2"
        )
        return

    # Determine new page based on callback data
    if query.data == "readme_next":
        new_page = current_page + 1
    elif query.data == "readme_prev":
        new_page = current_page - 1
    elif query.data.startswith("readme_page_"):
        new_page = int(query.data.split("_")[-1])
    else:
        new_page = current_page

    # Display the requested page
    await _display_readme_page(query, context, repo, new_page)


async def _display_readme_page(query, context: ContextTypes.DEFAULT_TYPE, repo: str, page: int):
    """Display a specific page of the README"""
    full_readme = context.user_data.get("full_readme", "")

    # Calculate pagination
    pages = _paginate_text(full_readme, PAGE_SIZE)
    total_pages = len(pages)

    # Ensure page is within bounds
    page = max(0, min(page, total_pages - 1))

    # Update current page in context
    context.user_data['readme_page'] = page

    # Get current page content
    if pages:
        page_content = pages[page]
    else:
        page_content = "No content available"

    # Build the message
    repo_escaped = escape_markdown(repo, 2)
    header = f"📖 *README for* __{repo_escaped}__\n"

    # Add page indicator if multiple pages
    if total_pages > 1:
        header += f"📄 _Page {page + 1} of {total_pages}_\n\n"
    else:
        header += "\n"

    # Escape content
    content_escaped = escape_markdown(page_content, 2)

    # Build final text
    final_text = header + content_escaped

    # Create keyboard
    keyboard = _create_readme_keyboard(page, total_pages)

    # Edit message
    try:
        await query.edit_message_text(
            final_text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
    except Exception as e:
        # If message is too long even after pagination, truncate further
        if "Message is too long" in str(e):
            content_truncated = page_content[:PAGE_SIZE - 500] + "\n\n... _(Content truncated)_"
            content_escaped = escape_markdown(content_truncated, 2)
            final_text = header + content_escaped

            await query.edit_message_text(
                final_text,
                parse_mode="MarkdownV2",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )


def _paginate_text(text: str, page_size: int) -> list:
    """Split text into pages intelligently"""
    if not text:
        return [""]

    pages = []
    remaining = text

    while remaining:
        if len(remaining) <= page_size:
            pages.append(remaining)
            break

        # Find a good break point
        truncate_at = page_size

        # Try to break at paragraph
        last_paragraph = remaining.rfind('\n\n', 0, truncate_at)
        if last_paragraph > page_size * 0.7:
            split_at = last_paragraph + 2  # Include the newlines
        else:
            # Try to break at line
            last_line = remaining.rfind('\n', 0, truncate_at)
            if last_line > page_size * 0.7:
                split_at = last_line + 1
            else:
                # Try to break at sentence
                last_sentence = max(
                    remaining.rfind('. ', 0, truncate_at),
                    remaining.rfind('! ', 0, truncate_at),
                    remaining.rfind('? ', 0, truncate_at)
                )
                if last_sentence > page_size * 0.7:
                    split_at = last_sentence + 2
                else:
                    # Break at word
                    last_space = remaining.rfind(' ', 0, truncate_at)
                    if last_space > page_size * 0.7:
                        split_at = last_space + 1
                    else:
                        split_at = truncate_at

        # Add page and continue
        pages.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()

    return pages if pages else [""]


def _create_readme_keyboard(current_page: int, total_pages: int):
    """Create keyboard with navigation buttons"""
    buttons = []

    # Navigation row
    nav_row = []

    # Previous button
    if current_page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Previous", callback_data="readme_prev"))

    # Page indicator (clickable for page selection if many pages)
    if total_pages > 5:
        nav_row.append(InlineKeyboardButton(
            f"📄 {current_page + 1}/{total_pages}",
            callback_data="readme_pages"
        ))

    # Next button
    if current_page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("➡️ Next", callback_data="readme_next"))

    if nav_row:
        buttons.append(nav_row)

    # Quick jump buttons for many pages
    if total_pages > 5:
        jump_row = []

        # First page
        if current_page > 1:
            jump_row.append(InlineKeyboardButton("⏮ First", callback_data="readme_page_0"))

        # Last page
        if current_page < total_pages - 2:
            jump_row.append(InlineKeyboardButton(
                "⏭ Last",
                callback_data=f"readme_page_{total_pages - 1}"
            ))

        if jump_row:
            buttons.append(jump_row)

    # Action buttons
    action_row = [
        InlineKeyboardButton("🔄 Refresh", callback_data="readme"),
        InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")
    ]
    buttons.append(action_row)

    return InlineKeyboardMarkup(buttons)


# Optional: Page selection dialog
async def handle_readme_pages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show page selection dialog"""
    query = update.callback_query
    await query.answer()

    full_readme = context.user_data.get("full_readme", "")
    pages = _paginate_text(full_readme, PAGE_SIZE)
    total_pages = len(pages)
    current_page = context.user_data.get("readme_page", 0)

    # Create page selection keyboard
    buttons = []

    # Create rows of 5 page buttons each
    for i in range(0, total_pages, 5):
        row = []
        for j in range(i, min(i + 5, total_pages)):
            # Mark current page
            if j == current_page:
                button_text = f"• {j + 1} •"
            else:
                button_text = str(j + 1)

            row.append(InlineKeyboardButton(
                button_text,
                callback_data=f"readme_page_{j}"
            ))
        buttons.append(row)

    # Back button
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data=f"readme_page_{current_page}")])

    keyboard = InlineKeyboardMarkup(buttons)

    repo = context.user_data.get("current_repo", "")
    repo_escaped = escape_markdown(repo, 2)

    text = f"📖 *{repo_escaped} README*\n\n"
    text += f"📄 *Select Page*\n\n"
    text += f"Current page: {current_page + 1} of {total_pages}"

    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=keyboard
    )
