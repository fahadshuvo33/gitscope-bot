import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from utils.git_api import fetch_languages

async def handle_languages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    repo = context.user_data.get("current_repo")
    if not repo:
        await q.edit_message_text("❌ _No repo selected\\. Send me a repository first\\._", parse_mode="MarkdownV2")
        return

    # Loading state
    await q.edit_message_text("⏳ *Fetching languages\\.\\.\\.*", parse_mode="MarkdownV2")

    async with aiohttp.ClientSession() as session:
        languages = await fetch_languages(session, repo)

    # Add back button
    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back to Repository", callback_data="refresh")]
    ])

    if not languages:
        await q.edit_message_text(
            f"❌ _No language data available for_ `{escape_markdown(repo, 2)}`",
            parse_mode="MarkdownV2",
            reply_markup=back_keyboard
        )
        return

    repo_name = escape_markdown(repo, 2)
    text = f"💻 *Programming Languages in* __{repo_name}__:\n\n"

    # Calculate total bytes
    total_bytes = sum(languages.values())
    sorted_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)

    # Language emojis mapping
    lang_emojis = {
        'JavaScript': '🟨',
        'TypeScript': '🔵',
        'Python': '🐍',
        'Java': '☕',
        'C++': '⚡',
        'C': '🔧',
        'C#': '💜',
        'Go': '🐹',
        'Rust': '🦀',
        'Ruby': '💎',
        'PHP': '🐘',
        'Swift': '🍎',
        'Kotlin': '🟣',
        'HTML': '🌐',
        'CSS': '🎨',
        'Shell': '🐚',
        'Dockerfile': '🐳',
        'YAML': '📄',
        'JSON': '📋'
    }

    for lang, bytes_count in sorted_languages:
        percentage = (bytes_count / total_bytes) * 100
        emoji = lang_emojis.get(lang, '📝')
        lang_escaped = escape_markdown(lang, 2)

        # Create progress bar
        bar_length = int(percentage / 5)  # Scale down to fit
        bar = '█' * bar_length + '░' * (20 - bar_length)

        text += f"{emoji} *{lang_escaped}*: `{percentage:.1f}%`\n"
        text += f"   `{escape_markdown(bar, 2)}`\n\n"

    await q.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=back_keyboard
    )
