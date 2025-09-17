# GitScope Bot - Run Instructions

## Quick Start

1. **Setup Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your tokens
   ```

2. **Install Dependencies & Run with UV** (Recommended):
   ```bash
   uv sync
   uv run python bot.py
   ```

   Or use the launcher:
   ```bash
   uv run run.py
   ```

3. **Alternative - Run with regular Python**:
   ```bash
   pip install -r requirements.txt
   python bot.py
   ```

## Environment Variables

Create a `.env` file with:

```env
BOT_TOKEN=your_telegram_bot_token_here
GITHUB_TOKEN=your_github_token_here
ADMIN_TELEGRAM_USERNAME=your_telegram_username
ADMIN_GITHUB_USERNAME=your_github_username
```

## Features Working

✅ **Commands**: /start, /help, /about, /developer, /trending, /logs (admin)
✅ **Direct Input**: Send username, repo name, or GitHub URLs
✅ **Message Updates**: No new messages, updates existing ones
✅ **Loading Animations**: Shows progress at bottom of messages
✅ **Error Handling**: User-friendly errors with retry/back buttons
✅ **Admin Features**: Special admin buttons and log access
✅ **Clean Logging**: Only useful logs saved, minimal console output

## Troubleshooting

- **Import errors**: Use `uv run --no-project python bot.py`
- **Bot not responding**: Check BOT_TOKEN in .env
- **GitHub API errors**: Add GITHUB_TOKEN to increase rate limits
- **Permission errors**: Ensure bot has proper Telegram permissions

## Log Levels

The bot now uses selective logging:
- ⚠️ Warnings and errors only
- 🤖 Bot status messages
- ℹ️ Important info messages
- All other noise suppressed

Perfect for production use with UV package manager!