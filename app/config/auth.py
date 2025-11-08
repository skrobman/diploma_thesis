from authx import AuthXConfig, AuthX
from dotenv import load_dotenv
import os

load_dotenv()

DEFAULT_EXPIRES_IN_SECONDS = 604800
expires_int = DEFAULT_EXPIRES_IN_SECONDS

try:
    expires_str = os.getenv("JWT_REFRESH_TOKEN_EXPIRES")

    if expires_str is not None:
        expires_int = int(expires_str)
except (ValueError, TypeError):

    pass

config = AuthXConfig(
    JWT_REFRESH_TOKEN_EXPIRES=expires_int,

    JWT_COOKIE_CSRF_PROTECT=False
)

security = AuthX(config=config)