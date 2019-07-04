from flask_babel import _, lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User
from wtforms import StringField, TextField, TextAreaField, SubmitField, RadioField, FieldList, FormField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileField, FileAllowed
from wtforms.fields.html5 import DateField

class LoginForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))


def isEnglish(form, field):
    english_alphabet = "abcdefghijklmnopqrstuvwxyz1234567890"
    for letter in str(field.data).lower():
        if letter not in english_alphabet:
            raise ValidationError(_l('English letters or numbers required'))

def isRussian(form, field):
    russian_alphabet = "йцукенгшщзхъфывапролджэячсмитьбю"
    for letter in str(field.data).lower():
        if letter not in russian_alphabet:
            raise ValidationError(_l('Russian letters required'))

class RegistrationForm(FlaskForm):
    real_name = StringField(_l('Username'), validators=[DataRequired(), isRussian])
    username = StringField(_l('Login'), validators=[DataRequired(), isEnglish])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(), EqualTo('password')])
    user_role = RadioField(_l('User role'), 
        choices=[('Admin',_l('Admin')),('Usual',_l('Usual user')),('Client',_l('Client'))])
    
    submit = SubmitField(_l('Register'))
    

    def validate_username(self, username):
        try:
            user = User.query.filter_by(username=username.data).first()
        except:
            user = None
        if user is not None:
            raise ValidationError(_l('Please use a different username.'))

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_l('Please use a different email address.'))

class EditProfileForm_Admin(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    role_list = SelectField(_l('Role'), 
        choices=[('Admin',_l('Admin')),('Usual',_l('Usual user')),('Client',_l('Client'))])
    picture = FileField(_l('Update Profile Picture'), validators=[FileAllowed(['jpg', 'png','jpeg'])])
    submit = SubmitField(_l('Submit'))

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm_Admin, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError(_l('Please use a different username.'))

class EditProfileForm(FlaskForm):
    picture = FileField(_l('Update Profile Picture'), validators=[FileAllowed(['jpg', 'png','jpeg'])])
    submit = SubmitField(_l('Submit'))

class TaskForm_edit(FlaskForm):
    assigner = SelectField(_l('Assigner'), choices=[], coerce=int)
    acceptor = SelectField(_l('Acceptor'), choices=[], coerce = int)
    status = SelectField(_l('Status'), 
        choices=[('Issued',_l('Issued')),('In progress',_l('In progress')),('Done',_l('Done'))])
    submit = SubmitField(_l('Submit'))

class TaskForm_create(FlaskForm):
    acceptor = SelectField(_l('Acceptor'), choices=[], coerce = int)
    submit = SubmitField(_l('Submit'))

class AddFieldForm(FlaskForm):
    add_field = SubmitField(_l('Add field'))
    fields_list = SelectField(_l('Field type'), 
        choices=[('Text',_l('Text')), ('TextArea',_l('TextArea')),
            ('Date',_l('Date')),('File',_l('File')),('Picture',_l('Picture')),('Link',_l('Link'))])

class TemplateForm(FlaskForm):
    name = TextField(label = _l("Template name"))
    submit = SubmitField(_l('Submit'))

class MenuForm(FlaskForm):
    name = TextField(label = _l("Link name"))
    submit = SubmitField(_l('Submit'))


def check_file_label(form, field):
    if (field.label.text["filename"] == "") and (not field.data):
        raise ValidationError(_l('Please choose a file'))