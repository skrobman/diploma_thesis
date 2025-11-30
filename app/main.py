from authx.exceptions import AuthXException
from fastapi import FastAPI, HTTPException

from app.config.config_logging import LOGGING_CONFIG
from app.routes import user, project_route

from fastapi.middleware.cors import CORSMiddleware

import logging.config

app = FastAPI()
app.include_router(user.router)

app.include_router(project_route.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация логгера
logging.config.dictConfig(LOGGING_CONFIG)

@app.exception_handler(AuthXException)
async def authx_exception_handler(exc: AuthXException):
    raise HTTPException(status_code=403, detail=str(exc))