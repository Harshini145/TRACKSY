from pydantic_settings import BaseSettings
from functools import lru_cache
from sqlalchemy.engine.url import URL


class Settings(BaseSettings):
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "tracksy"

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    APP_BASE_URL: str = "http://localhost:8000"

    # SMTP / Gmail
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_NAME: str = "Tracksy"

    # Budget thresholds
    BUDGET_WARNING_PERCENT: float = 80.0   # fire warning at 80 % spent

    @property
    def DATABASE_URL(self) -> URL:
        # Pass None (not empty string) when no password is set so MySQL
        # treats the login as "no password" instead of "wrong password"
        pwd = self.DB_PASSWORD if self.DB_PASSWORD else None
        return URL.create(
            "mysql+pymysql",
            username=self.DB_USER,
            password=pwd,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME
        )

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
