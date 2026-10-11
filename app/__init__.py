import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template

load_dotenv()


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).resolve().parent.parent / "templates"),
    )
    app.secret_key = os.getenv("SECRET_KEY", "").strip() or secrets.token_hex(32)
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
    from app.transient import WorkflowStore
    app.extensions["workflows"] = WorkflowStore()
    from app.discovery import jobs, csrf_token
    app.jinja_env.globals["csrf_token"] = csrf_token
    app.register_blueprint(jobs)

    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

    from app.routes import main
    app.register_blueprint(main)

    @app.errorhandler(413)
    def upload_too_large(_error):
        return render_template(
            "index.html",
            error="The upload request is too large. Keep the combined PDF and form data below 5 MiB.",
        ), 413

    return app
