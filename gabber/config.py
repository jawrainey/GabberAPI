# -*- coding: utf-8 -*-
import datetime
import os


class Config:
    HOST = '0.0.0.0'
    WEB_HOST = os.environ.get('WEB_HOST', 'http://localhost:8080')
    SECRET_KEY = os.environ.get('SECRET_KEY', '')
    SALT = os.environ.get('SALT', '')

    BRAND = os.environ.get('BRAND', 'Gabber')
    CONTACT_EMAIL = os.environ.get('CONTACT_EMAIL', 'admin@gabber.audio')

    MAILBOX = os.environ.get('MAILBOX', '')
    MAIL_API_KEY = os.environ.get('MAIL_API_KEY', '')
    MAIL_SENDER_NAME = os.environ.get('MAIL_SENDER_NAME', 'Gabber Admin')
    MAIL_SENDER_EMAIL = os.environ.get('MAIL_SENDER_EMAIL', 'admin@gabber.audio')

    S3_REGION = os.getenv('S3_REGION', 'eu-west-1')
    S3_BUCKET = os.getenv('S3_BUCKET', '')
    S3_KEY = os.getenv('S3_KEY', '')
    S3_SECRET = os.getenv('S3_SECRET', '')
    S3_LOCATION = 'https://{}.s3.amazonaws.com/'.format(S3_BUCKET)

    S3_PIPELINE_ID = os.getenv('S3_PIPELINE_ID', '')
    S3_PIPELINE_PRESET_ID = os.getenv('S3_PIPELINE_PRESET_ID', '')
    S3_ROOT_FOLDER = os.getenv('S3_APP_NAME', 'main')
    S3_PROJECT_MODE = os.environ.get('S3_APP_MODE', 'dev')

    JWT_SECRET_KEY = os.environ.get('JWT_SECRET', '')
    FCM_API_KEY = os.environ.get('FCM_API_KEY', '')
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(minutes=60*24*499)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '')
    PHOTOS_API_KEY = os.getenv('PHOTOS_API_KEY', '')

    JSONIFY_PRETTYPRINT_REGULAR = False


class Development(Config):
    DEBUG = True


class Testing(Config):
    TESTING = True


class Production(Config):
    pass


config = {
    'dev': Development,
    'prod': Production,
    'test': Testing
}
