# utils/languages.py
"""
Central language configuration for the GitHub Explorer Bot.
This module contains all language definitions used throughout the application.
"""

# Main language dictionary - single source of truth
LANGUAGES = {
    "python": {
        "display": "Python",
        "emoji": "🐍",
        "github_name": "Python",
        "short_name": "Python"
    },
    "javascript": {
        "display": "JavaScript",
        "emoji": "🟨",
        "github_name": "JavaScript",
        "short_name": "JS"
    },
    "typescript": {
        "display": "TypeScript",
        "emoji": "🔷",
        "github_name": "TypeScript",
        "short_name": "TS"
    },
    "java": {
        "display": "Java",
        "emoji": "☕",
        "github_name": "Java",
        "short_name": "Java"
    },
    "cpp": {
        "display": "C++",
        "emoji": "🔧",
        "github_name": "C++",
        "short_name": "C++"
    },
    "c": {
        "display": "C",
        "emoji": "🔵",
        "github_name": "C",
        "short_name": "C"
    },
    "csharp": {
        "display": "C#",
        "emoji": "🟦",
        "github_name": "C#",
        "short_name": "C#"
    },
    "go": {
        "display": "Go",
        "emoji": "🐹",
        "github_name": "Go",
        "short_name": "Go"
    },
    "rust": {
        "display": "Rust",
        "emoji": "🦀",
        "github_name": "Rust",
        "short_name": "Rust"
    },
    "ruby": {
        "display": "Ruby",
        "emoji": "💎",
        "github_name": "Ruby",
        "short_name": "Ruby"
    },
    "php": {
        "display": "PHP",
        "emoji": "🐘",
        "github_name": "PHP",
        "short_name": "PHP"
    },
    "swift": {
        "display": "Swift",
        "emoji": "🍎",
        "github_name": "Swift",
        "short_name": "Swift"
    },
    "kotlin": {
        "display": "Kotlin",
        "emoji": "🟣",
        "github_name": "Kotlin",
        "short_name": "Kotlin"
    },
    "dart": {
        "display": "Dart",
        "emoji": "🎯",
        "github_name": "Dart",
        "short_name": "Dart"
    },
    "scala": {
        "display": "Scala",
        "emoji": "🔴",
        "github_name": "Scala",
        "short_name": "Scala"
    },
    "r": {
        "display": "R",
        "emoji": "📊",
        "github_name": "R",
        "short_name": "R"
    },
    "matlab": {
        "display": "MATLAB",
        "emoji": "🧮",
        "github_name": "MATLAB",
        "short_name": "MATLAB"
    },
    "julia": {
        "display": "Julia",
        "emoji": "🟩",
        "github_name": "Julia",
        "short_name": "Julia"
    },
    "perl": {
        "display": "Perl",
        "emoji": "🐪",
        "github_name": "Perl",
        "short_name": "Perl"
    },
    "lua": {
        "display": "Lua",
        "emoji": "🌙",
        "github_name": "Lua",
        "short_name": "Lua"
    },
    "haskell": {
        "display": "Haskell",
        "emoji": "🎓",
        "github_name": "Haskell",
        "short_name": "Haskell"
    },
    "clojure": {
        "display": "Clojure",
        "emoji": "🌀",
        "github_name": "Clojure",
        "short_name": "Clojure"
    },
    "elixir": {
        "display": "Elixir",
        "emoji": "💧",
        "github_name": "Elixir",
        "short_name": "Elixir"
    },
    "erlang": {
        "display": "Erlang",
        "emoji": "📡",
        "github_name": "Erlang",
        "short_name": "Erlang"
    },
    "fsharp": {
        "display": "F#",
        "emoji": "🔷",
        "github_name": "F#",
        "short_name": "F#"
    },
    "ocaml": {
        "display": "OCaml",
        "emoji": "🐫",
        "github_name": "OCaml",
        "short_name": "OCaml"
    },
    "nim": {
        "display": "Nim",
        "emoji": "👑",
        "github_name": "Nim",
        "short_name": "Nim"
    },
    "crystal": {
        "display": "Crystal",
        "emoji": "💠",
        "github_name": "Crystal",
        "short_name": "Crystal"
    },
    "zig": {
        "display": "Zig",
        "emoji": "⚡",
        "github_name": "Zig",
        "short_name": "Zig"
    },
    "v": {
        "display": "V",
        "emoji": "🔻",
        "github_name": "V",
        "short_name": "V"
    },
    "assembly": {
        "display": "Assembly",
        "emoji": "⚙️",
        "github_name": "Assembly",
        "short_name": "Assembly"
    },
    "shell": {
        "display": "Shell",
        "emoji": "🐚",
        "github_name": "Shell",
        "short_name": "Shell"
    },
    "powershell": {
        "display": "PowerShell",
        "emoji": "🔷",
        "github_name": "PowerShell",
        "short_name": "PS"
    },
    "bash": {
        "display": "Bash",
        "emoji": "📟",
        "github_name": "Shell",  # GitHub groups bash under Shell
        "short_name": "Bash"
    },
    "makefile": {
        "display": "Makefile",
        "emoji": "🔨",
        "github_name": "Makefile",
        "short_name": "Make"
    },
    "cmake": {
        "display": "CMake",
        "emoji": "🏗️",
        "github_name": "CMake",
        "short_name": "CMake"
    },
    "dockerfile": {
        "display": "Dockerfile",
        "emoji": "🐳",
        "github_name": "Dockerfile",
        "short_name": "Docker"
    },
    "yaml": {
        "display": "YAML",
        "emoji": "📝",
        "github_name": "YAML",
        "short_name": "YAML"
    },
    "json": {
        "display": "JSON",
        "emoji": "📋",
        "github_name": "JSON",
        "short_name": "JSON"
    },
    "xml": {
        "display": "XML",
        "emoji": "📄",
        "github_name": "XML",
        "short_name": "XML"
    },
    "html": {
        "display": "HTML",
        "emoji": "🌐",
        "github_name": "HTML",
        "short_name": "HTML"
    },
    "css": {
        "display": "CSS",
        "emoji": "🎨",
        "github_name": "CSS",
        "short_name": "CSS"
    },
    "scss": {
        "display": "SCSS",
        "emoji": "🎨",
        "github_name": "SCSS",
        "short_name": "SCSS"
    },
    "sql": {
        "display": "SQL",
        "emoji": "🗄️",
        "github_name": "SQL",
        "short_name": "SQL"
    },
    "graphql": {
        "display": "GraphQL",
        "emoji": "🔀",
        "github_name": "GraphQL",
        "short_name": "GraphQL"
    },
    "vimscript": {
        "display": "Vim Script",
        "emoji": "📝",
        "github_name": "Vim script",
        "short_name": "Vim"
    },
    "emacs-lisp": {
        "display": "Emacs Lisp",
        "emoji": "🧬",
        "github_name": "Emacs Lisp",
        "short_name": "Emacs"
    },
    "tex": {
        "display": "TeX",
        "emoji": "📚",
        "github_name": "TeX",
        "short_name": "TeX"
    },
    "jupyter-notebook": {
        "display": "Jupyter Notebook",
        "emoji": "📓",
        "github_name": "Jupyter Notebook",
        "short_name": "Jupyter"
    },
    "all": {
        "display": "All Languages",
        "emoji": "🌍",
        "github_name": None,  # Special case
        "short_name": "All"
    }
}

# Helper functions
def get_language(code: str) -> dict:
    """Get language info by code, with fallback"""
    return LANGUAGES.get(code, {
        "display": code.title(),
        "emoji": "💻",
        "github_name": code,
        "short_name": code
    })

def get_language_emoji(language_name: str) -> str:
    """Get emoji for a language by its name (case-insensitive)"""
    language_lower = language_name.lower()
    
    # Try to find by code
    if language_lower in LANGUAGES:
        return LANGUAGES[language_lower]["emoji"]
    
    # Try to find by display name or github name
    for code, info in LANGUAGES.items():
        if (info["display"].lower() == language_lower or 
            (info["github_name"] and info["github_name"].lower() == language_lower)):
            return info["emoji"]
    
    # Default emoji
    return "💻"

def get_github_language_name(code: str) -> str:
    """Get GitHub's expected language name for search"""
    lang = get_language(code)
    return lang.get("github_name", code)

def format_language_button(code: str) -> str:
    """Format language for button display"""
    lang = get_language(code)
    return f"{lang['emoji']} {lang['short_name']}"

def get_language_display_name(code: str) -> str:
    """Get display name for a language"""
    return get_language(code)["display"]

# Create ordered list for UI display
LANGUAGE_CODES = list(LANGUAGES.keys())