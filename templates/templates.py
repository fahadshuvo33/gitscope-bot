# Consolidated Templates - Admin and Loading Functions Only

def escape_md(text):
    """Escape special characters for MarkdownV2"""
    if not text:
        return ""
    return str(text).replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('.', '\\.').replace('!', '\\!')

def get_admin_section(section_type, section_name, name, **data):
    """Generate admin section templates"""
    name_esc = escape_md(name)
    
    sections = {
        'repo_issues': f"👑 **ADMIN \\- ISSUES**\n**{name_esc}**\n🐛 Issues: {data.get('issues', 0):,}\n⚡ Admin Controls",
        'repo_prs': f"👑 **ADMIN \\- PULL REQUESTS**\n**{name_esc}**\n🔄 PRs: {data.get('prs', 0):,}\n⚡ Admin Controls",
        'repo_releases': f"👑 **ADMIN \\- RELEASES**\n**{name_esc}**\n🚀 Releases: {data.get('releases', 0):,}\n⚡ Admin Controls",
        'profile_repos': f"👑 **ADMIN \\- REPOSITORIES**\n**{name_esc}**\n📚 Repos: {data.get('public_repos', 0):,}\n⚡ Admin Controls",
        'profile_followers': f"👑 **ADMIN \\- FOLLOWERS**\n**{name_esc}**\n👥 Followers: {data.get('followers', 0):,}\n⚡ Admin Controls",
        'profile_activity': f"👑 **ADMIN \\- ACTIVITY**\n**{name_esc}**\n📈 Activity Monitoring\n⚡ Admin Controls"
    }
    
    key = f"{section_type}_{section_name}"
    return sections.get(key, f"👑 **ADMIN \\- {name_esc}**\n⚡ Admin Controls Available")

def get_loading_message(message_type, name=""):
    """Generate loading messages"""
    name_esc = escape_md(name) if name else ""
    return f"💡 Loading {name_esc}\\.\\.\\." if name else "💡 Loading\\.\\.\\."
