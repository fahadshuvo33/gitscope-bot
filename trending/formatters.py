# trending/formatters.py
"""Formatting utilities for trending repositories"""

from utils.formatting import escape_text
from .languages import get_language  # Add this import
import logging

logger = logging.getLogger(__name__)

# Centralized period configuration
PERIODS = {
    "daily": {
        "display": "Daily",
        "emoji": "🌅",
        "description": "Today's Hottest",
        "github_param": "daily"
    },
    "weekly": {
        "display": "Weekly", 
        "emoji": "🗓️",
        "description": "This Week's Top",
        "github_param": "weekly"
    },
    "monthly": {
        "display": "Monthly",
        "emoji": "📅", 
        "description": "This Month's Best",
        "github_param": "monthly"
    }
}

def get_period_info(period_code: str) -> dict:
    """Get period information by code"""
    return PERIODS.get(period_code, {
        "display": period_code.title(),
        "emoji": "📊",
        "description": f"{period_code.title()} Trending",
        "github_param": period_code
    })

def format_languages_menu_text() -> str:
    """Format the main language selection menu text"""
    return (
        "🔥 **TRENDING REPOSITORIES** 🔥\n\n"
        "🎯 Select a programming language to discover what's hot on GitHub:\n\n"
        "✨ _Find the most starred repositories and discover new projects\\!_\n"
        "🚀 _Updated in real\\-time from GitHub's trending algorithm_"
    )

def format_period_selection_text(language_code: str, current_period: str) -> str:
    """Format period selection menu text"""
    lang_info = get_language(language_code)
    
    text = (
        f"{lang_info['emoji']} **{lang_info['display']} Repositories**\n\n"
        f"⏰ Select time period for trending repos:\n\n"
        f"Current: _{current_period}_"
    )
    return text

def format_repo_entry(repo: dict, index: int, show_language: bool = True) -> str:
    """Format a single repository entry for display with enhanced styling"""
    try:
        # Get repo info
        repo_name = repo.get('full_name', 'Unknown')
        owner = repo.get('owner', {}).get('login', 'unknown')
        name = repo.get('name', 'unknown')
        stars = repo.get('stargazers_count', 0)
        forks = repo.get('forks_count', 0)
        watchers = repo.get('watchers_count', 0)
        description = repo.get('description', '') or 'No description available'
        language = repo.get('language', '')
        
        # Truncate description if too long
        if len(description) > 120:
            description = description[:117] + "..."
        
        # Format numbers with proper styling
        def format_number(num):
            if num >= 1000000:
                return f"{num/1000000:.1f}M"
            elif num >= 1000:
                return f"{num/1000:.1f}K"
            else:
                return str(num)
        
        star_str = format_number(stars)
        fork_str = format_number(forks)
        watch_str = format_number(watchers)
        
        # Enhanced formatting with repository name and GitHub link
        text = f"**{index}\\. {escape_text(repo_name)}**\n"
        text += f"🔗 [View on GitHub]({repo.get('html_url', '')})\n"
        text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"📝 _{escape_text(description)}_\n\n"
        
        # Stats line with better icons and spacing
        stats_line = f"⭐ **{star_str}** stars"
        
        if forks > 0:
            stats_line += f"  •  🔀 **{fork_str}** forks"
        
        if watchers > 0:
            stats_line += f"  •  👁️ **{watch_str}** watching"
        
        if show_language and language:
            from .languages import get_language_emoji
            lang_emoji = get_language_emoji(language)
            stats_line += f"  •  {lang_emoji} **{escape_text(language)}**"
        
        text += stats_line + "\n"
        
        # Add a subtle separator for readability
        text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        return text
    except Exception as e:
        logger.error(f"Error formatting repo: {e}")
        return f"**{index}\\. ❌ Error formatting repository**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

def format_trending_header(language: str, period: str) -> str:
    """Format the header for trending results with enhanced styling"""
    lang_info = get_language(language)
    period_info = get_period_info(period)
    
    # Create a more visually appealing header
    header = f"🔥 **TRENDING {escape_text(lang_info['display'].upper())} REPOSITORIES** 🔥\n"
    header += f"═══════════════════════════════════════════════════════════════\n"
    header += f"{period_info['emoji']} {period_info['description']} Repositories on GitHub\n"
    header += f"═══════════════════════════════════════════════════════════════\n\n"
    
    return header

def format_no_results_message(language_code: str, period: str) -> str:
    """Format a user-friendly no results message"""
    lang_info = get_language(language_code)
    period_info = get_period_info(period)
    
    # Get period suggestions
    other_periods = [p for p in PERIODS.keys() if p != period]
    period_suggestions = " or ".join([f"**{PERIODS[p]['display'].lower()}**" for p in other_periods])
    
    message = f"🤔 **No Trending Results Found**\n\n"
    message += f"No {lang_info['emoji']} **{lang_info['display']}** repositories are trending {period_info['display'].lower()} right now\\.\n\n"
    message += f"💡 **Suggestions:**\n"
    message += f"• Try {period_suggestions.replace('**', '\\*\\*')} periods\n"
    message += f"• Explore other programming languages\n"
    message += f"• Check back later for new trending repos\n\n"
    message += f"🚀 _GitHub's trending algorithm updates regularly\\!_"
    
    return message

def format_error_message(error_type: str = "general") -> str:
    """Format error messages with helpful information"""
    if error_type == "network":
        return (
            "🌐 **Connection Issue**\n\n"
            "Unable to fetch data from GitHub\\. Please check:\n\n"
            "• Your internet connection\n"
            "• GitHub's service status\n"
            "• Try again in a few moments\n\n"
            "🔄 _Most connection issues resolve quickly_"
        )
    elif error_type == "api":
        return (
            "🔧 **API Limit Reached**\n\n"
            "GitHub's API rate limit has been exceeded\\.\n\n"
            "• This resets every hour\n"
            "• Try again later\n"
            "• Consider using different search terms\n\n"
            "⏰ _Limits help keep the service fast for everyone_"
        )
    else:
        return (
            "❌ **Something Went Wrong**\n\n"
            "An unexpected error occurred while fetching trending repositories\\.\n\n"
            "• Please try again\n"
            "• If the problem persists, contact support\n"
            "• Check GitHub's status page\n\n"
            "🔄 _We're working to resolve any issues quickly_"
        )

def get_period_list() -> list:
    """Get list of period codes in order"""
    return list(PERIODS.keys())

def get_period_buttons_data() -> list:
    """Get period button data for UI"""
    return [(f"{info['emoji']} {info['display']}", code) 
            for code, info in PERIODS.items()]