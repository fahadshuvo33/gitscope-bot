WELCOME_MESSAGE = """
❚█══𝔾𝕚𝕥𝕊𝕔𝕠𝕡𝕖 𝔹𝕠𝕥══█❚

👋 Welcome, **{username}**\\!

🎯 **Your GitHub Explorer**:
• Search user profiles  
• Browse repositories
• Check trending repositories

🔍 **Ready to explore GitHub?**"""

def get_welcome_message(username="User"):
    return WELCOME_MESSAGE.format(username=username)
