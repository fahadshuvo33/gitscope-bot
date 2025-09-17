# GitScope Bot

A simplified Telegram bot for exploring GitHub repositories and user profiles with direct input support.

## Features

- **Direct Input**: No commands needed! Just type:
  - `username` - View GitHub profile
  - `username/repo` - View repository  
  - GitHub URLs - Auto-detected and parsed
- **GitHub Integration**: Real-time data from GitHub API
- **Smart Parsing**: Handles various input formats automatically
- **Clean Interface**: Minimal, focused user experience

## Project Structure

### Core Components

- `bot.py`: Main bot application with direct input handling
- `utils/input_parser.py`: Smart input parsing for usernames, repos, and URLs
- `utils/formatting.py`: Clean formatting for GitHub data display
- `utils/`: Essential utilities for GitHub API, error handling, and UI components

### Templates
- `templates/`: Message templates for consistent user interface
- `buttons/`: Interactive button handlers for navigation

## Usage Examples

Simply send any of these to the bot:

```
octocat
microsoft/vscode  
https://github.com/torvalds/linux
https://github.com/facebook
```

## Commands

- `/start` - Show welcome message
- `/help` - Display usage instructions

## Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (BOT_TOKEN, GITHUB_TOKEN)
4. Run: `python bot.py`

## Requirements

- Python 3.x
- Telegram Bot API Token
- GitHub API Token

## Architecture

The bot uses a simplified architecture focused on direct input processing:

1. **Input Parser** - Analyzes user input to determine type (profile/repo/URL)
2. **GitHub API** - Fetches real-time data from GitHub
3. **Formatter** - Presents data in clean, readable format
4. **Button Manager** - Handles interactive navigation

No complex command routing - just natural input processing!
