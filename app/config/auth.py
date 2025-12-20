from datetime import timedelta

from authx import AuthXConfig, AuthX

from app.config.config import settings

secret_key = settings.JWT_SECRET_KEY
if not secret_key:
    raise ValueError("Необходимо установить JWT_SECRET_KEY в .env")

config = AuthXConfig(
    JWT_SECRET_KEY=secret_key,
    JWT_ALGORITHM=settings.JWT_ALGORITHM,
    JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=7),
    JWT_COOKIE_CSRF_PROTECT=False
)

security = AuthX(config=config)