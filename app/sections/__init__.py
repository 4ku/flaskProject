from flask import Blueprint

bp = Blueprint('sections', __name__, template_folder='templates')

from app.sections import routes
