import logging

from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext

from common.whitelist_utils import save_whitelist
from settings import DefectStates, ADMIN_IDS


class BotHandlers:
    """
    Handler class for Telegram bot commands and callback queries.

    Main responsibilities:
    - Manage user access (whitelist, admins)
    - Implement command and callback button logic
    - Generate keyboards for user interaction
    - Work with FSM states
    """
    def __init__(self, whitelist: dict, admin_ids: list = ADMIN_IDS):
        """
        Initialize BotHandlers.

        :param whitelist: dictionary of users with access
        :param admin_ids: list of admin user ids
        """
        self.whitelist = whitelist
        self.admin_ids = admin_ids


    def _is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids

    def _is_whitelisted(self, user_id: int) -> bool:
        return user_id in self.whitelist or self._is_admin(user_id)

    def _add_to_whitelist(self, user_id: int, full_name: str, username: str) -> None:
        self.whitelist[user_id] = {"full_name": full_name, "username": username}
        save_whitelist(self.whitelist)

    def _get_start_keyboard(self, is_admin: bool) -> InlineKeyboardMarkup:
        buttons = [[InlineKeyboardButton(text="📸 Загрузить дефекты", callback_data="start_defects")]]
        if is_admin:
            buttons.append([InlineKeyboardButton(text="👥 Список пользователей", callback_data="list_users")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    def _get_request_access_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔓 Запросить доступ", callback_data="request_access")]
        ])

    def _get_approve_deny_keyboard(self, user_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve:{user_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"deny:{user_id}")
            ]
        ])

    async def start_cmd(self, message: Message, state: FSMContext):
        """
        Handler for the /start command. Shows a greeting and start buttons.
        :param message: Telegram Message object
        :param state: FSMContext
        """
        user_id = message.from_user.id

        if not self._is_whitelisted(user_id):
            await message.answer(
                "👋 Добро пожаловать!\nЧтобы начать использовать бота, запросите доступ:",
                reply_markup=self._get_request_access_keyboard()
            )
            return

        await message.answer(
            "Нажмите кнопку ниже, чтобы начать фиксацию дефектов:",
            reply_markup=self._get_start_keyboard(self._is_admin(user_id))
        )

    async def request_access_callback(self, callback: CallbackQuery):
        """
        Handler for the access request callback.
        Sends a notification to admins with an approve/deny keyboard.
        :param callback: CallbackQuery object
        """
        full_name = callback.from_user.full_name
        user_id = callback.from_user.id
        username = f"@{callback.from_user.username}" if callback.from_user.username else "—"

        text = (
            "📥 <b>Новый запрос на доступ</b>\n\n"
            f"👤 <b>Имя:</b> {full_name}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            f"🔗 <b>Username:</b> {username}\n"
        )

        buttons = self._get_approve_deny_keyboard(user_id)

        for admin_id in self.admin_ids:
            try:
                await callback.bot.send_message(
                    admin_id,
                    text,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                    reply_markup=buttons
                )
            except Exception as e:
                logging.warning(f"Не удалось уведомить админа: {e}")

        await callback.answer()
        await callback.message.answer("✅ Запрос отправлен администраторам. Ожидайте подтверждения.")

    async def approve_callback(self, callback: CallbackQuery):
        """
        Handler for admin approval of access.
        Adds the user to the whitelist and notifies them.
        :param callback: CallbackQuery object
        """
        if not self._is_admin(callback.from_user.id):
            await callback.answer("⛔ Нет доступа", show_alert=True)
            return

        user_id = int(callback.data.split(":")[1])

        if user_id in self.whitelist:
            await callback.answer("✅ Уже в вайтлисте", show_alert=True)
            return
        try:
            user = await callback.bot.get_chat(user_id)
        except Exception as e:
            logging.warning(f"Не удалось получить профиль пользователя {user_id}: {e}")
            await callback.answer("⚠️ Не удалось добавить пользователя.")
            return

        self._add_to_whitelist(user_id, user.full_name, user.username)

        try:
            buttons = self._get_start_keyboard(False)
            await callback.bot.send_message(
                user_id,
                "✅ Вам открыт доступ к функционалу бота.\nНажмите кнопку ниже, чтобы начать работу:",
                reply_markup=buttons
            )
        except Exception as e:
            logging.warning(f"Не удалось уведомить пользователя: {e}")
        try:
            await callback.message.edit_text(
                callback.message.text + "\n\n✅ Пользователь добавлен в вайтлист.",
                parse_mode="HTML"
            )
        except Exception as e:
            logging.warning(f"Не удалось обновить сообщение: {e}")

    async def deny_callback(self, callback: CallbackQuery):
        """
        Handler for denying an access request.
        :param callback: CallbackQuery object
        """
        if not self._is_admin(callback.from_user.id):
            await callback.answer("⛔ Нет доступа", show_alert=True)
            return

        await callback.answer("❌ Запрос отклонён")

        try:
            await callback.message.edit_text(
                callback.message.text + "\n\n❌ Запрос отклонён.",
                parse_mode="HTML"
            )
        except Exception as e:
            logging.warning(f"Не удалось обновить сообщение: {e}")

    async def list_users_callback(self, callback: CallbackQuery):
        """
        Handler for displaying the list of users with access.
        :param callback: CallbackQuery object
        """
        if not self._is_admin(callback.from_user.id):
            await callback.answer("⛔ Нет доступа", show_alert=True)
            return

        if not self.whitelist:
            await callback.message.answer("📭 Вайтлист пуст.")
            return

        text = "<b>👥 Пользователи с доступом:</b>\n\n"

        for uid, data in self.whitelist.items():
            full_name = data.get("full_name", "—")
            username = f"@{data.get('username')}" if data.get("username") else "—"
            text += (
                f"🆔 <code>{uid}</code>\n"
                f"👤 {full_name}\n"
                f"🔗 {username}\n"
            )

        await callback.message.answer(text.strip(), parse_mode="HTML")

    async def cancel_cmd(self, message: Message, state: FSMContext):
        """
        Handler for the /cancel command. Resets the user's session and FSM state.
        :param message: Telegram Message object
        :param state: FSMContext
        """
        await state.clear()

        user_id = message.from_user.id

        if not self._is_whitelisted(user_id):
            await message.answer(
                "Чтобы начать использовать бота, запросите доступ:",
                reply_markup=self._get_request_access_keyboard()
            )
            return

        await message.answer(
            "❌ Сессия сброшена. Нажмите кнопку ниже, чтобы начать заново:",
            reply_markup=self._get_start_keyboard(self._is_admin(user_id))
        )

    async def start_defects(self, callback: CallbackQuery, state: FSMContext):
        """
        Handler for starting defect upload.
        Switches FSM to upload state and initializes data.
        :param callback: CallbackQuery object
        :param state: FSMContext
        """
        await callback.answer()
        await callback.message.answer("Загрузите фото дефектов (одно или несколько)")
        await state.set_state(DefectStates.uploading)
        await state.update_data(
            defects=[],
            all_photo_ids=[],
            processed_photos=0,
            media_batches={},
            active_albums=set(),
            total_photo_count=0,
            status_msg=None
        ) 