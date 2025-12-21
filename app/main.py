from authx.exceptions import AuthXException
from fastapi.responses import JSONResponse
from fastapi import FastAPI, HTTPException, Request

from app.config.config_logging import LOGGING_CONFIG
from app.routes import task_route
from app.routes.users import user, user_profile

from fastapi.middleware.cors import CORSMiddleware

import logging.config

from app.routes.projects import general, members, archive, invitations

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "https://tasklytool.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(user.router)

app.include_router(user_profile.router)

#Роуты для проектов
app.include_router(general.router)
app.include_router(invitations.router)
app.include_router(members.router)
app.include_router(archive.router)

#Роуты для тасок
app.include_router(task_route.router)

# Конфигурация логгера
logging.config.dictConfig(LOGGING_CONFIG)

@app.exception_handler(AuthXException)
async def authx_exception_handler(
    request: Request,
    exc: AuthXException,
):
    response = JSONResponse(
        status_code=403,
        content={"detail": str(exc)},
    )

    origin = request.headers.get("origin")
    if origin in [
        "http://localhost:5173",
        "https://tasklytool.netlify.app",
    ]:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"

    return response

@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

    origin = request.headers.get("origin")
    if origin in [
        "http://localhost:5173",
        "https://tasklytool.netlify.app",
    ]:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"

    return response