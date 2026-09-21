from flask import Flask
from flask_smorest import Api

from .api import blueprint


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.update(
        API_TITLE="Teya Ledger API",
        API_VERSION="1.0.0",
        OPENAPI_VERSION="3.0.0",
        OPENAPI_URL_PREFIX="/",
        OPENAPI_SWAGGER_UI_PATH="/docs",
        OPENAPI_SWAGGER_UI_URL="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/",
    )
    api = Api(app)
    api.register_blueprint(blueprint)
    return app
