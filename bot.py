import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters, ConversationHandler
)
from styler import render_quote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_QUOTE = 1
WAITING_FOR_STYLE = 2
WAITING_FOR_POSITION = 3
WAITING_FOR_HANDLE = 4

STYLES = {
    "airy": "🌊 Airy & Minimal",
    "minimal": "☁️ Pure Minimal",
    "book": "📖 Book Page",
    "dark": "🌑 Dark Card",
    "warm": "☀️ Warm Editorial",
}

STYLE_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🌊 Airy & Minimal", callback_data="style_airy"),
     InlineKeyboardButton("☁️ Pure Minimal", callback_data="style_minimal")],
    [InlineKeyboardButton("📖 Book Page", callback_data="style_book"),
     InlineKeyboardButton("🌑 Dark Card", callback_data="style_dark")],
    [InlineKeyboardButton("☀️ Warm Editorial", callback_data="style_warm")],
    [InlineKeyboardButton("🎲 Surprise me", callback_data="style_random")],
])

POSITION_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("⬆️ Top", callback_data="pos_top"),
     InlineKeyboardButton("⬛ Center", callback_data="pos_center"),
     InlineKeyboardButton("⬇️ Bottom", callback_data="pos_bottom")],
])

HANDLE_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("No handle", callback_data="handle_none")],
])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hey! Send me a *photo* and I'll help you create an Instagram-ready quote card.\n\n"
        "Or send just a *quote as text* for a template-only design.",
        parse_mode="Markdown"
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User sent a photo — store it, ask for the quote."""
    photo = update.message.photo[-1]  # highest resolution
    context.user_data["photo_file_id"] = photo.file_id
    context.user_data["mode"] = "photo"

    await update.message.reply_text(
        "📸 Got the photo! Now send me the *quote text* you want on it.",
        parse_mode="Markdown"
    )
    return WAITING_FOR_QUOTE


async def handle_text_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User sent text — either quote reply or direct quote."""
    text = update.message.text.strip()

    if context.user_data.get("mode") == "photo":
        # This is the quote for the photo
        context.user_data["quote"] = text
        await update.message.reply_text(
            "✨ Pick a style:",
            reply_markup=STYLE_KEYBOARD
        )
        return WAITING_FOR_STYLE
    else:
        # No photo — template mode
        context.user_data["quote"] = text
        context.user_data["mode"] = "template"
        await update.message.reply_text(
            "📝 Quote saved! Pick a style:",
            reply_markup=STYLE_KEYBOARD
        )
        return WAITING_FOR_STYLE


async def handle_style_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    import random
    style_key = query.data.replace("style_", "")
    if style_key == "random":
        style_key = random.choice(list(STYLES.keys()))

    context.user_data["style"] = style_key

    # Ask for position next (only for photo modes, template styles auto-center)
    if context.user_data.get("mode") == "photo":
        await query.edit_message_text(
            "📍 Where should the quote go?",
            reply_markup=POSITION_KEYBOARD
        )
        return WAITING_FOR_POSITION
    elif style_key == "dark":
        await query.edit_message_text(
            "Want to add your Instagram handle? Type it (e.g. @yourname) or tap below:",
            reply_markup=HANDLE_KEYBOARD
        )
        return WAITING_FOR_HANDLE
    else:
        await query.edit_message_text(f"Generating *{STYLES[style_key]}* style... ⏳", parse_mode="Markdown")
        await _generate_and_send(update, context, query.message.chat_id)
        return ConversationHandler.END


async def handle_position_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    position = query.data.replace("pos_", "")
    context.user_data["position"] = position

    style_key = context.user_data.get("style")

    if style_key == "dark":
        await query.edit_message_text(
            "Want to add your Instagram handle? Type it (e.g. @yourname) or tap below:",
            reply_markup=HANDLE_KEYBOARD
        )
        return WAITING_FOR_HANDLE
    else:
        await query.edit_message_text(f"Generating... ⏳")
        await _generate_and_send(update, context, query.message.chat_id)
        return ConversationHandler.END


async def handle_handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User typed their Instagram handle."""
    if update.message:
        handle = update.message.text.strip()
        context.user_data["handle"] = handle
        chat_id = update.message.chat_id
        await update.message.reply_text("Generating... ⏳")
        await _generate_and_send(update, context, chat_id)
    return ConversationHandler.END


async def handle_no_handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["handle"] = None
    await query.edit_message_text("Generating... ⏳")
    await _generate_and_send(update, context, query.message.chat_id)
    return ConversationHandler.END


async def _generate_and_send(update, context, chat_id):
    bot = context.bot
    style = context.user_data.get("style", "airy")
    quote = context.user_data.get("quote", "")
    mode = context.user_data.get("mode", "template")
    handle = context.user_data.get("handle")
    position = context.user_data.get("position", "center")

    photo_bytes = None
    if mode == "photo":
        file_id = context.user_data.get("photo_file_id")
        photo_file = await bot.get_file(file_id)
        import io
        buf = io.BytesIO()
        await photo_file.download_to_memory(buf)
        buf.seek(0)
        photo_bytes = buf.read()

    try:
        output_path = render_quote(
            quote=quote,
            style=style,
            photo_bytes=photo_bytes,
            handle=handle,
            position=position
        )
        with open(output_path, "rb") as f:
            await bot.send_photo(
                chat_id=chat_id,
                photo=f,
                caption=f"Style: {STYLES[style]} ✨"
            )
        os.remove(output_path)
    except Exception as e:
        logger.error(f"Render error: {e}")
        await bot.send_message(chat_id=chat_id, text=f"❌ Something went wrong: {e}")

    # Clear user data
    context.user_data.clear()


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Cancelled. Send a new photo or quote whenever you're ready!")
    return ConversationHandler.END


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set!")

    app = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.PHOTO, handle_photo),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_quote),
        ],
        states={
            WAITING_FOR_QUOTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_quote)
            ],
            WAITING_FOR_STYLE: [
                CallbackQueryHandler(handle_style_choice, pattern="^style_")
            ],
            WAITING_FOR_POSITION: [
                CallbackQueryHandler(handle_position_choice, pattern="^pos_")
            ],
            WAITING_FOR_HANDLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_handle_input),
                CallbackQueryHandler(handle_no_handle, pattern="^handle_none$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    print("🤖 Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
