import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = "8562585775:AAFOzbtE2xsqedrx-hj1LXfhmLvvnSetgxQ"

async def start(update, context):
    await update.message.reply_text("🤖 Mention Bot\nUse /qwer in groups")

async def qwer(update, context):
    chat = update.effective_chat
    
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("❌ Groups only!")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /qwer your message")
        return
    
    msg = ' '.join(context.args)
    mentions = [f"@user{i}" for i in range(1, 31)]
    
    for i in range(0, len(mentions), 5):
        batch = mentions[i:i+5]
        await update.message.reply_text(f"{msg}\n\n{' '.join(batch)}")
        if i+5 < len(mentions):
            await asyncio.sleep(5)
    
    await update.message.reply_text("✅ Done!")

async def test(update, context):
    await update.message.reply_text("✅ Bot working!")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("qwer", qwer))
    app.add_handler(CommandHandler("mention", qwer))
    app.add_handler(CommandHandler("test", test))
    print("Bot starting...")
    app.run_polling()

if __name__ == '__main__':
    main()
