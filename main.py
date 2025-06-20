import os
import ctypes
import sqlite3
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, Updater, CallbackQueryHandler

# Load C++ shared library for UPI validation
lib = ctypes.CDLL('./validate.so')
lib.isValidUPI.argtypes = [ctypes.c_char_p]
lib.isValidUPI.restype = ctypes.c_bool

# Telegram Bot token and admin setup
token = "7114393656:AAEhqBLjEHCC5M0DYuWCkxpM88OvroF4xQo"
admin_chat_id = 6610363281
bot = Bot(token=token)

# Channel usernames to verify subscriptions
CHANNELS = ["@ZQ17atTJSuxiNTM1", "@BFH8eUFyJsUxNmVl", "@HnDCtAsIDSk1ZDU1"]

# Flask app for admin panel
app = Flask(__name__)

@app.route("/reward")
def reward():
    bot.send_message(chat_id=admin_chat_id, text="✅ Reward manually triggered by Admin Panel")
    return "✅ Reward sent"

@app.route("/panel")
def panel():
    return '''
        <h1>Admin Panel</h1>
        <button onclick="fetch('/reward')">Send Reward</button>
    '''

# --- DATABASE SETUP ---
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, upi TEXT, balance INTEGER DEFAULT 0, referred_by INTEGER)''')
conn.commit()

# --- BOT COMMANDS ---
def user_exists(user_id):
    c.execute("SELECT 1 FROM users WHERE id=?", (user_id,))
    return c.fetchone() is not None

def add_user(user_id, upi, referred_by=None):
    if not user_exists(user_id):
        c.execute("INSERT INTO users (id, upi, balance, referred_by) VALUES (?, ?, ?, ?)", (user_id, upi, 5, referred_by))
        if referred_by and user_exists(referred_by):
            c.execute("UPDATE users SET balance = balance + 2 WHERE id=?", (referred_by,))
        conn.commit()

def get_balance(user_id):
    c.execute("SELECT balance FROM users WHERE id=?", (user_id,))
    res = c.fetchone()
    return res[0] if res else 0

def update_balance(user_id, amount):
    c.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, user_id))
    conn.commit()

def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    args = context.args
    referred_by = int(args[0]) if args and args[0].isdigit() else None

    # Check if user joined all channels
    for ch in CHANNELS:
        try:
            status = bot.get_chat_member(chat_id=ch, user_id=user_id).status
            if status not in ['member', 'administrator', 'creator']:
                update.message.reply_text("❌ Please join all required channels:")
                for ch_link in CHANNELS:
                    update.message.reply_text(ch_link)
                return
        except:
            update.message.reply_text(f"⚠️ Could not verify channel: {ch}")
            return

    keyboard = [[InlineKeyboardButton("💳 Enter UPI", callback_data="enter_upi")]]
    update.message.reply_text("✅ Joined All! Tap below to proceed.", reply_markup=InlineKeyboardMarkup(keyboard))

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    if query.data == "enter_upi":
        context.bot.send_message(chat_id=user_id, text="💡 Send your UPI ID now:")

def text_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    upi = update.message.text.strip()
    args = context.args
    referred_by = int(args[0]) if args and args[0].isdigit() else None

    if lib.isValidUPI(upi.encode()):
        if not user_exists(user_id):
            add_user(user_id, upi, referred_by)
            update.message.reply_text(f"✅ UPI {upi} saved. You've earned ₹5! Use /menu to see options.")
        else:
            update.message.reply_text("ℹ️ You’ve already submitted your UPI.")
    else:
        update.message.reply_text("❌ Invalid UPI format.")

def menu(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("💰 Balance", callback_data="balance"),
         InlineKeyboardButton("🤝 Refer", callback_data="refer")],
        [InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")]
    ]
    update.message.reply_text("📋 Your Menu:", reply_markup=InlineKeyboardMarkup(keyboard))

def menu_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    if query.data == "balance":
        balance = get_balance(user_id)
        query.edit_message_text(f"💰 Your Balance: ₹{balance}")
    elif query.data == "refer":
        link = f"https://t.me/{context.bot.username}?start={user_id}"
        query.edit_message_text(f"🔗 Share your referral link:\n{link}")
    elif query.data == "withdraw":
        balance = get_balance(user_id)
        if balance >= 10:
            update_balance(user_id, -10)
            context.bot.send_message(chat_id=admin_chat_id, text=f"🤑 Withdraw requested by {user_id}. Send to saved UPI.")
            query.edit_message_text("✅ Withdraw request sent to admin.")
        else:
            query.edit_message_text("❌ Minimum ₹10 needed to withdraw.")

# --- BOT SETUP ---
updater = Updater(token, use_context=True)
dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("menu", menu))
dp.add_handler(CallbackQueryHandler(button_handler, pattern="enter_upi"))
dp.add_handler(CallbackQueryHandler(menu_buttons, pattern="^(balance|refer|withdraw)$"))
dp.add_handler(CommandHandler("help", menu))
dp.add_handler(CommandHandler("refer", menu))
dp.add_handler(CommandHandler("withdraw", menu))
dp.add_handler(CommandHandler("balance", menu))
dp.add_handler(CommandHandler("upi", text_handler))
dp.add_handler(CommandHandler("reward", lambda update, context: context.bot.send_message(chat_id=update.effective_chat.id, text="🚀 Viral reward sent!")))

# --- START EVERYTHING ---
if __name__ == '__main__':
    updater.start_polling()
    app.run(host='0.0.0.0', port=3000)
                      
