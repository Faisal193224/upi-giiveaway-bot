from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3

# --- CONFIGURATION ---
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # 🔁 Replace this
CHANNELS = ["@ZQ17atTJSuxiNTM1", "@BFH8eUFyJsUxNmVl", "@HnDCtAsIDSk1ZDU1"]  # ✅ Use your exact channels
START_REWARD = 5
REFERRAL_REWARD = 2

# --- DATABASE SETUP ---
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, balance INTEGER, referred_by INTEGER)''')
conn.commit()

# --- FUNCTIONS ---
def user_exists(user_id):
    c.execute("SELECT 1 FROM users WHERE id=?", (user_id,))
    return c.fetchone() is not None

def add_user(user_id, referred_by=None):
    if not user_exists(user_id):
        c.execute("INSERT INTO users (id, balance, referred_by) VALUES (?, ?, ?)",
                  (user_id, START_REWARD, referred_by))
        conn.commit()
        if referred_by and user_exists(referred_by):
            c.execute("UPDATE users SET balance = balance + ? WHERE id=?", (REFERRAL_REWARD, referred_by))
            conn.commit()

def get_balance(user_id):
    c.execute("SELECT balance FROM users WHERE id=?", (user_id,))
    result = c.fetchone()
    return result[0] if result else 0

def update_balance(user_id, amount):
    c.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, user_id))
    conn.commit()

# --- START HANDLER ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    referred_by = int(args[0]) if args and args[0].isdigit() else None

    for ch in CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=ch, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                await update.message.reply_text(f"❌ Join all channels first:\n{chr(10).join(CHANNELS)}")
                return
        except:
            await update.message.reply_text(f"⚠️ Error checking channel: {ch}")
            return

    if not user_exists(user_id):
        add_user(user_id, referred_by)

    keyboard = [[InlineKeyboardButton("💰 Balance", callback_data="balance"),
                 InlineKeyboardButton("🤝 Refer", callback_data="refer")],
                [InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")]]
    await update.message.reply_text("✅ Verified! Use buttons below:", reply_markup=InlineKeyboardMarkup(keyboard))

# --- BUTTON HANDLER ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "balance":
        await query.edit_message_text(text=f"💰 Balance: ₹{get_balance(user_id)}")
    elif query.data == "refer":
        link = f"https://t.me/{context.bot.username}?start={user_id}"
        await query.edit_message_text(text=f"🔗 Share your link:\n{link}")
    elif query.data == "withdraw":
        if get_balance(user_id) >= 10:
            update_balance(user_id, -10)
            await query.edit_message_text("✅ ₹10 withdrawn. Will be sent to your UPI.")
        else:
            await query.edit_message_text("❌ You need at least ₹10 to withdraw.")

# --- BOT START ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.run_polling()
