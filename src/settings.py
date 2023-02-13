from pydantic import BaseSettings
from pathlib import Path

class Settings(BaseSettings):

    DB_HOST: str = "localhost"
    DB_PORT: str = "6666"

    media_root: str = "/media/"
    media_path: Path = Path("./srv/media")
    

settings = Settings()