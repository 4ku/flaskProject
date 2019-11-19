import os
from datetime import timedelta
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'y0u-wi11-never-guess'
    # SQLALCHEMY_DATABASE_URI = 'mysql://sarp_admin:123456@localhost/sqlalchemy?charset=utf8mb4'
    # SQLALCHEMY_DATABASE_URI = 'mysql://u0700504_admin:admin1.@localhost/u0700504_flaskprojectdb?charset=utf8mb4'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    'sqlite:///' + os.path.join(basedir, 'app.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=5)
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    LANGUAGES = ['ru', 'en']


    ADMINS = "sarp.project@ya.ru"
    MAIL_SERVER="smtp.yandex.com"
    MAIL_PORT=465
    MAIL_USERNAME="sarp.project@ya.ru"
    MAIL_PASSWORD="1234567z"

