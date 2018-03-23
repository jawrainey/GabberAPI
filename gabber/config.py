import datetime
import os


class Config:
    HOST = '0.0.0.0'
    WEB_HOST = os.environ.get('WEB_HOST', 'http://localhost:8080')
    SECRET_KEY = os.environ.get('SECRET_KEY', '')
    SALT = os.environ.get('SALT', 'secret')

    JWT_SECRET_KEY = os.environ.get('JWT_SECRET', 'secret')
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(minutes=60 * 24 * 499)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '')


class Development(Config):
    DEBUG = True


class Testing(Config):
    TESTING = True


class Production(Config):
    pass


config = {
    'development': Development,
    'testing': Testing,
    'production': Production,
    'default': Development
}
