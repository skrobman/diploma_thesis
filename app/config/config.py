from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str

    JWT_SECRET_KEY: str
    JWT_REFRESH_TOKEN: str
    JWT_REFRESH_TOKEN_EXPIRES: str
    JWT_ALGORITHM: str

    MAILJET_API_KEY: str
    MAILJET_SECRET_KEY: str
    SENDER_EMAIL: str
    SENDER_NAME: str

    RENDER_LINK: str
    FRONTEND_URL: str = "https://tasklytool.netlify.app"
    BASE_LINK: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()