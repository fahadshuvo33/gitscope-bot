DEVELOPER_INFO = """👨‍💻 **𝔻𝔼𝕍𝔼𝕃𝕆ℙ𝔼ℝ 𝕀ℕ𝔽𝕆**

🚀 **GitScope Bot** \\- Your GitHub Explorer

**Developer:** {developer_name}
**Version:** {version}
**Language:** Python
**Framework:** python\\-telegram\\-bot

🌟 **Features:**
• GitHub profile exploration
• Repository browsing
• Trending repositories
• Real\\-time statistics

📧 **Contact:** {contact_email}
🐙 **Source:** {github_url}

💡 **Found a bug or have suggestions\\?**
Feel free to reach out\\!"""

def get_developer_info(version="2\\.0", developer_name="🄵🄰🄷🄰🄳 🄷🄾🅂🅂🄰🄸🄽", github_url="https://github\\.com/fahadshuvo33/gitscope\\-bot", contact_email="fahadshuvo33@gmail\\.com"):
    return DEVELOPER_INFO.format(
        version=version,
        developer_name=developer_name,
        github_url=github_url,
        contact_email=contact_email
    )
