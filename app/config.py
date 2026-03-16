import os
from dataclasses import dataclass


@dataclass
class Settings:
    host: str = os.getenv("APP_HOST", "127.0.0.1")
    port: int = int(os.getenv("APP_PORT", "5000"))
    auto_open_browser: bool = os.getenv("APP_OPEN_BROWSER", "1") == "1"


settings = Settings()
