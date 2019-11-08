from flask_babel import _, lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import TextField, SubmitField


class MenuForm(FlaskForm):
    name = TextField(label = _l("Link name"))
    submit = SubmitField(_l('Submit'))
