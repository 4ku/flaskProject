from flask_wtf import FlaskForm
from flask_babel import _, lazy_gettext as _l
from wtforms.validators import ValidationError, DataRequired
from app.models import Sections
from wtforms import TextField, BooleanField, SubmitField


class SectionForm(FlaskForm):
    name = TextField(label = _l("Page name"), validators =[DataRequired()])
    is_displayed =  BooleanField(_l('Display'))
    submit = SubmitField(_l('Submit'))

    def __init__(self, original_name, *args, **kwargs):
        super(SectionForm, self).__init__(*args, **kwargs)
        self.original_name = original_name

    def validate_name(self, name):
        if name.data != self.original_name:
            section = Sections.query.filter_by(name=self.name.data).first()
            if section is not None:
                raise ValidationError(_l('Please use a different section name.'))

class PageForm(FlaskForm):
    submit = SubmitField(_l('Submit'))