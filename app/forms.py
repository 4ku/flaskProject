from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User
from wtforms import StringField, TextField, TextAreaField, SubmitField, RadioField, FieldList, FormField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileField, FileAllowed

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    user_role = RadioField('User role', 
        choices=[('Admin','Admin'),('Usual','Usual user'),('Client','Client')])
    
    submit = SubmitField('Register')
    

    def validate_username(self, username):
        try:
            user = User.query.filter_by(username=username.data).first()
        except:
            user = None
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class EditProfileForm_Admin(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    role_list = SelectField('Role', 
        choices=[('Admin','Admin'),('Usual','Usual user'),('Client','Client')])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png','jpeg'])])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm_Admin, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

class EditProfileForm(FlaskForm):
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png','jpeg'])])
    submit = SubmitField('Submit')

class TaskForm_edit(FlaskForm):
    assigner = SelectField('Assigner', choices=[], coerce=int)
    acceptor = SelectField('Acceptor', choices=[], coerce = int)
    status = SelectField('Status', 
        choices=[('Issued','Issued'),('In progress','In progress'),('Done','Done')])
    submit = SubmitField('Submit')

class TaskForm_create(FlaskForm):
    acceptor = SelectField('Acceptor', choices=[], coerce = int)
    submit = SubmitField('Submit')

class AddFieldForm(FlaskForm):
    add_field = SubmitField('Add field')
    fields_list = SelectField('Field type', 
        choices=[('Text','Text'), ('TextArea','TextArea'),('Date','Date'),('File','File')])

class MenuForm(FlaskForm):
    name = TextField(label = "Link name")
    submit = SubmitField('Submit')


def check_file_label(form, field):
    if (field.label.text["filename"] == "") and (not field.data):
        raise ValidationError('Please choose a file')