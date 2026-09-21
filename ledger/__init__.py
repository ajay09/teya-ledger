from flask import Flask

from .api import blueprint


def create_app() -> Flask:
    app = Flask(__name__)
    # app.register_blueprint(blueprint, url_prefix="/v1")
    return app
