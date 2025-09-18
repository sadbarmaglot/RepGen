import logging
import uvicorn

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from common.whitelist_utils import load_whitelist
from core.handlers import BotHandlers
from core.photo_manager import PhotoManager
from settings import DefectStates, BOT_TOKEN

from api.services.defect_analyzer import DefectAnalyzer
from api.services.model_manager import ModelManager
from api.models.config import (
    DefectAnalysisRequest, DefectAnalysisResponse
)
from api.routes.auth import router as auth_router
from api.routes.projects import router as projects_router
from api.routes.objects import router as objects_router
from api.routes.object_members import router as object_members_router
from api.routes.upload import router as upload_router
from api.routes.plans import router as plans_router
from api.routes.marks import router as marks_router
from api.routes.photos import router as photos_router
from api.routes.construction import router as construction_router

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    root_path="/repgen",
    title="Defect Analysis API",
    description="API для анализа дефектов строительных конструкций по изображениям",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(objects_router)
app.include_router(object_members_router)
app.include_router(plans_router)
app.include_router(marks_router)
app.include_router(photos_router)
app.include_router(upload_router)
app.include_router(construction_router)

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

# Инициализация сервисов
model_manager = ModelManager()
defect_analyzer = DefectAnalyzer(model_manager)

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {"message": "Defect Analysis API", "status": "running"}

@app.get("/health")
async def health_check():
    """Проверка состояния сервиса"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "available_models": model_manager.get_available_models()
    }


@app.post("/analyze_images", response_model=DefectAnalysisResponse)
async def analyze_defects(
    request: DefectAnalysisRequest,
):
    """
    Анализ дефектов по изображениям
    
    Принимает список URL изображений и возвращает анализ дефектов
    """
    try:
        logger.info(f"Получен запрос на анализ {len(request.image_infos)} изображений")
        
        # Валидация количества изображений
        if len(request.image_infos) > 20:
            raise HTTPException(
                status_code=400, 
                detail="Максимальное количество изображений: 20"
            )
        
        # Анализ изображений
        results = await defect_analyzer.analyze_images(
            image_infos=request.image_infos,
            config=request.config
        )
        
        return DefectAnalysisResponse(results=results)
        
    except Exception as e:
        logger.error(f"Ошибка при анализе: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    # asyncio.run(main())