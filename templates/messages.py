SUCCESS_MESSAGE = """✅ **{title}**

{message}

💡 **Tip:** {tip}"""

INFO_MESSAGE = """ℹ️ **{title}**

{message}

💡 **Tip:** {tip}"""

WARNING_MESSAGE = """⚠️ **{title}**

{message}\n\n💡 **Tip:** {tip}"""

LOADING_MESSAGE = """⏳ **Loading** {title}\n
{message}\n\n💡 {tip}"""

def get_success_message(title, message, tip="Operation completed successfully!"):
    return SUCCESS_MESSAGE.format(title=title, message=message, tip=tip)

def get_info_message(title, message, tip="Use /help for more commands"):
    return INFO_MESSAGE.format(title=title, message=message, tip=tip)

def get_warning_message(title, message, tip="Please review the information carefully"):
    return WARNING_MESSAGE.format(title=title, message=message, tip=tip)

def get_loading_message(title, message, tip="Loading\.\.\."):
    return LOADING_MESSAGE.format(title=title, message=message, tip=tip)

def get_invalid_input_message() -> str:
    """Get message for invalid input"""
    return (
        "❌ **Invalid Input**\n\n"
        "I can help you with:\n\n"
        "**GitHub Profiles:**\n"
        "• `username` - e.g., `octocat`\n"
        "• `github.com/username`\n"
        "• `https://github.com/username`\n\n"
        "**GitHub Repositories:**\n"
        "• `owner/repo` - e.g., `microsoft/vscode`\n"
        "• `github.com/owner/repo`\n"
        "• `https://github.com/owner/repo`\n\n"
        "**Commands:**\n"
        "• `/start` - Main menu\n"
        "• `/help` - Show help\n"
        "• `/trending` - Trending repositories"
    )

def get_invalid_command_message() -> str:
    """Get message for invalid command"""
    return (
        "❌ **Invalid Command**\n\n"
        "Available commands:\n\n"
        "• `/start` \\- Main menu\n"
        "• `/help` \\- Show help\n"
        "• `/trending` \\- Trending repositories\n"
        "• `/developer` \\- Developer info\n"
        "• `/about` \\- About bot\n"
    )

def get_invalid_profile_message() -> str:
    """Get message for invalid profile format"""
    return (
        "❌ **Invalid Profile Format**\n\n"
        "Username requirements:\n"
        "• 1-39 characters\n"
        "• Only letters, numbers, and hyphens\n"
        "• Cannot start or end with hyphen\n"
        "• No consecutive hyphens"
    )

def get_invaid_repo_message() -> str:
    """Get message for invalid repository format"""
    return (
        "❌ **Invalid Repository Format**\n\n"
        "Repository requirements:\n"
        "• Can contain letters, numbers, dots, underscores, and hyphens\n"
        "• Cannot be empty\n"
        "• Format: `owner/repository`\n"
        "• URL: `https://github.com/owner/repository`\n"
        "• URL: `github.com/owner/repository`\n"
        "• Invalid URL: `github.com/owner/repository/<invalid>`"
    )

def get_invalid_url_message() -> str:
    """Get message for invalid URL"""
    return (
        "❌ **Invalid URL**\n\n"
        "URL requirements:\n"
        "• Must be a valid GitHub URL\n"
        "• Cannot be empty\n"
        "• Format: `https://github.com/owner`\n"
        "• Format: `https://github.com/owner/repository`\n"
        "• URL: `github.com/owner/repository`\n"
        "• Invalid URL: `github.com/owner/repository/<invalid>`"
    )
