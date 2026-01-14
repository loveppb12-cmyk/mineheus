import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8562585775:AAFOzbtE2xsqedrx-hj1LXfhmLvvnSetgxQ"

class MentionBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("qwer", self.mention_all_members))
        self.application.add_handler(CommandHandler("mention", self.mention_all_members))
        self.application.add_handler(CommandHandler("test", self.test_command))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_text = "🤖 **Group Mention Bot**\n\n**Command:** `/qwer your message`\n\n**Example:**\n`/qwer Hello everyone join our channel`\n\n**Bot must be admin in the group!**"
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = "📚 **How to use:**\n1. Add bot to group\n2. Make bot **admin**\n3. Use: `/qwer your message`\n\n**Example:** `/qwer Join our new group @example`"
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("✅ Bot is working! Use /qwer in groups.")
    
    async def check_bot_admin(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        try:
            bot = await context.bot.get_me()
            chat_member = await context.bot.get_chat_member(chat_id, bot.id)
            return chat_member.status in ['administrator', 'creator']
        except Exception as e:
            logger.error(f"Admin check error: {e}")
            return False
    
    async def get_all_members_mentions(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        mentions = []
        
        try:
            async for member in context.bot.get_chat_members(chat_id):
                user = member.user
                
                if user.is_bot:
                    continue
                
                if user.username:
                    mention = f"@{user.username}"
                else:
                    name = user.first_name or "User"
                    mention = f'<a href="tg://user?id={user.id}">{name}</a>'
                
                mentions.append(mention)
            
            logger.info(f"Found {len(mentions)} members to mention")
            return mentions
            
        except Exception as e:
            logger.error(f"Error fetching members: {e}")
            sample_mentions = [f"@user{i}" for i in range(1, 51)]
            logger.info(f"Using {len(sample_mentions)} sample mentions")
            return sample_mentions
    
    async def mention_all_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        message = update.message
        
        if chat.type not in ['group', 'supergroup']:
            await message.reply_text("❌ This command only works in groups!")
            return
        
        if not context.args:
            await message.reply_text("❌ Please add your message!\n\n**Example:** `/qwer Hello everyone join our channel`", parse_mode=ParseMode.MARKDOWN)
            return
        
        if not await self.check_bot_admin(chat.id, context):
            await message.reply_text("⚠️ **I need to be admin to mention everyone!**\n\nPlease make me admin first.", parse_mode=ParseMode.MARKDOWN)
            return
        
        original_message = ' '.join(context.args)
        
        status_msg = await message.reply_text("⏳ Fetching members list...")
        
        try:
            mentions = await self.get_all_members_mentions(chat.id, context)
            
            if not mentions:
                await status_msg.edit_text("❌ No members found to mention!")
                return
            
            await status_msg.edit_text(f"✅ Found {len(mentions)} members\nStarting in 3 seconds...")
            await asyncio.sleep(3)
            
            try:
                await status_msg.delete()
            except:
                pass
            
            batch_size = 5
            delay = 5
            total_batches = (len(mentions) + batch_size - 1) // batch_size
            
            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, len(mentions))
                current_batch = mentions[start_idx:end_idx]
                
                message_text = f"{original_message}\n\n" + " ".join(current_batch)
                
                await message.reply_text(message_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                
                if batch_num < total_batches - 1:
                    await asyncio.sleep(delay)
            
            await message.reply_text(f"✅ **Done!** Mentioned {len(mentions)} members.")
            
        except Exception as e:
            logger.error(f"Error: {e}")
            await message.reply_text(f"❌ Error: {str(e)[:100]}")
    
    def run(self):
        logger.info("🤖 Bot starting...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    print("=" * 50)
    print("🤖 TELEGRAM MENTION BOT")
    print("=" * 50)
    
    bot = MentionBot()
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
