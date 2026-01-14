import asyncio
import logging
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode
import re

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token from @BotFather
BOT_TOKEN = "8562585775:AAFOzbtE2xsqedrx-hj1LXfhmLvvnSetgxQ"

# Command to trigger mentions
TRIGGER_COMMAND = "/qwer"

async def mention_all_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the mention command"""
    
    # Check if the message is from a group
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("This command only works in groups!")
        return
    
    # Check if command format is correct
    if len(context.args) < 1:
        await update.message.reply_text(f"Usage: {TRIGGER_COMMAND} [your message]")
        return
    
    # Get the original message (excluding the command)
    original_message = ' '.join(context.args)
    
    # Get all chat members
    try:
        chat_id = update.effective_chat.id
        members = []
        
        # Get all members (administrators might need to be fetched separately)
        async for member in context.bot.get_chat_members(chat_id):
            # Skip bots and users without usernames if needed
            if member.user.is_bot:
                continue
                
            # Get user mention
            if member.user.username:
                mention = f"@{member.user.username}"
            else:
                # Fallback to user ID if no username
                mention = f"[{member.user.first_name}](tg://user?id={member.user.id})"
            
            members.append(mention)
        
        if not members:
            await update.message.reply_text("No members found to mention!")
            return
        
        # Send the original message first
        await update.message.reply_text(f"**{original_message}**", parse_mode=ParseMode.MARKDOWN)
        
        # Mention members in batches (to avoid rate limits and message length issues)
        batch_size = 5  # Adjust based on Telegram limits
        delay_between_batches = 5  # seconds
        
        for i in range(0, len(members), batch_size):
            batch = members[i:i + batch_size]
            mention_text = " ".join(batch)
            
            # Send mention batch
            await update.message.reply_text(mention_text, parse_mode=ParseMode.MARKDOWN)
            
            # Wait before sending next batch (except for the last batch)
            if i + batch_size < len(members):
                await asyncio.sleep(delay_between_batches)
    
    except Exception as e:
        logger.error(f"Error mentioning members: {e}")
        await update.message.reply_text("An error occurred while mentioning members.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "🤖 Mention Bot is active!\n\n"
        f"Use {TRIGGER_COMMAND} [message] to mention all group members.\n"
        "Example: /qwer Hello everyone!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        f"**Bot Commands:**\n\n"
        f"{TRIGGER_COMMAND} [message] - Mention all members with your message\n"
        f"/start - Start the bot\n"
        f"/help - Show this help message\n\n"
        f"**Example:**\n"
        f"{TRIGGER_COMMAND} Join my group @example\n\n"
        f"⚠️ Note: The bot needs to be admin to fetch all members.",
        parse_mode=ParseMode.MARKDOWN
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates."""
    logger.warning(f'Update {update} caused error {context.error}')

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("qwer", mention_all_members))

    # Register error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    print("🤖 Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
