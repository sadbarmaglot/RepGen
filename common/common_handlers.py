from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Начать заполнение", callback_data="start_filling")]
    ])
    message = update.message or update.callback_query.message
    await message.reply_text("Нажмите кнопку ниже, чтобы начать:", reply_markup=keyboard)
