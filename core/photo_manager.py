import os
import uuid
import json
import aiohttp
import asyncio
import logging
import weakref

import concurrent.futures
from typing import Dict, Optional
from aiogram import Bot
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile
)
from openai import OpenAI, RateLimitError
from aiogram.fsm.context import FSMContext

from common.gc_utils import upload_to_gcs
from common.defects_db import SYSTEM_MESSAGE, PROMPT
from docx_generator.generate_defect_report import generate_defect_only_report
from settings import (
    DefectStates,
    COMMON_DELAY_SECONDS,
    RATE_DELAY_SECONDS,
    GPT_MAX_WORKERS,
    GPT_SEM_COUNT,
    MODEL_NAME
)

class PhotoManager:
    """
    Class for managing defect photo processing, interacting with OpenAI, and generating reports.

    Main responsibilities:
    - Asynchronous processing and analysis of photos via OpenAI API
    - Managing tasks for album and single photo processing
    - Generating and sending reports to the user
    - Working with Telegram Bot API and FSM states
    """
    def __init__(self, client: OpenAI = OpenAI()):
        """
        Initialize PhotoManager.

        :param client: OpenAI instance for API interaction (default: new instance)
        """
        self.client = client
        self.album_button_tasks: Dict[int, Dict[str, asyncio.Task]] = {}
        self.status_locks = weakref.WeakValueDictionary()
        self.gpt_semaphore = asyncio.Semaphore(GPT_SEM_COUNT)
        self.openai_executor = concurrent.futures.ThreadPoolExecutor(max_workers=GPT_MAX_WORKERS)
        self.common_delay_sec = COMMON_DELAY_SECONDS
        self.rate_delay_sec = RATE_DELAY_SECONDS
        self.model = MODEL_NAME

    def _add_task(self, chat_id: int, group_id: str, task: asyncio.Task) -> None:
        """
        Add an album processing task for a chat and group.
        If a task already exists and is not finished, it will be cancelled.
        """
        if chat_id not in self.album_button_tasks:
            self.album_button_tasks[chat_id] = {}
        
        existing_task = self.album_button_tasks[chat_id].get(group_id)
        if existing_task and not existing_task.done():
            existing_task.cancel()
        
        self.album_button_tasks[chat_id][group_id] = task

    def _remove_task(self, chat_id: int, group_id: str) -> None:
        """
        Remove an album processing task for a chat and group.
        """
        if chat_id in self.album_button_tasks:
            self.album_button_tasks[chat_id].pop(group_id, None)
            if not self.album_button_tasks[chat_id]:
                self.album_button_tasks.pop(chat_id)

    async def _call_openai_chat_limited(self, **kwargs):
        """
        Asynchronously call OpenAI chat completion with semaphore and thread pool limits.
        """
        async with self.gpt_semaphore:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                self.openai_executor,
                lambda: self.client.chat.completions.create(**kwargs)
            )    

    def cancel_chat_tasks(self, chat_id: int) -> None:
        """
        Cancel all album processing tasks for the specified chat.
        """
        if chat_id in self.album_button_tasks:
            for task in self.album_button_tasks[chat_id].values():
                if not task.done():
                    task.cancel()
            self.album_button_tasks.pop(chat_id)
            
    async def process_photo(self, file_id: str, bot: Bot, max_retries: int = 3) -> Optional[Dict]:
        """
        Download a photo by file_id, upload it to GCS, send it to OpenAI for analysis, and return the result.
        :param file_id: file_id of the photo in Telegram
        :param bot: Telegram Bot instance
        :param max_retries: maximum number of attempts for RateLimit
        :return: dict with defect description or None on error
        """
        uid = str(uuid.uuid4())[:8]
        filename = f"defect_{uid}.jpg"

        file = await bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"

        blob = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as resp:
                    if resp.status != 200:
                        raise Exception(f"Failed to download image: {resp.status}")
                    with open(filename, "wb") as f:
                        f.write(await resp.read())

            blob, image_url = await upload_to_gcs(filename, ".jpg")

            for attempt in range(max_retries):
                try:
                    response = await self._call_openai_chat_limited(
                        model=self.model,
                        messages=[
                            SYSTEM_MESSAGE,
                            {"role": "user", "content": [
                                {"type": "text", "text": PROMPT},
                                {"type": "image_url", "image_url": {"url": image_url}}
                            ]}
                        ],
                        temperature=0.2,
                        max_tokens=1024,
                        response_format={"type": "json_object"}
                    )

                    result = json.loads(response.choices[0].message.content)

                    return {
                        "defect": result["defect_description"],
                        "eliminating_method": result["recommendation"],
                        "image_path": filename
                    }

                except RateLimitError as e:
                    logging.warning(f"[RETRY {attempt + 1}/{max_retries}] RateLimit: — ждём {self.rate_delay_sec}с")
                    await asyncio.sleep(self.rate_delay_sec)
                except Exception as e:
                    logging.exception(f"[GPT ERROR] Ошибка при обработке изображения {file_id}: {e}")
                    return None

            logging.error(f"[GIVE UP] Превышено число попыток ({max_retries}) для {file_id}")
            return None

        finally:
            if blob:
                try:
                    blob.delete()
                except Exception as e:
                    logging.warning(f"[WARNING] Не удалось удалить blob: {e}")

    async def worker(self, file_id, bot, state, failed_files):
        """
        Process a single photo: calls process_photo, updates state, reports progress.
        :param file_id: file_id of the photo
        :param bot: Telegram Bot instance
        :param state: FSMContext
        :param failed_files: list of failed file_ids
        :return: result of process_photo or None
        """
        try:
            result = await self.process_photo(file_id, bot)
        except asyncio.CancelledError:
            logging.warning(f"[CANCELLED] Обработка фото {file_id} была отменена")
            result = None
        except Exception as e:
            logging.exception(f"[GPT ERROR] Ошибка при обработке фото {file_id}: {e}")
            result = None

        if result is None:
            failed_files.append(file_id)

        current_data = await state.get_data()
        new_processed = current_data.get("processed_photos", 0) + 1
        await state.update_data(processed_photos=new_processed)

        current_status_msg = current_data.get("status_msg")
        total_count = current_data.get("total_photo_count", 0)

        try:
            await bot.edit_message_text(
                chat_id=current_status_msg[0],
                message_id=current_status_msg[1],
                text=f"🔍 Обработка фото: {new_processed}/{total_count}"
            )
        except Exception:
            pass

        return result

    async def auto_process_album(self, message: Message, group_id: str, state: FSMContext):
        """
        Automatically process a photo album (media group):
        - collects file_ids, calls worker for each photo
        - updates progress, generates report upon completion
        :param message: Telegram Message object
        :param group_id: album identifier
        :param state: FSMContext
        """
        bot = message.bot
        chat_id = message.chat.id

        try:
            await asyncio.sleep(self.common_delay_sec)

            data = await state.get_data()

            media_batches = data.get("media_batches", {})
            photo_ids = media_batches.pop(group_id, [])
            if not photo_ids:
                return

            await state.update_data(media_batches=media_batches)

            lock = self.status_locks.setdefault(chat_id, asyncio.Lock())
            
            async with lock:
                data = await state.get_data()
                active_albums = set(data.get("active_albums", set()))
                active_albums.add(group_id)
                await state.update_data(active_albums=list(active_albums))

                total_photo_count = data.get("total_photo_count", 0)
                if not data.get("status_msg"):
                    msg = await message.answer(f"🔍 Обработка фото: 0/{total_photo_count}")
                    await state.update_data(status_msg=(msg.chat.id, msg.message_id))

            failed_files = []

            tasks = [self.worker(fid, bot, state, failed_files) for fid in photo_ids]
            raw_results = await asyncio.gather(*tasks, return_exceptions=True)
            new_defects = [r for r in raw_results if isinstance(r, dict)]

            if new_defects:
                defects = data.get("defects", [])
                defects.extend(new_defects)
                await state.update_data(defects=defects)
            
            async with lock:
                data = await state.get_data()
                active_albums = set(data.get("active_albums", set()))
                active_albums.discard(group_id)
                await state.update_data(active_albums=list(active_albums))

                defects = data.get("defects", [])
                total_photo_count = data.get("total_photo_count", 0)
                albums_done = not active_albums

                if albums_done:
                    await self.generate_and_send_report(message, state)

                await state.update_data(status_msg=None)

            if failed_files:
                await message.answer(
                    f"⚠️ {len(failed_files)} фото не удалось обработать. "
                    f"Это могло произойти из-за перегрузки сервера OpenAI или ошибок в изображении. "
                    f"Попробуйте отправить их повторно позже."
                )
        except asyncio.CancelledError:
            pass
        finally:
            self._remove_task(chat_id, group_id)
    
    async def handle_photo(self, message: Message, state: FSMContext):
        """
        Photo handler: determines if it's a single photo or album, starts processing, and updates state.
        :param message: Telegram Message object
        :param state: FSMContext
        """
        data = await state.get_data()
        chat_id = message.chat.id
        group_id = message.media_group_id
        file_id = message.photo[-1].file_id

        if group_id:
            media_batches = dict(data.get("media_batches", {}))
            media_batches.setdefault(group_id, []).append(file_id)

            all_photo_ids = list(data.get("all_photo_ids", []))
            all_photo_ids.append(file_id)

            total_photo_count = len(all_photo_ids)

            await state.update_data(
                media_batches=media_batches,
                all_photo_ids=all_photo_ids,
                total_photo_count=total_photo_count
            )

            task = asyncio.create_task(self.auto_process_album(message, group_id, state))
            self._add_task(chat_id=chat_id, group_id=group_id, task=task)
        else:
            await message.answer("🔍 Анализирую фото...")

            defect = await self.process_photo(file_id, message.bot)
            if defect:
                defects = data.get("defects", [])
                defects.append(defect)
                await state.update_data(defects=defects)
            else:
                await message.answer("❌ Не удалось проанализировать изображение.")

            active_albums = set(data.get("active_albums", set()))
            all_photo_ids = data.get("all_photo_ids", [])
            if not active_albums and not all_photo_ids:
                await self.generate_and_send_report(message, state)

            await state.set_state(DefectStates.uploading)

    @staticmethod
    async def generate_and_send_report(message: Message, state: FSMContext):
        """
        Generate and send a defect report to the user, clear state, and delete temporary files.
        :param message: Telegram Message object
        :param state: FSMContext
        """
        data = await state.get_data()
        defects = data.get("defects", [])
        if not defects:
            await message.answer("❌ Нет сохранённых дефектов для формирования отчёта.")
            return

        buffer = generate_defect_only_report(data)
        buffer.seek(0)
        input_file = BufferedInputFile(buffer.read(), filename="defects_report.docx")

        for defect in defects:
            try:
                if defect.get("image_path") and os.path.isfile(defect["image_path"]):
                    os.remove(defect["image_path"])
            except Exception as e:
                logging.warning(f"[WARNING] Не удалось удалить файл {defect['image_path']}: {e}")

        await message.answer_document(input_file)
        await state.clear()

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📸 Загрузить дефекты", callback_data="start_defects")]
        ])
        await message.answer("✅ Отчёт сформирован. Можете загрузить новый набор дефектов:", reply_markup=kb)
