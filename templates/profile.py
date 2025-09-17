def escape_md(text):
    """Escape special characters for MarkdownV2"""
    if not text:
        return ""
    return str(text).replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('.', '\\.').replace('!', '\\!')

def get_profile_message(name, login, bio="", location="", company="", 
                       followers=0, following=0, public_repos=0, exists=True, is_admin=False):
    """Generate profile message with dynamic values"""
    if not exists:
        return "❌ **User Not Found**\nThe user profile doesn't exist or is private\\."
    
    name_esc = escape_md(name)
    login_esc = escape_md(login)
    
    if is_admin:
        return f"""👑 **ADMIN \\- {name_esc}** \\(@{login_esc}\\)

📊 **Account Overview**
├─ 📚 Repositories: {public_repos:,}
├─ 👥 Followers: {followers:,}
└─ 👤 Following: {following:,}

⚙️ **Admin Controls Available**"""
    
    # Build profile info
    info_parts = []
    if bio: info_parts.append(f"📝 {escape_md(bio)}")
    if company: info_parts.append(f"🏢 {escape_md(company)}")
    if location: info_parts.append(f"📍 {escape_md(location)}")
    
    info_text = '\n'.join(info_parts) if info_parts else 'ℹ️ No profile information available'
    activity = '🔥 Active Developer' if public_repos > 0 else '💡 No public repositories'
    
    return f"""👤 **{name_esc}** \\(@{login_esc}\\)

{info_text}

📊 **GitHub Stats**
├─ 📚 Repositories: {public_repos:,}
├─ 👥 Followers: {followers:,}
└─ 👤 Following: {following:,}

{activity}"""

def get_profile_loading(username):
    """Generate loading message for profile"""
    return f"""👤 **{escape_md(username)}**

💡 Loading profile data\\.\\.\\."""
