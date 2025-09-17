# Shared language configuration for both trending implementations

LANGUAGES = [
    {"name": "All Languages", "code": "", "icon": "🌐"},
    {"name": "Python", "code": "python", "icon": "🐍"},
    {"name": "JavaScript", "code": "javascript", "icon": "🍺"},
    {"name": "TypeScript", "code": "typescript", "icon": "⚡"},
    {"name": "Java", "code": "java", "icon": "☕"},
    {"name": "C", "code": "c", "icon": "🔷"},
    {"name": "C#", "code": "csharp", "icon": "💜"},
    {"name": "C++", "code": "cpp", "icon": "🔧"},
    {"name": "Go", "code": "go", "icon": "🐹"},
    {"name": "Rust", "code": "rust", "icon": "🦀"},
    {"name": "Ruby", "code": "ruby", "icon": "💎"},
    {"name": "PHP", "code": "php", "icon": "🐘"},
    {"name": "Swift", "code": "swift", "icon": "🍎"},
    {"name": "Kotlin", "code": "kotlin", "icon": "🟣"},
    {"name": "Dart", "code": "dart", "icon": "🎯"},
]

def get_language_icon(language_code: str) -> str:
    """Get icon for a programming language by its code"""
    if not language_code:
        return "🌐"
    
    for lang in LANGUAGES:
        if lang["code"].lower() == language_code.lower():
            return lang["icon"]
    return "💻"  # Default icon

def get_language_name(language_code: str) -> str:
    """Get display name for a programming language by its code"""
    if not language_code:
        return "All Languages"
    
    for lang in LANGUAGES:
        if lang["code"].lower() == language_code.lower():
            return lang["name"]
    return language_code.title()  # Fallback to capitalized code