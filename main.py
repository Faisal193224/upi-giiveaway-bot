from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Put your bot token here
TOKEN = "7114393656:AAEhqBLjEHCC5M0DYuWCkxpM88OvroF4xQo"

def send_upi_reward(user_id):
    print(f"🏱 UPI reward triggered for user: {user_id}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/+ZQ17atTJSuxiNTM1")],
        [InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/+BFH8eUFyJsUxNmVl")],
        [InlineKeyboardButton("📢 Join Channel 3", url="https://t.me/+HnDCtAsIDSk1ZDU1")],
        [InlineKeyboardButton("✅ I Have Joined", callback_data="verify")]
    ]
    await update.message.reply_text(
        "🎉 *Welcome to the UPI Giveaway!*\n\nJoin all channels and tap ✅ to claim your reward.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    send_upi_reward(query.from_user.id)
    await query.edit_message_text("✅ Verified! Reward is being processed — stay tuned!")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify, pattern="^verify$"))
    print("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
