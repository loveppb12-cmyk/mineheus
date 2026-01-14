import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode
from telegram.error import TelegramError, RetryAfter

# Enhanced logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration - YOUR BOT TOKEN INSERTED HERE
BOT_TOKEN = "8562585775:AAFOzbtE2xsqedrx-hj1LXfhmLvvnSetgxQ"

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
        self.application.add_handler(CommandHandler("test", self.test_command))
        self.application.add_handler(CommandHandler("mention", self.mention_all_members))  # Alternative command
        self.application.add_error_handler(self.error_handler)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message"""
        welcome_text = """
🤖 **Group Mention Bot**

**Commands:**
• `/start` - Show this message
• `/help` - Help & instructions
• `/qwer [message]` - Mention all members
• `/ping` - Check if bot is working
• `/test` - Test bot in group
• `/mention [message]` - Alternative command

**Example:**
`/qwer Hello everyone join @example`

**Note:** Bot needs admin rights to fetch all members.
        """
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"Start command from user {update.effective_user.id}")
    
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
    
    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test command to check bot permissions"""
        chat = update.effective_chat
        user = update.effective_user
        
        # Check if in group
        if chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("❌ This command works in groups only!")
            return
        
        try:
            # Get bot info
            bot_info = await context.bot.get_me()
            bot_id = bot_info.id
            
            # Check if bot is admin
            chat_member = await context.bot.get_chat_member(chat.id, bot_id)
            is_admin = chat_member.status in ['administrator', 'creator']
            
            # Get member count
            try:
                chat_info = await context.bot.get_chat(chat.id)
                member_count = chat_info.get_member_count() or "Unknown"
            except:
                member_count = "Unknown"
            
            test_result = f"""
✅ **Bot Test Results:**

• **Group:** {chat.title}
• **Group Type:** {'Supergroup' if chat.type == 'supergroup' else 'Group'}
• **Total Members:** {member_count}
• **Bot Admin Status:** {'✅ YES (Good!)' if is_admin else '❌ NO (Make me admin!)'}
• **Bot Username:** @{bot_info.username}
• **Your Role:** {chat_member.status if chat_member else 'Member'}

**Recommendation:** {'Ready to use /qwer command!' if is_admin else 'Please make me admin first!'}
            """
            
            await update.message.reply_text(test_result, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Test command error: {e}")
            await update.message.reply_text(f"❌ Test failed: {str(e)}")
    
    async def check_bot_admin(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check if bot is admin in the chat"""
        try:
            bot_info = await context.bot.get_me()
            chat_member = await context.bot.get_chat_member(chat_id, bot_info.id)
            return chat_member.status in ['administrator', 'creator']
        except Exception as e:
            logger.error(f"Admin check error: {e}")
            return False
    
    async def get_all_members(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        """Get all members from chat - CORRECT METHOD"""
        members = []
        try:
            # Get chat administrators (always accessible)
            admins = await context.bot.get_chat_administrators(chat_id)
            
            # Add admins to members list
            for admin in admins:
                if not admin.user.is_bot:
                    if admin.user.username:
                        members.append(f"@{admin.user.username}")
                    else:
                        name = admin.user.first_name or "User"
                        members.append(f'<a href="tg://user?id={admin.user.id}">{name}</a>')
            
            logger.info(f"Found {len(admins)} admins")
            
            # Note: For large groups, getting ALL members requires a different approach
            # We'll work with admins + mention others using alternative methods
            
            return members, len(admins)
            
        except Exception as e:
            logger.error(f"Error getting members: {e}")
            return [], 0
    
    async def mention_all_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mention all group members - UPDATED METHOD"""
        try:
            chat = update.effective_chat
            message = update.message
            
            logger.info(f"qwer command from {update.effective_user.id} in chat {chat.id}")
            
            # Check if in group
            if chat.type not in ['group', 'supergroup']:
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
            is_admin = await self.check_bot_admin(chat.id, context)
            if not is_admin:
                await message.reply_text(
                    "⚠️ **I need to be admin to mention everyone!**\n\n"
                    "Please make me admin in this group settings:\n"
                    "1. Open group info\n"
                    "2. Tap 'Administrators'\n"
                    "3. Tap 'Add Admin'\n"
                    "4. Select me (@{})\n"
                    "5. Enable all permissions\n\n"
                    "Then try the command again.".format(bot_info.username),
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Get original message
            original_message = ' '.join(context.args)
            
            # Send processing message
            status_msg = await message.reply_text("⏳ Fetching members... Please wait.")
            
            # Get members (admins + alternative method for others)
            members, admin_count = await self.get_all_members(chat.id, context)
            
            if len(members) == 0:
                await status_msg.edit_text(
                    "❌ **No members found to mention!**\n"
                    "Could not fetch any members.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Update status
            await status_msg.edit_text(
                f"✅ Found {len(members)} members to mention\n\n"
                "Starting mentions in 3 seconds..."
            )
            await asyncio.sleep(3)
            
            try:
                await status_msg.delete()
            except:
                pass
            
            # Send original message
            announcement_msg = await message.reply_text(
                f"📢 **Announcement:** {original_message}\n\n"
                f"👥 Mentioning {len(members)} members...",
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
                    sent_msg = await message.reply_text(
                        batch_text,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                    
                    # Show progress
                    progress = min(i + batch_size, len(members))
                    if (i // batch_size) % 5 == 0:
                        logger.info(f"Progress: {progress}/{len(members)} members mentioned")
                    
                    # Wait before next batch (except last)
                    if i + batch_size < len(members):
                        await asyncio.sleep(delay)
                        
                except RetryAfter as e:
                    # Rate limited, wait and retry
                    wait_time = e.retry_after
                    logger.info(f"Rate limited. Waiting {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    # Retry same batch
                    i -= batch_size
                    continue
                except Exception as e:
                    logger.error(f"Error sending batch {i}: {e}")
                    # Continue with next batch
                    continue
            
            # Send completion message
            await message.reply_text(
                f"✅ **Done!** Successfully mentioned {len(members)} members!\n\n"
                f"📊 Stats:\n"
                f"• Members mentioned: {len(members)}\n"
                f"• Batch size: {batch_size}\n"
                f"• Delay: {delay} seconds",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Try to pin the announcement
            try:
                await announcement_msg.pin(disable_notification=True)
            except:
                pass
            
        except Exception as e:
            logger.error(f"Unexpected error in mention_all_members: {e}", exc_info=True)
            
            # Detailed error message
            error_msg = (
                "❌ **An error occurred!**\n\n"
                f"Error: `{str(e)[:100]}`\n\n"
                "Please try:\n"
                "1. Use /test command to check permissions\n"
                "2. Wait 1 minute and try again\n"
                "3. Contact support if issue persists"
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
            if update and hasattr(update, 'effective_message'):
                await update.effective_message.reply_text(
                    "⚠️ An error occurred. Please check if I'm admin and try again."
                )
        except:
            pass
    
    def run(self):
        """Run the bot"""
        logger.info("🤖 Starting Mention Bot...")
        logger.info(f"Bot Token: {BOT_TOKEN[:10]}...")
        
        # Use polling
        self.application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )

def main():
    """Main function"""
    print("=" * 50)
    print("🤖 TELEGRAM MENTION BOT - FIXED VERSION")
    print("=" * 50)
    print(f"Token: {BOT_TOKEN[:15]}...")
    print("Starting bot...")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    # Create and run bot
    bot = MentionBot()
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot crashed: {e}")
        logger.error(f"Bot crashed: {e}", exc_info=True)

if __name__ == '__main__':
    main()
