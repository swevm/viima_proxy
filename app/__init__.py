from flask import Flask
from .proxyapp import proxyapp


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY='dev')

    app.register_blueprint(proxyapp)
    return app

