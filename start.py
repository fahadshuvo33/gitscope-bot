from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

class StartHandler:
    def __init__(self):
        self.bot_name = "Git Scope"
        self.version = "1.0.0"
        self.developer = "@fahadshuvo"  # Replace with your actual username
        self.developer_github = "fahadshuvo33"  # Replace with your GitHub username
        self.developer_name = "Fahad Hossain"  # Replace with your actual name
        self.developer_bio = "Ai Developer | Python Developer | Api Developer"

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command with welcome message and instructions"""
        user = update.effective_user
        user_name = escape_markdown(user.first_name or "there", 2)

        welcome_text = (
            f"👋 *Hello {user_name}\\!*\n\n"
            f"🚀 Welcome to **{escape_markdown(self.bot_name, 2)}**\n"
            f"_Version {escape_markdown(self.version, 2)}_\n\n"

            "🔍 *What I can do:*\n"
            "• View repository statistics\n"
            "• Show top contributors\n"
            "• List open pull requests & issues\n"
            "• Display programming languages used\n"
            "• Show latest releases\n"
            "• Preview README files\n\n"

            "📝 *How to use:*\n"
            "• Send: `owner/repository`\n"
            "• Or use: `/repo owner/repository`\n"
            "• You can also send GitHub URLs\\!\n\n"

            "💡 *Examples:*\n"
            "• `microsoft/vscode`\n"
            "• `facebook/react`\n"
            "• `google/tensorflow`\n"
            "• `/repo torvalds/linux`\n\n"

            "Ready to explore GitHub repositories\\? 🎯"
        )

        # Create inline keyboard with helpful buttons
        keyboard = [
            [
                InlineKeyboardButton("📖 Help", callback_data="help"),
                InlineKeyboardButton("ℹ️ About", callback_data="about")
            ],
            [
                InlineKeyboardButton("🔥 Popular Repos", callback_data="popular")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Check if it's a callback query or regular message
        if update.callback_query:
            await update.callback_query.edit_message_text(
                welcome_text,
                parse_mode="MarkdownV2",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                welcome_text,
                parse_mode="MarkdownV2",
                reply_markup=reply_markup
            )

        # Clear any existing repo data
        context.user_data.clear()

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle help command or help button"""
        help_text = self._get_help_text()

        if update.callback_query:
            query = update.callback_query
            await query.answer()

            # Back to start button
            keyboard = [[InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                help_text,
                parse_mode="MarkdownV2",
                reply_markup=reply_markup
            )
        else:
            # Regular /help command
            await update.message.reply_text(help_text, parse_mode="MarkdownV2")

    async def handle_about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle about button with clickable developer name"""
        query = update.callback_query
        await query.answer()

        about_text = (
            f"ℹ️ *About {escape_markdown(self.bot_name, 2)}*\n\n"
            f"🔧 Version: `{escape_markdown(self.version, 2)}`\n"
            f"🛠️ Built with: Python \\& python\\-telegram\\-bot\n"
            f"🔗 GitHub API: Official REST API v3\n\n"

            "🌟 *Features:*\n"
            "• Real\\-time GitHub data\n"
            "• Interactive button interface\n"
            "• Support for public repositories\n"
            "• Clean and user\\-friendly design\n"
            "• Fast response times\n\n"

            "🔒 *Privacy:*\n"
            "• No data is stored permanently\n"
            "• Only public GitHub data is accessed\n"
            "• Your searches are not logged\n\n"

            "Made with ❤️ for developers\\!"
        )

        keyboard = [
            [
                InlineKeyboardButton("👨‍💻 Meet the Developer", callback_data="developer_profile")
            ],
            [
                InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            about_text,
            parse_mode="MarkdownV2",
            reply_markup=reply_markup
        )

    async def handle_popular(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show popular repositories suggestions"""
        query = update.callback_query
        await query.answer()

        popular_text = (
            "🔥 *Popular Repositories to Explore:*\n\n"

            "**Frontend Frameworks:**\n"
            "• `facebook/react` \\- React library\n"
            "• `vuejs/vue` \\- Vue\\.js framework\n"
            "• `angular/angular` \\- Angular framework\n\n"

            "**Backend & Languages:**\n"
            "• `nodejs/node` \\- Node\\.js runtime\n"
            "• `python/cpython` \\- Python language\n"
            "• `golang/go` \\- Go programming language\n\n"

            "**Development Tools:**\n"
            "• `microsoft/vscode` \\- VS Code editor\n"
            "• `git/git` \\- Git version control\n"
            "• `docker/docker` \\- Docker containerization\n\n"

            "**AI & Machine Learning:**\n"
            "• `tensorflow/tensorflow` \\- TensorFlow ML\n"
            "• `pytorch/pytorch` \\- PyTorch framework\n"
            "• `huggingface/transformers` \\- NLP models\n\n"

            "**Operating Systems:**\n"
            "• `torvalds/linux` \\- Linux kernel\n"
            "• `microsoft/terminal` \\- Windows Terminal\n"
            "• `apple/darwin-xnu` \\- macOS kernel\n\n"

            "Just click on any repository name or type it manually\\!"
        )

        keyboard = [[InlineKeyboardButton("⬅️ Back to Start", callback_data="back_to_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            popular_text,
            parse_mode="MarkdownV2",
            reply_markup=reply_markup
        )

    async def handle_developer_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show developer profile when username is clicked"""
        query = update.callback_query
        await query.answer()

        # Developer profile text
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

        # Create buttons for developer profile
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
            "├── bot\\.py          # Main bot file\n"
            "├── start\\.py        # Welcome & help\n"
            "├── handlers/       # Feature handlers\n"
            "├── utils/          # API & formatting\n"
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

        # Don't change the message, just show a notification

    async def handle_back_to_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle back to start button"""
        query = update.callback_query
        await query.answer()

        # Call handle_start but make sure update.callback_query is set
        await self.handle_start(update, context)

    def _get_help_text(self):
        """Get formatted help text"""
        return (
            "📖 *Help \\- How to Use This Bot*\n\n"

            "🎯 *Basic Usage:*\n"
            "1\\. Send a repository name: `owner/repository`\n"
            "2\\. Or use the command: `/repo owner/repository`\n"
            "3\\. You can also paste GitHub URLs directly\\!\n\n"

            "🔍 *Valid Formats:*\n"
            "• `microsoft/vscode`\n"
            "• `/repo facebook/react`\n"
            "• `https://github.com/google/tensorflow`\n"
            "• `github.com/torvalds/linux`\n\n"

            "⚙️ *Available Commands:*\n"
            "• `/start` \\- Show welcome message\n"
            "• `/help` \\- Show this help\n"
            "• `/repo <owner/name>` \\- View repository\n\n"

            "🎛️ *Interactive Features:*\n"
            "After sending a repository, use buttons to:\n"
            "• 👥 View top contributors\n"
            "• 🔀 Check open pull requests\n"
            "• 🐛 See open issues\n"
            "• 💻 View programming languages\n"
            "• 🏷️ Check latest releases\n"
            "• 📖 Read README preview\n"
            "• 🔄 Refresh repository data\n\n"

            "⚠️ *Important Notes:*\n"
            "• Only public repositories are supported\n"
            "• Data is fetched in real\\-time from GitHub\n"
            "• Repository must exist and be accessible\n"
            "• Some private repos may show as 'not found'\n\n"

            "Need more help\\? Just ask\\! 😊"
        )

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries for start-related buttons"""
        query = update.callback_query
        action = query.data

        if action == "help":
            await self.handle_help(update, context)
        elif action == "about":
            await self.handle_about(update, context)
        elif action == "popular":
            await self.handle_popular(update, context)
        elif action == "developer_profile":
            await self.handle_developer_profile(update, context)
        elif action == "source_code":
            await self.handle_source_code(update, context)
        elif action == "other_projects":
            await self.handle_other_projects(update, context)
        elif action == "rate_bot":
            await self.handle_rate_bot(update, context)
        elif action == "back_to_start":
            await self.handle_back_to_start(update, context)
        else:
            await query.answer("Unknown action")

# Create global instance
start_handler = StartHandler()
