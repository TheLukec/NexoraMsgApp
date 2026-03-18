import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "Nexora Group Chat Server")
    host: str = os.getenv("SERVER_HOST", "0.0.0.0")
    port: int = int(os.getenv("SERVER_PORT", "8000"))
    secret_key: str = os.getenv("SECRET_KEY", "change-this-secret-key")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))

    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL"))

    cors_allow_origins: str = os.getenv("CORS_ALLOW_ORIGINS", "")
    default_admin_username: str = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    default_admin_password: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

    uploads_dir: str = os.getenv("UPLOADS_DIR", "uploads")
    default_max_upload_mb: int = int(os.getenv("DEFAULT_MAX_UPLOAD_MB", "10"))

    def post_init(self):
        if not self.database_url:
            raise ValueError("DATABASE_URL is not set in environment variables")

    def parsed_cors_origins(self) -> list[str]:
        if self.cors_allow_origins.strip() == "":
            return ["*"]
        return [item.strip() for item in self.cors_allow_origins.split(",") if item.strip()]


settings = Settings()
