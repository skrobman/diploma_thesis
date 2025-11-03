from authx import AuthXConfig, AuthX
from dotenv import load_dotenv
import os

load_dotenv()

config = AuthXConfig()
config.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default_secret")
config.JWT_ACCESS_COOKIE_NAME = "access_token"
config.JWT_COOKIE_CSRF_PROTECT = False
config.JWT_TOKEN_LOCATION = ["headers"]

security = AuthX(config=config)