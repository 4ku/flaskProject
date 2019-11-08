from flask_babel import _, lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from app.models import Users
from wtforms import StringField, PasswordField, BooleanField, SubmitField

class LoginForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))

def isRussian(form, field):
    russian_alphabet = "йцукенгшщзхъфывапролджэячсмитьбю"
    for letter in str(field.data).lower():
        if letter not in russian_alphabet:
            raise ValidationError(_l('Russian letters required'))

class RegistrationForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    last_name = StringField(_l('Last name'), validators=[DataRequired(), isRussian])
    first_name = StringField(_l('First name'), validators=[DataRequired(), isRussian])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Register'))
    
    def validate_email(self, email):
        try:
            user = Users.query.filter_by(email=email.data).first()
        except:
            user = None
        if user is not None:
            raise ValidationError(_l('Please use a different email address.'))