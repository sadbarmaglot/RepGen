"""
Endpoints для проверки обновлений десктоп-клиентов.

Метаданные релизов хранятся в публичном GCS-бакете repgen_releases:
  windows/latest.json — текущая версия для Windows

Бакет публичный (allUsers:objectViewer), поэтому загрузка установщика идёт
напрямую с storage.googleapis.com, минуя бэкенд.
"""
import time
from typing import Literal

import httpx
from fastapi import APIRouter, HTTPException

from common.logging_utils import get_user_logger

logger = get_user_logger(__name__)

router = APIRouter(prefix="/desktop", tags=["desktop-updates"])

RELEASES_BASE_URL = "https://storage.googleapis.com/repgen_releases"
CACHE_TTL_SECONDS = 60

_cache: dict[str, tuple[float, dict]] = {}


@router.get("/version")
async def get_latest_version(platform: Literal["windows"] = "windows") -> dict:
    """
    Возвращает метаданные последнего релиза для указанной платформы.

    Структура ответа:
        {
            "version": "1.0.1",
            "url": "https://storage.googleapis.com/repgen_releases/windows/AI-Engineer-Setup-1.0.1.exe",
            "released_at": "2026-04-29",
            "notes": "...",
            "min_supported": "1.0.0"  // optional
        }

    Возвращает 404, если релизов для платформы ещё нет.
    """
    now = time.monotonic()
    cached = _cache.get(platform)
    if cached and now - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    url = f"{RELEASES_BASE_URL}/{platform}/latest.json"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
    except httpx.RequestError as exc:
        logger.error(f"Failed to fetch latest release for {platform}: {exc}")
        raise HTTPException(status_code=502, detail="Release storage unavailable")

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail=f"No releases for platform '{platform}'")
    if response.status_code != 200:
        logger.error(f"Unexpected status from releases storage: {response.status_code}")
        raise HTTPException(status_code=502, detail="Release storage error")

    try:
        data = response.json()
    except ValueError:
        logger.error(f"Invalid JSON in latest.json for {platform}")
        raise HTTPException(status_code=502, detail="Malformed release metadata")

    _cache[platform] = (now, data)
    return data
