import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from common.whitelist_utils import load_whitelist
from core.handlers import BotHandlers
from core.photo_manager import PhotoManager
from settings import DefectStates, BOT_TOKEN

handlers = BotHandlers(
    whitelist=load_whitelist(),
)

photo_manager = PhotoManager()

async def cancel_cmd(message: Message, state: FSMContext):
    photo_manager.cancel_chat_tasks(message.chat.id)
    await handlers.cancel_cmd(message, state)

async def start_defects(callback: CallbackQuery, state: FSMContext):
    photo_manager.cancel_chat_tasks(callback.message.chat.id)
    await handlers.start_defects(callback, state)

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.message.register(handlers.start_cmd, CommandStart())
    dp.message.register(handlers.cancel_cmd, Command("cancel"))
    dp.message.register(photo_manager.handle_photo, F.photo, StateFilter(DefectStates.uploading))
    dp.callback_query.register(handlers.list_users_callback, F.data == "list_users")
    dp.callback_query.register(handlers.request_access_callback, F.data == "request_access")
    dp.callback_query.register(handlers.approve_callback, F.data.startswith("approve:"))
    dp.callback_query.register(handlers.deny_callback, F.data.startswith("deny:"))
    dp.callback_query.register(start_defects, F.data == "start_defects")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())