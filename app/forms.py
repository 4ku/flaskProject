from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User
from wtforms import StringField, TextAreaField, SubmitField, RadioField, FieldList, FormField
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
        choices=[('Admin','Admin'),('Usual','Usual user'),('Client','client')])
    
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



class TextAreaEntryForm(FlaskForm):
    text = TextAreaField('Add description', validators=[
        DataRequired(), Length(min=1, max=140)])

class PostForm(FlaskForm):
    text_areas = FieldList(FormField(TextAreaEntryForm), min_entries=1)
    # post = TextAreaField('Add task', validators=[
    #     DataRequired(), Length(min=1, max=140)])

    
    user_list = SelectField('users', choices=[])
    submit = SubmitField('Submit')
    add_field = SubmitField('Add field')




class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    role_list = SelectField('Role', 
        choices=[('Admin','Admin'),('Usual','Usual user'),('Client','Client')])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png','jpeg'])])
    submit = SubmitField('Submit')

    
    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')   



class EditTaskForm(FlaskForm):
    assigner = SelectField('Assigner', choices=[(1,"cl1"),(2,"cl2")], coerce=int)
    acceptor = SelectField('Acceptor', choices=[(2,"cl2")], coerce = int)
    post = TextAreaField('Add task', validators=[
        DataRequired(), Length(min=1, max=140)])
    status = SelectField('Status', 
        choices=[('Issued','Issued'),('In progress','In progress'),('Done','Done')])
    submit = SubmitField('Submit')  