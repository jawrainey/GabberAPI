from .config import config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
jwt = JWTManager()
ma = Marshmallow()
migrate = Migrate()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)

    from .api import restful_api
    restful_api.init_app(app)

    # TODO: create a blueprint that handles errors
    from gabber.utils import general as er
    app.register_error_handler(er.CustomException, lambda e: er.custom_response(e.status_code, e.data, e.errors))

    # TODO: use Flask-Script for database initialisation, etc.
    return app
