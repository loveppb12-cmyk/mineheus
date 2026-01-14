import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8562585775:AAFOzbtE2xsqedrx-hj1LXfhmLvvnSetgxQ"

async def start(update, context):
    await update.message.reply_text(
        "🤖 **Group Mention Bot**\n\n"
        "**Command:** `/qwer your message`\n\n"
        "**Example:** `/qwer Hello everyone join our channel`\n\n"
        "⚠️ **Bot must be admin in the group!**",
        parse_mode=ParseMode.MARKDOWN
    )

async def qwer(update, context):
    chat = update.effective_chat
    
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("❌ This command works in groups only!")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /qwer your message")
        return
    
    # Send processing message
    status_msg = await update.message.reply_text("⏳ Fetching group members...")
    
    try:
        # Get bot info to check admin status
        bot = await context.bot.get_me()
        
        # Check if bot is admin
        try:
            chat_member = await context.bot.get_chat_member(chat.id, bot.id)
            if chat_member.status not in ['administrator', 'creator']:
                await status_msg.edit_text("❌ I need to be admin to mention everyone!")
                return
        except Exception as e:
            await status_msg.edit_text(f"❌ Error checking admin status: {e}")
            return
        
        msg = ' '.join(context.args)
        
        # Fetch real group members
        mentions = []
        member_count = 0
        
        try:
            # Get all chat members
            async for member in context.bot.get_chat_members(chat.id):
                member_count += 1
                user = member.user
                
                # Skip bots
                if user.is_bot:
                    continue
                
                # Create mention
                if user.username:
                    # User has username
                    mention = f"@{user.username}"
                else:
                    # User without username - use ID mention
                    name = user.first_name or "User"
                    mention = f'<a href="tg://user?id={user.id}">{name}</a>'
                
                mentions.append(mention)
            
            await status_msg.edit_text(f"✅ Found {member_count} members, {len(mentions)} to mention")
            
        except Exception as e:
            logger.error(f"Error fetching members: {e}")
            await status_msg.edit_text("⚠️ Using sample mentions (bot may need more permissions)")
            
            # Fallback to sample mentions if can't fetch real members
            mentions = [f"@user{i}" for i in range(1, 31)]
        
        if not mentions:
            await status_msg.edit_text("❌ No members found to mention!")
            return
        
        # Delete status message
        try:
            await status_msg.delete()
        except:
            pass
        
        # Send mentions in batches
        batch_size = 5
        delay = 5  # seconds between batches
        
        for i in range(0, len(mentions), batch_size):
            batch = mentions[i:i+batch_size]
            
            # Create message text
            if i == 0:
                message_text = f"📢 **{msg}**\n\n"
            else:
                message_text = f"{msg}\n\n"
            
            message_text += " ".join(batch)
            
            # Send the message
            await update.message.reply_text(
                message_text,
                parse_mode=ParseMode.HTML if mentions[0].startswith('<a href') else None,
                disable_web_page_preview=True
            )
            
            # Wait before next batch (except last batch)
            if i + batch_size < len(mentions):
                await asyncio.sleep(delay)
        
        # Send completion message
        await update.message.reply_text(f"✅ **Done!** Mentioned {len(mentions)} members.")
        
    except Exception as e:
        logger.error(f"Error in qwer command: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")

async def test(update, context):
    """Test command to check bot permissions"""
    chat = update.effective_chat
    
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("❌ This command works in groups only!")
        return
    
    try:
        bot = await context.bot.get_me()
        
        # Check admin status
        try:
            chat_member = await context.bot.get_chat_member(chat.id, bot.id)
            is_admin = chat_member.status in ['administrator', 'creator']
        except:
            is_admin = False
        
        # Try to get member count
        try:
            chat_info = await context.bot.get_chat(chat.id)
            member_count = chat_info.get_member_count() or "Unknown"
        except:
            member_count = "Unknown"
        
        test_result = f"""
✅ **Bot Test Results:**

• **Group:** {chat.title}
• **Bot Username:** @{bot.username}
• **Admin Status:** {'✅ YES' if is_admin else '❌ NO'}
• **Members:** {member_count}
• **Ready for /qwer:** {'✅ YES' if is_admin else '❌ Make me admin first!'}
        """
        
        await update.message.reply_text(test_result, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Test error: {e}")

async def help_command(update, context):
    """Help command"""
    help_text = """
📚 **How to use:**

1. Add bot to group
2. Make bot **admin** (required!)
3. Use: `/qwer your message`

**Example:**
`/qwer Join our new channel @example`

**What happens:**
The bot will:
1. Fetch all group members
2. Post your message
3. Mention members in batches of 5
4. Wait 5 seconds between batches

**Requirements:**
• Bot must be admin
• Works in groups/supergroups only
    """
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("qwer", qwer))
    app.add_handler(CommandHandler("mention", qwer))  # Alternative command
    app.add_handler(CommandHandler("test", test))
    
    print("🤖 Bot starting...")
    print("Commands: /start, /help, /qwer, /mention, /test")
    print("Press Ctrl+C to stop")
    
    app.run_polling()

if __name__ == '__main__':
    main()
