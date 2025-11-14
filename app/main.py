from authx.exceptions import AuthXException
from fastapi import FastAPI, HTTPException, Depends, Request
from dotenv import load_dotenv
import os

from app.config.auth import security
from app.routes import user, project_route

from fastapi.middleware.cors import CORSMiddleware

import logging
import logging.config
import sys

app = FastAPI()
app.include_router(user.router)

app.include_router(project_route.router)

load_dotenv()

api_key = os.getenv("MAILJET_API_KEY")
api_secret = os.getenv("MAILJET_SECRET_KEY")
sender_email = os.getenv("SENDER_EMAIL")
sender_name = os.getenv("SENDER_NAME")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,  # Оставляем логгеры uvicorn и FastAPI

    # Форматтеры: как будет выглядеть строка лога
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            # Пример: 2025-11-11 20:10:05,123 - app.services.auth_service - ERROR - Database timeout
        },
    },

    # Обработчики: куда отправлять логи
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",  # Вывод в "поток" (консоль)
            "formatter": "default",  # Используем наш форматтер "default"
            "stream": sys.stdout,  # Конкретно - в stdout (стандартный вывод)
        },
    },

    # Логгеры: какие логгеры как настроить
    "root": {  # "Корневой" логгер (по умолчанию для ВСЕХ)
        "level": "INFO",  # Минимальный уровень для вывода (DEBUG, INFO, WARNING, ERROR)
        "handlers": ["console"],  # Куда отправлять: на 'console'
    },
}

# 2. Применяем конфигурацию
logging.config.dictConfig(LOGGING_CONFIG)

@app.exception_handler(AuthXException)
async def authx_exception_handler(request: Request, exc: AuthXException):
    raise HTTPException(status_code=403, detail=str(exc))