def escape_md(text):
    """Escape special characters for MarkdownV2"""
    if not text:
        return ""
    return str(text).replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('.', '\\.').replace('!', '\\!')

def get_repo_message(name, full_name, description="", language="Unknown", 
                    stars=0, forks=0, issues=0, exists=True, is_admin=False):
    """Generate repository message with dynamic values"""
    if not exists:
        return "❌ **Repository Not Found**\nThe repository doesn't exist or is private\\."
    
    name_esc = escape_md(name)
    full_name_esc = escape_md(full_name)
    desc_esc = escape_md(description or 'No description provided')
    lang_esc = escape_md(language)
    
    if is_admin:
        return f"""👑 **ADMIN \\- {name_esc}**
🔗 `{full_name_esc}`

📊 **Statistics**
├─ ⭐ {stars:,} stars
├─ 🍴 {forks:,} forks
└─ 🐛 {issues:,} open issues

⚙️ **Admin Controls Available**"""
    
    return f"""📚 **{name_esc}**
🔗 `{full_name_esc}`

📝 {desc_esc}

💻 **Language:** {lang_esc}

📊 **Stats**
├─ ⭐ {stars:,} stars
├─ 🍴 {forks:,} forks
└─ 🐛 {issues:,} open issues"""

def get_repo_loading(repo_name):
    """Generate loading message for repository"""
    return f"""📚 **{escape_md(repo_name)}**

💡 Loading repository data\\.\\.\\."""
