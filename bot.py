import logging
import threading
import time
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
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
        
        # Admin Notification Buttons
        keyboard = [
            [
                InlineKeyboardButton("Verify & Send File", callback_data=f"v_{user.id}"),
                InlineKeyboardButton("Reject", callback_data=f"r_{user.id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        admin_caption = (
            f"🔔 **Naya Payment Verification Request!**\n\n"
            f"👤 **User:** {user.first_name} (@{user.username})\n"
            f"🆔 **User ID:** `{user.id}`\n"
            f"💳 **Amount:** ₹{AMOUNT}\n"
            f"🔢 **UTR Number:** `{text}`"
        )

        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_id,
            caption=admin_caption,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
        # Clear step
        USER_DATA.pop(user.id, None)

# --- BUTTON CLICK HANDLER WITH TRY-EXCEPT LOGGING ---
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    action, target_id = data.split("_")
    target_id = int(target_id)

    if action == "v":
        try:
            # Send Link to Customer
            await context.bot.send_message(
                chat_id=target_id,
                text=f"✅ Aapka payment successfully verify ho gaya hai!\n\n📁 **Aapki File ka Channel Link:**\n{FILE_LINK}"
            )
            # Update Admin Message
            await query.edit_message_caption(
                caption=f"{query.message.caption}\n\n✅ **STATUS: Verified & Link Sent!**",
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"Error sending link to user {target_id}: {e}")
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"❌ **Error:** User ({target_id}) ko link nahi bhej paye.\nDetails: `{e}`",
                parse_mode="Markdown"
            )

    elif action == "r":
        try:
            # Send Reject Message to Customer
            await context.bot.send_message(
                chat_id=target_id,
                text="❌ Aapka payment verify nahi ho paya. Kripya sahi UTR aur Screenshot ke sath dobara koshish karein."
            )
            # Update Admin Message
            await query.edit_message_caption(
                caption=f"{query.message.caption}\n\n❌ **STATUS: Rejected!**",
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"Error sending reject status: {e}")

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    # Direct Route Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_click))

    print("Bot is live on Render...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
