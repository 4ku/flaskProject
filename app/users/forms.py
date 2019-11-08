from flask_babel import _, lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms.validators import ValidationError, DataRequired, Email
from app.models import Users
from wtforms import Form, StringField, SubmitField, SelectField
from flask_wtf.file import FileField, FileAllowed

class EditProfileForm_Admin(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    role_list = SelectField(_l('Role'), 
        choices=[('Admin',_l('Admin')),('Usual',_l('Usual user')),('Not confirmed',_l('Not confirmed'))])
    picture = FileField(_l('Update Profile Picture'), validators=[FileAllowed(['jpg', 'png','jpeg'])])
    submit = SubmitField(_l('Submit'))

    def __init__(self, original_email, *args, **kwargs):
        super(EditProfileForm_Admin, self).__init__(*args, **kwargs)
        self.original_email = original_email

    def validate_email(self, email):
        if email.data != self.original_email:
            user = Users.query.filter_by(email=self.email.data).first()
            if user is not None:
                raise ValidationError(_l('Please use a different email.'))


class EditProfileForm(FlaskForm):
    picture = FileField(_l('Update Profile Picture'), validators=[FileAllowed(['jpg', 'png','jpeg'])])
    submit = SubmitField(_l('Submit'))