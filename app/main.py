from pathlib import Path

from flask import Flask

from config import settings
from gui import open_in_browser
from routes import web

BASE_DIR = Path(__file__).resolve().parent


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=str(BASE_DIR / "static"),
        template_folder=str(BASE_DIR / "templates"),
    )
    app.register_blueprint(web)
    return app


app = create_app()


if __name__ == "__main__":
    local_url = f"http://{settings.host}:{settings.port}"
    if settings.auto_open_browser:
        open_in_browser(local_url)
    app.run(host=settings.host, port=settings.port, debug=False)
