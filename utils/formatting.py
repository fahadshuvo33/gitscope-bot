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

def get_language_emoji(language):
    """Get emoji for programming language"""
    language_emojis = {
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
        'JSON': '📋',
        'Dart': '🎯',
        'R': '📊',
        'Scala': '🔴',
        'Perl': '🐪',
        'Lua': '🌙',
        'Haskell': '🎓',
        'Clojure': '🍀',
        'Elixir': '💧',
        'Erlang': '📡',
        'F#': '🔷',
        'OCaml': '🐫',
        'Vim script': '📝',
        'PowerShell': '💙',
        'Assembly': '⚙️',
        'Makefile': '🔨',
        'CMake': '🏗️'
    }
    return language_emojis.get(language, '📝')

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

def format_repo_info(repo_data, is_admin_repo: bool = False):
    """Format repository basic information with enhanced UI"""
    if not repo_data:
        return "❌ Repository information not available"

    # Safely get values with defaults
    full_name = escape_text(repo_data.get('full_name', 'Unknown'))
    description = repo_data.get('description')
    language = repo_data.get('language')
    license_info = repo_data.get('license')
    homepage = repo_data.get('homepage', '')

    # Handle description
    if description:
        if len(description) > 200:
            description = description[:200] + "..."
        description = escape_text(description)
    else:
        description = "_No description available_"

    # Handle language
    if language:
        lang_emoji = get_language_emoji(language)
        language_text = f"{lang_emoji} {escape_text(language)}"
    else:
        language_text = "📝 _Not specified_"

    # Handle license
    if license_info:
        license_name = license_info.get('name', 'Unknown')
        license_emoji = get_license_emoji(license_name)
        license_text = f"{license_emoji} {escape_text(license_name)}"
    else:
        license_text = "❌ _No license_"

    # Format stats with better readability
    stars = format_number(repo_data.get('stargazers_count', 0))
    forks = format_number(repo_data.get('forks_count', 0))
    watchers = format_number(repo_data.get('subscribers_count', 0))
    issues = format_number(repo_data.get('open_issues_count', 0))
    size = format_file_size(repo_data.get('size', 0) * 1024)  # GitHub size is in KB

    # Repository status indicators
    is_fork = repo_data.get('fork', False)
    is_archived = repo_data.get('archived', False)
    is_private = repo_data.get('private', False)

    status_indicators = []
    if is_fork:
        status_indicators.append("🍴 _Fork_")
    if is_archived:
        status_indicators.append("📦 _Archived_")
    if is_private:
        status_indicators.append("🔒 _Private_")

    # Build the main info message
    info = (
        f"📂 **{full_name}**\n\n"
        f"📝 {description}\n\n"
    )

    # Add status indicators if any
    if status_indicators:
        info += f"🏷️ {' • '.join(status_indicators)}\n\n"

    # Statistics section with better visual hierarchy
    info += (
        f"📊 **Repository Statistics:**\n"
        f"⭐ `{stars}` stars • 🍴 `{forks}` forks\n"
        f"👀 `{watchers}` watchers • 🐛 `{issues}` open issues\n"
        f"💾 Size: `{size}`\n\n"

        f"ℹ️ **Details:**\n"
        f"💻 Language: {language_text}\n"
        f"📄 License: {license_text}\n"
        f"📅 Created: `{humanize_date(repo_data.get('created_at', ''))}`\n"
        f"🔄 Updated: `{humanize_date(repo_data.get('updated_at', ''))}`\n"
    )

    # Add homepage if available
    if homepage:
        homepage_escaped = escape_text(homepage)
        info += f"🌐 Homepage: [{homepage_escaped}]({homepage})\n"

    # Add GitHub link
    github_url = repo_data.get('html_url', '')
    if github_url:
        info += f"\n🔗 [View on GitHub]({github_url})"

    # Add default branch info
    default_branch = repo_data.get('default_branch', 'main')
    info += f"\n🌿 Default branch: `{escape_text(default_branch)}`"

    # Add admin specific badge and styling
    if is_admin_repo:
        admin_header = f"═══════ ✨👑 𝔸𝔻𝕄𝕀ℕ ℝ𝔼ℙ𝕆𝕊𝕀𝕋𝕆ℝ𝕐 👑✨ ═══════\n"
        admin_badge = f"🧨🔥 Where Bugs Go to Multiply 🔥🧨\n"
        admin_footer = f"\n═══════════ 🐛 End of Bugs 🐛 ═══════════\n"
        info = f"{admin_header}{admin_badge}\n{info}{admin_footer}"

    return info

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

def get_topic_emojis(topics):
    """Get appropriate emojis for repository topics"""
    topic_emojis = {
        'web': '🌐',
        'mobile': '📱',
        'desktop': '💻',
        'api': '🔌',
        'library': '📚',
        'framework': '🏗️',
        'tool': '🔧',
        'cli': '⌨️',
        'bot': '🤖',
        'game': '🎮',
        'ml': '🧠',
        'ai': '🤖',
        'blockchain': '⛓️',
        'security': '🔒',
        'testing': '🧪',
        'documentation': '📖',
        'tutorial': '🎓',
        'template': '📋',
        'awesome': '⭐',
        'list': '📝'
    }

    result = []
    for topic in topics[:5]:  # Limit to 5 topics
        emoji = topic_emojis.get(topic.lower(), '🏷️')
        result.append(f"{emoji} {escape_text(topic)}")

    return result

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

def format_profile_info(profile_data):
    """Format user profile information"""
    if not profile_data:
        return "❌ Profile information not available"

    login = escape_text(profile_data.get('login', 'Unknown'))
    name = profile_data.get('name')
    bio = profile_data.get('bio')
    company = profile_data.get('company')
    location = profile_data.get('location')
    blog = profile_data.get('blog')
    twitter = profile_data.get('twitter_username')
    
    # Build profile info
    info = f"👤 **{login}**\n"
    
    if name and name != login:
        info += f"📝 {escape_text(name)}\n"
    
    info += "\n"
    
    if bio:
        bio_text = escape_text(bio[:200] + "..." if len(bio) > 200 else bio)
        info += f"💭 {bio_text}\n\n"
    
    # Stats
    followers = format_number(profile_data.get('followers', 0))
    following = format_number(profile_data.get('following', 0))
    repos = format_number(profile_data.get('public_repos', 0))
    gists = format_number(profile_data.get('public_gists', 0))
    
    info += (
        f"📊 **Statistics:**\n"
        f"👥 `{followers}` followers • `{following}` following\n"
        f"📚 `{repos}` repositories • `{gists}` gists\n\n"
    )
    
    # Additional info
    info += "ℹ️ **Details:**\n"
    
    if company:
        info += f"🏢 Company: {escape_text(company)}\n"
    
    if location:
        info += f"📍 Location: {escape_text(location)}\n"
    
    if blog:
        blog_escaped = escape_text(blog)
        info += f"🌐 Website: [{blog_escaped}]({blog})\n"
    
    if twitter:
        info += f"🐦 Twitter: [@{escape_text(twitter)}](https://twitter.com/{twitter})\n"
    
    info += f"📅 Joined: `{humanize_date(profile_data.get('created_at', ''))}`\n"
    
    # GitHub profile link
    html_url = profile_data.get('html_url', '')
    if html_url:
        info += f"\n🔗 [View on GitHub]({html_url})"
    
    return info

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
