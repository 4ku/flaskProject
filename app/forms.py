from flask_babel import _, lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import TextField, SubmitField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired


class MenuForm(FlaskForm):
    name = TextField(label = _l("Link name"))
    submit = SubmitField(_l('Submit'))

class LogoForm(FlaskForm):
    file = FileField(label = _l("New logo"), validators = [DataRequired(), FileAllowed(['jpg', 'png','jpeg', 'svg'])])
    submit = SubmitField(_l('Submit'))