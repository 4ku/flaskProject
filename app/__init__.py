from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_session import Session
from flask import session
from flask_babel import Babel
from config import Config


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
db.create_all()
migrate = Migrate(app, db)
babel = Babel(app)
login = LoginManager(app)
login.session_protection = "strong"
login.login_view = 'login'
Session(app)
app.jinja_env.globals['LANGUAGES'] = app.config['LANGUAGES']

@babel.localeselector
def get_locale():
    if "CURRENT_LANGUAGE" in session:
        return session["CURRENT_LANGUAGE"]
    return request.accept_languages.best_match(app.config['LANGUAGES'])

from app import routes, task_routes, models
