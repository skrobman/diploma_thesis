from authx import AuthXConfig, AuthX
from dotenv import load_dotenv
import os

load_dotenv()

DEFAULT_EXPIRES_IN_SECONDS = 604800
expires_int = DEFAULT_EXPIRES_IN_SECONDS

# try:
#     expires_str = os.getenv("JWT_REFRESH_TOKEN_EXPIRES")
#     if expires_str is not None:
#         expires_int = int(expires_str)
# except (ValueError, TypeError):
#     pass

secret_key = os.getenv("JWT_SECRET_KEY")
if not secret_key:
    raise ValueError("Необходимо установить JWT_SECRET_KEY в .env")

config = AuthXConfig(
    JWT_SECRET_KEY=secret_key,
    JWT_ALGORITHM="HS256",
    JWT_REFRESH_TOKEN_EXPIRES=os.getenv("JWT_REFRESH_TOKEN_EXPIRES", "7d"),
    #JWT_REFRESH_TOKEN_EXPIRES=expires_int,
    JWT_COOKIE_CSRF_PROTECT=False
)

security = AuthX(config=config)