from datetime import datetime, timezone

def _escape_markdown_v2(text: str) -> str:
    """Escapes characters that have special meaning in MarkdownV2."""
    if text is None:
        return ""
    
    text = str(text)  # Convert to string if not already
    special_chars = (
        '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!', "'"
    )
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def escape_text(text: str) -> str:
    """Public function to escape text for MarkdownV2"""
    return _escape_markdown_v2(text)

def humanize_date(date_string):
    """Convert ISO date string to human-readable format"""
    try:
        dt = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
        dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt

        days = delta.days
        seconds = delta.seconds

        if days < 1:
            if seconds < 60:
                return f"{seconds}s ago"
            elif seconds < 3600:
                return f"{seconds // 60}m ago"
            else:
                return f"{seconds // 3600}h ago"
        elif days < 30:
            return f"{days}d ago"
        elif days < 365:
            return f"{days // 30}mo ago"
        else:
            return f"{days // 365}y ago"
    except Exception:
        return "Unknown"

def format_number(num):
    """Format large numbers with K/M/B suffixes"""
    if num >= 1000000000:
        return f"{num/1000000000:.1f}B"
    elif num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return str(num)

def format_file_size(bytes_count):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} TB"

def get_license_emoji(license_name):
    """Get emoji for license type"""
    license_emojis = {
        'MIT License': '✅',
        'Apache License 2.0': '🔓',
        'GNU General Public License v3.0': '🆓',
        'BSD 3-Clause "New" or "Revised" License': '📜',
        'BSD 2-Clause "Simplified" License': '📄',
        'Mozilla Public License 2.0': '🦊',
        'The Unlicense': '🚫',
        'ISC License': '📋',
        'GNU Lesser General Public License v3.0': '📚',
        'Creative Commons Zero v1.0 Universal': '🎨'
    }
    return license_emojis.get(license_name, '📄')


def create_progress_bar(percentage, length=20):
    """Create a visual progress bar"""
    filled = int(percentage / 100 * length)
    bar = '█' * filled + '░' * (length - filled)
    return bar

def truncate_text(text, max_length=100, suffix="..."):
    """Safely truncate text with suffix"""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def format_commit_message(message):
    """Format commit message for display"""
    if not message:
        return "_No commit message_"

    # Take first line only
    first_line = message.split('\n')[0]

    # Truncate if too long
    if len(first_line) > 80:
        first_line = first_line[:77] + "..."

    return escape_text(first_line)



def format_topics(topics):
    """Format repository topics with emojis"""
    if not topics:
        return "_No topics specified_"

    topic_list = get_topic_emojis(topics)
    return " • ".join(topic_list)

def calculate_time_ago(date_string):
    """Calculate and return formatted time difference"""
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
        date_obj = date_obj.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = now - date_obj

        if diff.days > 365:
            years = diff.days // 365
            return f"{years}y ago"
        elif diff.days > 30:
            months = diff.days // 30
            return f"{months}mo ago"
        elif diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            return "just now"
    except:
        return "unknown"

def format_user_link(user_data):
    """Format user information with link"""
    if not user_data:
        return "_Unknown user_"

    login = escape_text(user_data.get('login', 'Unknown'))
    html_url = user_data.get('html_url', '')

    if html_url:
        return f"[{login}]({html_url})"
    else:
        return login


def safe_error_message(message: str) -> str:
    """Safely format error message for Telegram"""
    if not message:
        return "❌ An error occurred"
    
    # Remove technical details and escape special characters
    clean_msg = str(message).replace("Can't parse entities:", "").strip()
    clean_msg = _escape_markdown_v2(clean_msg)
    
    # Keep it simple and user-friendly
    if len(clean_msg) > 100:
        return "❌ Unable to process request\\. Please try again\\."
    
def safe_get(data, *keys, default="N/A"):
    """Safely get nested dictionary values"""
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return default
    return data if data is not None else default
