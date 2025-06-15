import os

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

class Settings(BaseSettings):
    load_dotenv()
    tg_token: str = os.environ["TG_TOKEN"]
    db_dsn: str = os.environ["DATABASE_URL"]

settings = Settings()