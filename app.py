import os
import asyncio
import logging
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode
from telegram.error import TelegramError, RetryAfter, BadRequest

# Enhanced logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration - USE ENVIRONMENT VARIABLE FOR SECURITY!
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

class MentionBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
        self.processing_groups = set()
        self.user_cache = {}
        
    def setup_handlers(self):
        """Setup command handlers"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("qwer", self.mention_all_members))
        self.application.add_handler(CommandHandler("ping", self.ping))
        self.application.add_handler(CommandHandler("stats", self.get_stats))
        self.application.add_error_handler(self.error_handler)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message"""
        welcome_text = """
🤖 **Mass Mention Bot**

**Commands:**
• `/start` - Show this message
• `/help` - Detailed instructions
• `/qwer [message]` - Mention all members
• `/ping` - Check bot status
• `/stats` - Get group statistics

**Example:**
`/qwer Important announcement for all members!`

⚠️ **Requires Admin Rights**
        """
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send help message"""
        help_text = """
📚 **MASS MENTION BOT - User Guide**

**For Group Admins:**
1. **Add bot to group**
2. **Make bot ADMIN** with permissions
3. **Usage:** `/qwer your message here`

**Example:** `/qwer Join our new channel @example`

**How it works:**
1. Fetches all members
2. Mentions in batches
3. Skips bots
4. Automatic rate limit handling

**For best results:**
- Use in supergroups
- Test with small group first
- Don't spam (once per hour recommended)
        """
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def ping(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check bot status"""
        await update.message.reply_text("✅ Bot is active and ready!")
    
    async def get_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get group statistics"""
        chat = update.effective_chat
        
        # Check if group
        if chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("❌ This command works in groups only!")
            return
        
        try:
            # Get bot info
            bot_info = await context.bot.get_me()
            
            # Check if admin
            try:
                chat_member = await context.bot.get_chat_member(chat.id, bot_info.id)
                is_admin = chat_member.status in ['administrator', 'creator']
            except:
                is_admin = False
            
            stats_text = f"""
📊 **Group Statistics:**

• **Group:** {chat.title}
• **Type:** {'Supergroup' if chat.type == 'supergroup' else 'Group'}
• **Bot Status:** {'✅ Admin' if is_admin else '❌ Not Admin'}
• **Processing:** {'✅ Available' if chat.id not in self.processing_groups else '⏳ Busy'}
            """
            
            await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Stats error: {e}")
            await update.message.reply_text("❌ Could not fetch statistics")
    
    async def is_bot_admin(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check if bot is admin"""
        try:
            bot_info = await context.bot.get_me()
            chat_member = await context.bot.get_chat_member(chat_id, bot_info.id)
            return chat_member.status in ['administrator', 'creator']
        except Exception as e:
            logger.error(f"Admin check failed: {e}")
            return False
    
    def get_user_mention(self, user):
        """Get mention for a user"""
        if user.username:
            return f"@{user.username}"
        else:
            name = user.first_name or user.last_name or "User"
            return f'<a href="tg://user?id={user.id}">{name}</a>'
    
    async def mention_all_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main mention function"""
        chat = update.effective_chat
        message = update.message
        
        # Check if in group
        if chat.type not in ['group', 'supergroup']:
            await message.reply_text("❌ This command works in groups only!")
            return
        
        # Check admin status
        if not await self.is_bot_admin(chat.id, context):
            admin_instructions = """
⚠️ **BOT NEEDS ADMIN RIGHTS!**

To make me admin:
1. Go to group settings
2. Tap "Administrators"
3. Tap "Add Admin"
4. Select me (the bot)
5. Enable these permissions:
   • Delete messages
   • Ban users
   • Invite users via link

Then try the command again.
            """
            await message.reply_text(admin_instructions, parse_mode=ParseMode.MARKDOWN)
            return
        
        # Get message
        if not context.args:
            await message.reply_text(
                "❌ Please add your message!\n\n"
                "**Format:** `/qwer your message here`\n"
                "**Example:** `/qwer Important announcement!`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        original_message = ' '.join(context.args)
        
        # Send initial status
        status_msg = await message.reply_text(
            "⏳ **Starting mass mention...**\n"
            "Fetching members list...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # Fetch members
            members = []
            fetched_count = 0
            
            async for member in context.bot.get_chat_members(chat.id):
                fetched_count += 1
                if not member.user.is_bot:
                    members.append(self.get_user_mention(member.user))
            
            if not members:
                await status_msg.edit_text(
                    "❌ **No members found to mention!**\n"
                    "All members might be bots.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Update status
            await status_msg.edit_text(
                f"✅ **Ready to mention!**\n\n"
                f"• Members found: {len(members)}\n"
                f"• Starting mentions...",
                parse_mode=ParseMode.MARKDOWN
            )
            
            await asyncio.sleep(2)
            
            # Send original message
            await message.reply_text(
                f"📢 **ANNOUNCEMENT**\n\n{original_message}\n\n"
                f"👥 Mentioning {len(members)} members...",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Mention in batches
            batch_size = 5
            delay_between_batches = 5
            successful_mentions = 0
            
            for i in range(0, len(members), batch_size):
                batch = members[i:i + batch_size]
                mention_text = " ".join(batch)
                
                try:
                    # Send batch
                    await message.reply_text(
                        mention_text,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                    
                    successful_mentions += len(batch)
                    
                    # Wait between batches
                    if i + batch_size < len(members):
                        await asyncio.sleep(delay_between_batches)
                        
                except RetryAfter as e:
                    # Rate limited
                    wait_time = e.retry_after
                    await asyncio.sleep(wait_time)
                    # Retry same batch
                    i -= batch_size
                    continue
                    
                except Exception as e:
                    logger.error(f"Error sending batch: {e}")
                    continue
            
            # Send completion message
            completion_text = f"""
✅ **MENTION COMPLETED!**

📊 **Statistics:**
• Total members mentioned: {successful_mentions}

📢 **Message sent:**
{original_message}
            """
            
            await message.reply_text(completion_text, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            
            error_message = f"""
❌ **ERROR OCCURRED**

**Error:** `{str(e)[:100]}`

**Possible solutions:**
1. Check if bot is still admin
2. Wait 5 minutes and try again
3. Try in smaller group first
            """
            
            try:
                await message.reply_text(error_message, parse_mode=ParseMode.MARKDOWN)
            except:
                pass
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Global error handler"""
        logger.error(f"Error: {context.error}", exc_info=True)
        
        # Try to notify user
        try:
            if update and hasattr(update, 'effective_message'):
                error_msg = "⚠️ An error occurred. Please try again."
                await update.effective_message.reply_text(error_msg)
        except:
            pass
    
    def run(self):
        """Start the bot"""
        logger.info("🚀 Starting Mass Mention Bot...")
        logger.info("✅ Bot is ready")
        
        # Start polling
        self.application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )

def main():
    """Entry point"""
    # Security check - REPLACE WITH YOUR TOKEN
    ACTUAL_TOKEN = "8562585775:AAFOzbtE2xsqedrx-hj1LXfhmLvvnSetgxQ"
    
    if ACTUAL_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("❌ ERROR: Please replace ACTUAL_TOKEN with your bot token!")
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
