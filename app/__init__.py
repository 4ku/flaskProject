from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_moment import Moment
from flask_session import Session
from flask import session
from flask_babel import Babel
from config import Config
from datetime import datetime
from jinja2 import ChoiceLoader, FileSystemLoader

import logging
from logging.handlers import SMTPHandler
from logging.handlers import RotatingFileHandler
import os

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
db.create_all()
db.session.commit()


migrate = Migrate(app, db)
babel = Babel(app)
moment = Moment(app)
session_ = Session(app)

login = LoginManager(app)
login.session_protection = "strong"
login.login_view = 'auth.login'


# Blueprints - подгрузка модулей, которые находятся в папках auth, sections и tasks
from app.auth import bp as auth_bp
from app.sections import bp as sections_bp
from app.tasks import bp as tasks_bp
from app.users import bp as users_bp
app.register_blueprint(auth_bp)
app.register_blueprint(sections_bp, url_prefix = "/sections")
app.register_blueprint(tasks_bp, url_prefix = "/tasks")
app.register_blueprint(users_bp)



# Добавим путь для шаблонов динамических полей
loader = FileSystemLoader("app/dynamic_fields/templates/")
my_loader = ChoiceLoader([
        app.jinja_loader, loader ])
app.jinja_loader = my_loader


# Функция load_user необходима для LoginManager 
from app.models import Users
@login.user_loader
def load_user(id):
    return Users.query.get(int(id))

# Добавляем список языков и функцию сейчашнего времени в глобальные 
# переменные jinja, чтобы их можно было использовать в шаблонах
app.jinja_env.globals.update(now = datetime.utcnow)
app.jinja_env.globals['LANGUAGES'] = app.config['LANGUAGES']

# Получение текущего языка
@babel.localeselector
def get_locale():
    if "CURRENT_LANGUAGE" in session:
        return session["CURRENT_LANGUAGE"]
    return request.accept_languages.best_match(app.config['LANGUAGES'])

from app import routes, models, errors_handling