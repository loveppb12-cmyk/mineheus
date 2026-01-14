import asyncio
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your bot token
BOT_TOKEN = "8562585775:AAFOzbtE2xsqedrx-hj1LXfhmLvvnSetgxQ"

class MentionBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.user_cache = {}
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup command handlers"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("qwer", self.mention_all_members))
        self.application.add_handler(CommandHandler("mention", self.mention_all_members))
        self.application.add_handler(CommandHandler("test", self.test_command))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message"""
        welcome_text = """
🤖 **Group Mention Bot**

**Commands:**
• `/start` - Show this message
• `/help` - Help & instructions
• `/qwer [message]` - Mention all members
• `/mention [message]` - Alternative command
• `/test` - Test bot permissions

**Example:**
`/qwer Hello everyone join our channel @example`

The bot will:
1. Post your message
2. Mention members in batches of 5
3. Wait 5 seconds between batches

⚠️ **Bot must be admin to mention everyone!**
        """
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send help message"""
        help_text = """
📚 **How to use:**

1. Add bot to your group
2. Make bot **admin** (required!)
3. Use: `/qwer your message here`

**Format:**
