def get_trending_message(time_period="today", language="all"):
    """Get trending repositories message"""
    lang_text = f" \\- {language.title()}" if language != "all" else ""
    period_text = time_period.title()
    
    return f"""📈 **TRENDING{lang_text} \\- {period_text.upper()}**

🔥 **Discover the hottest GitHub repositories**

Select options below to explore trending projects\\!

⏰ **Time Periods:**
• Today \\- Last 24 hours
• This Week \\- Last 7 days  
• This Month \\- Last 30 days

💻 **Popular Languages:**
• All Languages
• Python, JavaScript, Java
• Go, Rust, TypeScript

💡 Use the buttons below to start exploring\\!"""

def get_trending_loading(time_period="today", language="all"):
    """Get trending loading message"""
    lang_text = f" {language.title()}" if language != "all" else ""
    return f"📈 **TRENDING{lang_text} \\- {time_period.upper()}**\n\n💡 Loading trending repositories\\.\\.\\."

def get_trending_list(repos, time_period="today", language="all"):
    """Format trending repositories list"""
    if not repos:
        lang_text = f" {language.title()}" if language != "all" else ""
        return f"📈 **TRENDING{lang_text} \\- {time_period.upper()}**\n\n❌ No trending repositories found\\."
    
    def escape_md(text):
        if not text:
            return ""
        return str(text).replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('.', '\\.').replace('!', '\\!')
    
    lang_text = f" {language.title()}" if language != "all" else ""
    header = f"📈 **TRENDING{lang_text} \\- {time_period.upper()}**\n\n"
    
    repo_list = ""
    for i, repo in enumerate(repos[:10], 1):
        name = escape_md(repo.get('name', 'Unknown'))
        owner = escape_md(repo.get('owner', {}).get('login', 'Unknown'))
        description = escape_md(repo.get('description', 'No description'))
        stars = repo.get('stargazers_count', 0)
        language = escape_md(repo.get('language', 'Unknown'))
        
        if len(description) > 60:
            description = description[:57] + "\\.\\.\\."
        
        repo_list += f"""**{i}\\. {owner}/{name}**
⭐ {stars:,} • 💻 {language}
📝 {description}

"""
    
    return header + repo_list.rstrip()

def get_trending_help():
    """Get trending help message"""
    return """📈 **TRENDING REPOSITORIES HELP**

🔥 **Time Periods:**
• Today \\- Last 24 hours
• This Week \\- Last 7 days
• This Month \\- Last 30 days

💻 **Language Filters:**
• All Languages \\- No filter
• Python \\- Python projects
• JavaScript \\- JS/Node projects
• Java \\- Java applications

📊 **Information Shown:**
• Repository name and owner
• Star count and language
• Description
• Growth metrics

💡 **Tips:**
• Check daily for new trends
• Filter by your interests
• Click repos for details"""
