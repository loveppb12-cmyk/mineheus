import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.error import TelegramError

# Enable detailed logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration - REPLACE WITH YOUR TOKEN
BOT_TOKEN = "8562585775:AAFOzbtE2xsqedrx-hj1LXfhmLvvnSetgxQ"  # ⚠️ Change this in production!

class MentionBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
        
    def setup_handlers(self):
        """Setup command handlers"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("qwer", self.mention_all_members))
        self.application.add_handler(CommandHandler("ping", self.ping))
        self.application.add_error_handler(self.error_handler)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message"""
        welcome_text = """
🤖 **Group Mention Bot is Active!**

**Commands:**
• `/start` - Show this message
• `/help` - Help & instructions
• `/qwer [message]` - Mention all members
• `/ping` - Check if bot is working

**Example:**
`/qwer Hello everyone join @example`

**Note:** Bot needs admin rights to fetch all members.
        """
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send help message"""
        help_text = """
📚 **How to use:**

1. Add me to your group
2. Make me **admin** (important!)
3. Use: `/qwer your message here`

**Example:**
`/qwer Important announcement!`

I will:
1. Post your message
2. Mention all members in groups of 5
3. Wait 5 seconds between groups

⚠️ **Requirements:**
• I must be admin in the group
• Works in groups/supergroups only
• I skip bots automatically
        """
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def ping(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check if bot is alive"""
        await update.message.reply_text("🏓 Pong! Bot is alive and working!")
    
    async def check_bot_admin(self, chat_id: int, bot_id: int, context) -> bool:
        """Check if bot is admin in the chat"""
        try:
            chat_member = await context.bot.get_chat_member(chat_id, bot_id)
            return chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
        except Exception as e:
            logger.error(f"Admin check error: {e}")
            return False
    
    async def mention_all_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mention all group members"""
        try:
            chat = update.effective_chat
            message = update.message
            
            # Check if in group
            if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
                await message.reply_text("❌ This command only works in groups!")
                return
            
            # Check if message has text after command
            if not context.args:
                await message.reply_text(
                    "❌ Please add a message!\n\n"
                    "Example: `/qwer Hello everyone!`\n"
                    "Example: `/qwer Join my group @channel`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Get bot info
            bot_info = await context.bot.get_me()
            bot_id = bot_info.id
            
            # Check if bot is admin
            is_admin = await self.check_bot_admin(chat.id, bot_id, context)
            if not is_admin:
                await message.reply_text(
                    "⚠️ **I need to be admin to mention everyone!**\n\n"
                    "Please make me admin in this group settings.\n"
                    "Without admin rights, I can't fetch member list.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Get original message
            original_message = ' '.join(context.args)
            
            # Send processing message
            status_msg = await message.reply_text("⏳ Fetching members list...")
            
            # Get all members
            members = []
            total_count = 0
            mention_count = 0
            
            # Fetch members with error handling
            try:
                async for member in context.bot.get_chat_members(chat.id):
                    total_count += 1
                    
                    # Skip bots
                    if member.user.is_bot:
                        continue
                    
                    # Create mention
                    if member.user.username:
                        mention = f"@{member.user.username}"
                    else:
                        # For users without username, use their name
                        name = member.user.first_name or "User"
                        mention = f"[{name}](tg://user?id={member.user.id})"
                    
                    members.append(mention)
                    mention_count += 1
                    
            except Exception as e:
                logger.error(f"Error fetching members: {e}")
                await status_msg.edit_text(
                    f"❌ Error fetching members: {str(e)[:100]}\n"
                    "Make sure I have admin permissions."
                )
                return
            
            if mention_count == 0:
                await status_msg.edit_text("❌ No members found to mention!")
                return
            
            # Update status
            await status_msg.edit_text(
                f"✅ Found {total_count} total members\n"
                f"📢 Will mention {mention_count} users (bots excluded)\n\n"
                "Starting mentions in 3 seconds..."
            )
            await asyncio.sleep(2)
            
            # Send original message
            await message.reply_text(
                f"📢 **Announcement:** {original_message}\n\n"
                f"👥 Mentioning {mention_count} members...",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Mention in batches
            batch_size = 5
            delay = 5  # seconds between batches
            
            for i in range(0, len(members), batch_size):
                batch = members[i:i + batch_size]
                batch_text = " ".join(batch)
                
                try:
                    # Send the batch
                    await message.reply_text(
                        batch_text,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True
                    )
                    
                    # Show progress
                    progress = min(i + batch_size, len(members))
                    logger.info(f"Progress: {progress}/{len(members)} members mentioned")
                    
                    # Wait before next batch (except last)
                    if i + batch_size < len(members):
                        await asyncio.sleep(delay)
                        
                except Exception as e:
                    logger.error(f"Error sending batch {i}: {e}")
                    # Continue with next batch
                    continue
            
            # Send completion message
            await message.reply_text(
                f"✅ **Done!** Successfully mentioned {mention_count} members!\n\n"
                f"📊 Stats:\n"
                f"• Total members: {total_count}\n"
                f"• Members mentioned: {mention_count}\n"
                f"• Bots skipped: {total_count - mention_count}",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Unexpected error in mention_all_members: {e}", exc_info=True)
            
            # Detailed error message
            error_msg = (
                "❌ **An error occurred!**\n\n"
                "Common issues:\n"
                "1. I'm not admin - Make me admin\n"
                "2. Group is too large - Try in smaller group\n"
                "3. Rate limit - Wait a few minutes\n"
                "4. Privacy settings - Some users can't be mentioned\n\n"
                f"Error: `{str(e)[:100]}`"
            )
            
            try:
                await update.message.reply_text(error_msg, parse_mode=ParseMode.MARKDOWN)
            except:
                pass
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Log errors"""
        logger.error(f"Exception while handling update: {context.error}", exc_info=True)
        
        # Try to send error message
        try:
            if isinstance(update, Update) and update.effective_message:
                await update.effective_message.reply_text(
                    "⚠️ An error occurred. Please check if I'm admin and try again."
                )
        except:
            pass
    
    def run(self):
        """Run the bot"""
        logger.info("🤖 Starting Mention Bot...")
        logger.info(f"Bot username: (will be fetched on startup)")
        
        # Use polling (simpler for debugging)
        self.application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            close_loop=False
        )

def main():
    """Main function"""
    # Check token
    if not BOT_TOKEN or "YOUR_BOT_TOKEN_HERE" in BOT_TOKEN:
        print("❌ ERROR: Please set your BOT_TOKEN in the code")
        print("Replace the BOT_TOKEN variable with your actual token")
        return
    
    # Create and run bot
    bot = MentionBot()
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot crashed: {e}")

if __name__ == '__main__':
    main()
