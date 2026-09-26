import logging
import threading
import time
import requests
from flask import Flask
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# --- FLASK WEB SERVER FOR RENDER ---
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is active and running!"

def run_flask():
    app_flask.run(host="0.0.0.0", port=10000)

# --- CONFIGURATION ---
BOT_TOKEN = "8588533313:AAFtCfJaLI19ilw30jmztiDQz6Uq7Sc0dcM"
ADMIN_ID = 8313247547
UPI_ID = "7276052050@fam"
AMOUNT = 60
FILE_LINK = "https://t.me/+P6Uhtt1OuEIxZWU1"

RENDER_APP_URL = "https://capcut-tele-bot.onrender.com"

# Temporary memory to store user steps
USER_DATA = {}

def keep_alive():
    while True:
        time.sleep(120)
        try:
            requests.get(RENDER_APP_URL)
        except Exception:
            pass

QR_CODE_URL = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={UPI_ID}%26pn=Merchant%26am={AMOUNT}%26cu=INR"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# --- COMMAND HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USER_DATA[user.id] = {"step": "WAITING_PHOTO"}
    
    msg = (
        f"Aapka swagat hai, {user.first_name}!\n\n"
        f"CapCut Pro (Lifetime With Updates) Lene ke liye aapko **₹{AMOUNT}** ka payment karna hoga.\n"
        f"📌 **UPI ID:** `{UPI_ID}`\n\n"
        f"Upar diye gaye QR Code ko scan karke payment karein. **Kripya exact ₹{AMOUNT} hi bhejein.**\n\n"
        f"Payment karne ke baad, Payment ka **Screenshot** yahan bhejein.\n\n"
        f"👑 Owner - Aditya Services (@asoffcial) 👑"
    )
    
    await update.message.reply_photo(
        photo=QR_CODE_URL,
        caption=msg,
        parse_mode="Markdown"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in USER_DATA and USER_DATA[user.id].get("step") == "WAITING_PHOTO":
        photo_id = update.message.photo[-1].file_id
        USER_DATA[user.id]["photo_id"] = photo_id
        USER_DATA[user.id]["step"] = "WAITING_UTR"
        
        await update.message.reply_text(
            "Screenshot mil gaya hai! Ab kripya apna **12-digit UTR / Transaction No** yahan type karke bhejein:"
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    
    if user.id in USER_DATA and USER_DATA[user.id].get("step") == "WAITING_UTR":
        photo_id = USER_DATA[user.id].get("photo_id")
        
        # User Confirmation Message
        await update.message.reply_text(
            "Wait Until Your Payment Is Verified , You Will Receive Your File Whithin 1 Hour"
        )
        
        # Admin Notification with Tap Commands
        admin_caption = (
            f"🔔 **Naya Payment Verification Request!**\n\n"
            f"👤 **User:** {user.first_name} (@{user.username})\n"
            f"🆔 **User ID:** `{user.id}`\n"
            f"💳 **Amount:** ₹{AMOUNT}\n"
            f"🔢 **UTR Number:** `{text}`\n\n"
            f"⚡ **Tap to Take Action:**\n"
            f"✅ Approve: /approve_{user.id}\n"
            f"❌ Reject: /reject_{user.id}"
        )

        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_id,
            caption=admin_caption,
            parse_mode="Markdown"
        )
        
        USER_DATA.pop(user.id, None)

# --- ONE-TAP APPROVE / REJECT COMMANDS ---
async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    command_text = update.message.text
    target_id = int(command_text.split("_")[1])

    try:
        # Send Link to Customer
        await context.bot.send_message(
            chat_id=target_id,
            text=f"✅ Aapka payment successfully verify ho gaya hai!\n\n📁 **Aapki File ka Channel Link:**\n{FILE_LINK}"
        )
        await update.message.reply_text(f"✅ User (`{target_id}`) ko file link bhej diya gaya hai!", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error sending message to user: `{e}`", parse_mode="Markdown")

async def reject_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    command_text = update.message.text
    target_id = int(command_text.split("_")[1])

    try:
        # Send Reject Message to Customer
        await context.bot.send_message(
            chat_id=target_id,
            text="❌ Aapka payment verify nahi ho paya. Kripya sahi UTR aur Screenshot ke sath dobara koshish karein."
        )
        await update.message.reply_text(f"❌ User (`{target_id}`) ka request reject kar diya gaya hai.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: `{e}`", parse_mode="Markdown")

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex(r"^/approve_\d+"), approve_command))
    app.add_handler(MessageHandler(filters.Regex(r"^/reject_\d+"), reject_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot is active with Tap-Commands...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
