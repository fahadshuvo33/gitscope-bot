from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

class DeveloperHandler:
    def __init__(self):
        # Update these with your information
        self.developer = "@yourusername"  # Your Telegram username
        self.developer_github = "yourgithubusername"  # Your GitHub username
        self.developer_name = "Your Name"  # Your actual name
        self.developer_bio = "Full Stack Developer | Python Enthusiast | Open Source Contributor"
        self.version = "1.0.0"

    async def handle_developer_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show developer profile"""
        query = update.callback_query
        await query.answer()

        profile_text = (
            f"👨‍💻 *Developer Profile*\n\n"

            f"🏷️ **Name:** {escape_markdown(self.developer_name, 2)}\n"
            f"📱 **Telegram:** {escape_markdown(self.developer, 2)}\n"
            f"💻 **GitHub:** [github\\.com/{self.developer_github}](https://github.com/{self.developer_github})\n\n"

            f"📝 *Bio:*\n{escape_markdown(self.developer_bio, 2)}\n\n"

            "🛠️ *This Bot:*\n"
            f"• Built with Python & python\\-telegram\\-bot\n"
            f"• Uses GitHub REST API v3\n"
            f"• Open source and free to use\n"
            f"• Real\\-time data fetching\n\n"

            "💡 *Skills & Technologies:*\n"
            "🐍 Python • 🤖 Bot Development\n"
            "🌐 Web Development • ⚡ FastAPI\n"
            "🗄️ Databases • ☁️ Cloud Deployment\n"
            "🔧 DevOps • 📊 Data Analysis\n\n"

            "📊 *Bot Statistics:*\n"
            f"• Version: `{escape_markdown(self.version, 2)}`\n"
            f"• Language: Python 3\\.13\n"
            f"• Framework: python\\-telegram\\-bot\n"
            f"• API: GitHub REST API\n\n"

            "💬 *Contact:*\n"
            "• Found a bug\\? Report it\\!\n"
            "• Have suggestions\\? Let me know\\!\n"
            "• Want to collaborate\\? Reach out\\!\n\n"

            "⭐ _If you like this bot, consider starring it on GitHub\\!_"
        )

        keyboard = [
            [
                InlineKeyboardButton("🐙 GitHub Profile", url=f"https://github.com/{self.developer_github}"),
                InlineKeyboardButton("📧 Contact", url=f"https://t.me/{self.developer.replace('@', '')}")
            ],
            [
                InlineKeyboardButton("🤖 Bot Source Code", callback_data="source_code"),
                InlineKeyboardButton("⭐ Rate Bot", callback_data="rate_bot")
            ],
            [
                InlineKeyboardButton("🔄 Other Projects", callback_data="other_projects")
            ],
            [
                InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            profile_text,
            parse_mode="MarkdownV2",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

    async def handle_source_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bot source code information"""
        query = update.callback_query
        await query.answer()

        source_text = (
            "🤖 *Bot Source Code*\n\n"

            "📂 *Repository Structure:*\n"
            "```\n"
            "gitscope\\-bot/\n"
            "├── bot\\.py\n"
            "├── start/\n"
            "│   ├── welcome\\.py\n"
            "│   ├── help\\.py\n"
            "│   ├── about\\.py\n"
            "│   ├── developer\\.py\n"
            "│   └── router\\.py\n"
            "├── handlers/\n"
            "├── utils/\n"
            "└── requirements\\.txt\n"
            "```\n\n"

            "🛠️ *Technologies Used:*\n"
            "• **Language:** Python 3\\.13\n"
            "• **Framework:** python\\-telegram\\-bot\n"
            "• **HTTP Client:** aiohttp\n"
            "• **API:** GitHub REST API v3\n"
            "• **Deployment:** Cloud hosting\n\n"

            "🌟 *Features:*\n"
            "• Modular architecture\n"
            "• Async/await for performance\n"
            "• Error handling & timeouts\n"
            "• Clean code structure\n"
            "• Comprehensive logging\n\n"

            "📝 *Want to contribute\\?*\n"
            "• Fork the repository\n"
            "• Create a feature branch\n"
            "• Submit a pull request\n"
            "• Follow coding standards\n\n"

            "_This bot is open source and free to use\\!_"
        )

        keyboard = [
            [
                InlineKeyboardButton("📂 View Source", url=f"https://github.com/{self.developer_github}/gitscope-bot"),
                InlineKeyboardButton("🐛 Report Bug", url=f"https://github.com/{self.developer_github}/gitscope-bot/issues")
            ],
            [
                InlineKeyboardButton("⬅️ Back to Profile", callback_data="developer_profile")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            source_text,
            parse_mode="MarkdownV2",
            reply_markup=reply_markup
        )

    async def handle_other_projects(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show other projects by the developer"""
        query = update.callback_query
        await query.answer()

        projects_text = (
            "🔄 *Other Projects*\n\n"

            "🚀 *Recent Projects:*\n\n"

            "🤖 **AI Chat Bot**\n"
            "• Multi\\-language support\n"
            "• OpenAI integration\n"
            "• Custom personality modes\n\n"

            "🌐 **Portfolio Website**\n"
            "• Modern responsive design\n"
            "• Built with React & Node\\.js\n"
            "• Deployed on Vercel\n\n"

            "📊 **Data Analysis Tools**\n"
            "• Python automation scripts\n"
            "• Data visualization\n"
            "• Report generation\n\n"

            "🔧 **DevOps Utilities**\n"
            "• Docker configurations\n"
            "• CI/CD pipelines\n"
            "• Monitoring solutions\n\n"

            "💡 *Upcoming Projects:*\n"
            "• GitHub Analytics Dashboard\n"
            "• Code Review Assistant Bot\n"
            "• Open Source Contribution Tracker\n\n"

            "⭐ _Check out my GitHub for more projects\\!_"
        )

        keyboard = [
            [
                InlineKeyboardButton("🐙 All Projects", url=f"https://github.com/{self.developer_github}?tab=repositories"),
                InlineKeyboardButton("🌟 Starred Repos", url=f"https://github.com/{self.developer_github}?tab=stars")
            ],
            [
                InlineKeyboardButton("⬅️ Back to Profile", callback_data="developer_profile")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            projects_text,
            parse_mode="MarkdownV2",
            reply_markup=reply_markup
        )

    async def handle_rate_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle bot rating"""
        query = update.callback_query
        await query.answer("⭐ Thanks for your interest! You can rate this bot by starring the GitHub repository!")

# Create instance
developer_handler = DeveloperHandler()
