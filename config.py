import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'y0u-wi11-never-guess'
    # SQLALCHEMY_DATABASE_URI = 'mysql://sarp_admin:123456@localhost/sqlalchemy?charset=utf8mb4'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    'sqlite:///' + os.path.join(basedir, 'app.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_TYPE = 'filesystem'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    LANGUAGES = ['ru', 'en']