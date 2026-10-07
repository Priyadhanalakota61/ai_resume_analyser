from dotenv import load_dotenv
from flask import Flask, render_template

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

    from app.routes import main
    app.register_blueprint(main)

    @app.errorhandler(413)
    def upload_too_large(_error):
        return render_template(
            "index.html",
            error="The upload request is too large. Use a PDF smaller than 5 MiB.",
        ), 413

    return app
