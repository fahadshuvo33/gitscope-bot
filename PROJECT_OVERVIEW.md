# GitScope Bot - Complete Project Documentation

## Overview

GitScope Bot is a Telegram bot that allows users to explore GitHub repositories and user profiles directly through Telegram. The bot supports direct input (no commands needed) and provides an interactive interface for browsing GitHub data.

## Key Features

### ✅ Implemented Features

1. **Direct Input Processing**: No commands needed - just type:
   - `username` → View GitHub profile
   - `username/repo` → View repository
   - GitHub URLs → Auto-detected and parsed

2. **Message Updating**: Bot updates existing messages instead of creating new ones

3. **Loading Animations**: Shows loading indicators at the bottom of messages

4. **Comprehensive Error Handling**: User-friendly error messages with retry/back buttons

5. **Admin Features**: Special admin buttons and logs access for configured admin users

6. **Template System**: Organized message templates for consistent formatting

### 🚧 Features Coming Soon (Placeholders Added)

- Repository contributors, issues, pull requests, releases
- User repositories, starred repos, followers, following
- Avatar display
- README viewing
- Trending repositories by language

## File Structure & Explanations

### Core Files

**`bot.py`** - Main application entry point
- Handles all Telegram bot interactions
- Contains message handlers for text input and button callbacks
- Implements admin detection and loading animations
- Routes different types of callbacks to specialized handlers

**`requirements.txt`** - Python dependencies
- python-telegram-bot==20.7
- aiohttp==3.9.1
- python-dotenv==1.0.0

**`.env.example`** - Environment variables template
- BOT_TOKEN: Telegram bot token
- GITHUB_TOKEN: GitHub API token (optional, increases rate limits)
- ADMIN_TELEGRAM_USERNAME: Admin's Telegram username
- ADMIN_GITHUB_USERNAME: Admin's GitHub username

### Utils Directory (`utils/`)

**`input_parser.py`** - Smart input parsing
- Identifies if user input is a username, repo name, or URL
- Supports various GitHub URL formats
- Validates input format

**`git_api.py`** - GitHub API client
- Comprehensive GitHub API wrapper with caching
- Error handling for rate limits, network issues, not found errors
- Session management and retry logic
- Supports both authenticated and unauthenticated requests

**`loading.py`** - Loading animation system
- Animated loading indicators (progress bars, dots, spinners)
- Updates message content with loading at bottom
- Decorator system for easy loading integration

**`keyboards.py`** - Interactive button system
- Universal pagination keyboard system
- Profile and repository navigation buttons
- Admin-specific buttons
- Error handling buttons (retry, back)

**`formatting.py`** - Text formatting utilities
- MarkdownV2 escaping for special characters
- Profile and repository data formatting

**`manager.py`** - Centralized utilities manager
- GitHub API wrapper with error handling
- Utility function access point

**`db_logger.py`** - Activity logging
- SQLite database logging for bot activities
- Admin log viewing functionality

**`error_handler.py`** - Error management
- Centralized error handling and logging

### Templates Directory (`templates/`)

**`__init__.py`** - Template package initialization
- Exports all template functions
- Central access point for templates

**`profile.py`** - User profile templates
- Profile message formatting
- Admin profile templates
- Loading messages for profiles

**`repos.py`** - Repository templates
- Repository information formatting
- Admin repository templates
- Loading messages for repositories

**`welcome.py`** - Welcome message template
- Bot introduction and welcome text

**`about.py`** - About bot information
- Bot version, features, and description

**`developer.py`** - Developer information
- Contact information and bot details

**`help.py`** - Help and usage instructions
- Command explanations and examples

**`errors.py`** - Error message templates
- Consistent error formatting
- User-friendly error messages

**`trending.py`** - Trending repositories templates
- Language-based trending repo displays

**`templates.py`** - Shared template utilities
- Common functions like markdown escaping
- Admin section generators
- Loading message generators

### Commands Directory (`commands/`)

**`start.py`** - /start command handler
- Welcome message with navigation buttons

**`help.py`** - /help command handler
- Usage instructions and examples

**`trending.py`** - /trending command handler
- Trending repositories by language

**`about.py`** - /about command handler
- Bot information and features

**`developer.py`** - /developer command handler
- Developer contact and information

**`admin.py`** - Admin-only commands
- Log viewing and admin controls

**`router.py`** - Command routing system
- Centralized command handling

## How The Bot Works

### Input Processing Flow

1. **User sends message** → `handle_text()` in bot.py
2. **Input parsing** → `InputParser.parse_input()` identifies type
3. **API call** → GitHub API fetched via utils manager
4. **Template formatting** → Data formatted using templates
5. **Response** → Message updated with loading animation then final content

### Button Interaction Flow

1. **User clicks button** → `handle_callback_query()` receives callback
2. **Route to handler** → Specialized handlers for profile/repo actions
3. **Loading animation** → Shows loading at bottom of current message
4. **Data fetch** → GitHub API called for new data
5. **Update message** → Same message updated with new content and buttons

### Admin Features

- Admin detection based on Telegram username in environment variables
- Special admin buttons for enhanced functionality
- Log viewing capability for debugging
- Admin-specific profile and repository templates

### Error Handling

- Network errors → Retry button with back option
- Not found errors → Clear error message with navigation
- API errors → User-friendly explanations
- All errors logged to database for admin review

## Setup Instructions

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your tokens
   ```

3. **Run Bot**:
   ```bash
   python bot.py
   ```

## Technical Architecture

### Key Design Principles

1. **No New Messages**: Bot always updates existing messages instead of creating new ones
2. **Loading Feedback**: Users always see loading animations during data fetching
3. **Error Recovery**: Every error provides clear recovery options
4. **Admin Features**: Enhanced functionality for administrators
5. **Template System**: Consistent message formatting across all features

### Message Update System

The bot uses a sophisticated message updating system:
- Loading animations appear at the bottom of existing content
- Same message is edited with new content and buttons
- Error states maintain context and provide recovery options

### Caching and Performance

- GitHub API responses cached for 5 minutes
- Connection pooling for efficient API requests
- Retry logic with exponential backoff
- Rate limit handling and user feedback

## Future Development

The foundation is complete with placeholder functions for:
- Repository details (contributors, issues, PRs, releases)
- User details (repositories, starred, followers, following)
- Avatar and README display
- Advanced trending repository features

Each placeholder includes the proper template system, error handling, and navigation structure needed for easy implementation.

---

**Status**: ✅ Bot is fully functional with all core features implemented
**Next Steps**: Implement placeholder features as needed
**Documentation**: Complete and up-to-date