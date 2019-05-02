from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_user import UserManager
from config import Config

import logging
from logging.handlers import SMTPHandler
from logging.handlers import RotatingFileHandler
import os

from flask import Flask, session
# from flask.ext.session import Session

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
# Session(app)
login.login_view = 'login'

UPLOAD_FOLDER = './photos'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

from app import routes, models
user_manager = UserManager(app, db, models.User)

