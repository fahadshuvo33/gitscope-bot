# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Bot
- `python bot.py` - Start the GitScope Telegram bot
- Requires `.env` file with `BOT_TOKEN` and `GITHUB_TOKEN` environment variables

### Dependencies
- `pip install -r requirements.txt` - Install Python dependencies
- Main dependencies: python-telegram-bot, aiohttp, python-dotenv

## Architecture Overview

### Core Application Flow
The bot uses a **direct input processing** architecture where users send GitHub usernames, repository names, or URLs directly without commands.

**Main Components:**
- `bot.py` - Entry point with handlers and application setup
- `utils/input_parser.py` - Parses user input to identify profiles/repos/URLs
- `utils/git_api.py` - GitHub API wrapper with caching, error handling, and retry logic
- `utils/manager.py` - Central utils manager for consistent API access

### Message Processing Flow
1. User sends text → `handle_text()` in bot.py:200
2. Input parsed by `InputParser.parse_input()`
3. GitHub API called via `utils.github_api` wrapper
4. Response formatted and sent with interactive keyboards

### Key Architectural Patterns

**Input Processing:**
- Supports formats: `username`, `username/repo`, GitHub URLs
- Validation and normalization in input_parser.py:4

**API Layer:**
- Centralized GitHub API client in git_api.py:1
- Built-in caching (5min TTL), retry logic, and error handling
- Session management with connection pooling

**Error Handling:**
- Comprehensive error types: NotFoundError, RateLimitError, NetworkError
- User-friendly error messages in git_api.py:656
- Activity logging to SQLite database

**State Management:**
- Stateless design - no persistent user sessions
- Interactive buttons handled via callback queries
- Loading states with progress indicators

### Directory Structure
- `commands/` - Telegram command handlers (/start, /help, etc.)
- `utils/` - Core utilities (API, formatting, keyboards, logging)
- `templates/` - Message template system
- `repos/` - Repository data caching

### Database
- SQLite database (`logs.db`) for activity logging
- Admin log viewing functionality for debugging

## Development Notes

### GitHub API Integration
- Uses GitHub API v3 with optional token authentication
- Rate limits: 60/hour (unauthenticated) or 5000/hour (with token)
- Implements exponential backoff and request caching

### Message Formatting
- Uses Telegram MarkdownV2 for rich formatting
- Escape utility in formatting.py for special characters
- Loading animations and progress indicators

### Button System
- Unified callback handler in bot.py:24 (`handle_all_buttons`)
- Keyboard generation utilities in utils/keyboards.py
- Navigation patterns for pagination and back buttons