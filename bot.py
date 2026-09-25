    import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# --- FLASK WEB SERVER (Render Free Tier Ke Liye) ---
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is running live on Render Free Tier!"

def run_flask():
    app_flask.run(host="0.0.0.0", port=10000)

# --- BOT CONFIGURATION ---
BOT_TOKEN = "8588533313:AAFtCfJaLI19ilw30jmztiDQz6Uq7Sc0dcM"
ADMIN_ID = 8313247547
UPI_ID = "7276052050@fam"
AMOUNT = 60
FILE_LINK = "https://t.me/+P6Uhtt1OuEIxZWU1"

QR_CODE_URL = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={UPI_ID}%26pn=Merchant%26am={AMOUNT}%26cu=INR"

WAITING_FOR_SCREENSHOT = 1
WAITING_FOR_UTR = 2

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
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
    return WAITING_FOR_SCREENSHOT

async def receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file_id = update.message.photo[-1].file_id
    context.user_data["photo_id"] = photo_file_id
    
    await update.message.reply_text(
        "Screenshot mil gaya hai! Ab kripya apna **12-digit UTR / Transaction No** yahan type karke bhejein:"
    )
    return WAITING_FOR_UTR

async def receive_utr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    utr_text = update.message.text
    context.user_data["utr"] = utr_text
    user = update.effective_user

    await update.message.reply_text(
        "Wait Until Your Payment Is Verified , You Will Receive Your File Whithin 1 Hour"
    )

    keyboard = [
        [
            InlineKeyboardButton("Verify & Send File", callback_data=f"verify_{user.id}"),
            InlineKeyboardButton("Reject", callback_data=f"reject_{user.id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    admin_caption = (
        f"🔔 **Naya Payment Verification Request!**\n\n"
        f"👤 **User:** {user.first_name} (@{user.username})\n"
        f"🆔 **User ID:** `{user.id}`\n"
        f"💳 **Amount:** ₹{AMOUNT}\n"
        f"🔢 **UTR Number:** `{utr_text}`"
    )

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=context.user_data["photo_id"],
        caption=admin_caption,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    return ConversationHandler.END

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    action = data[0]
    target_user_id = int(data[1])

    if action == "verify":
        await query.edit_message_caption(caption=f"{query.message.caption}\n\n✅ **Verified & Link Sent!**")
        
        await context.bot.send_message(
            chat_id=target_user_id, 
            text=f"✅ Aapka payment successfully verify ho gaya hai!\n\n📁 **Aapki File ka Channel Link:** {FILE_LINK}"
        )

    elif action == "reject":
        await query.edit_message_caption(caption=f"{query.message.caption}\n\n❌ **Rejected!**")
        await context.bot.send_message(
            chat_id=target_user_id, 
            text="❌ Aapka payment verify nahi ho paya. Kripya sahi UTR aur Screenshot ke sath dobara koshish karein."
        )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Process cancel ho gaya hai.")
    return ConversationHandler.END

def main():
    # Start Flask server in background thread
    threading.Thread(target=run_flask, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FOR_SCREENSHOT: [MessageHandler(filters.PHOTO, receive_screenshot)],
            WAITING_FOR_UTR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_utr)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_click))

    print("Bot start ho gaya hai...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
