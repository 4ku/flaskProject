from flask_babel import _, lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField,SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from app.models import Users, Roles
from wtforms import Form, StringField, TextField, TextAreaField, SubmitField, \
    RadioField, FieldList, FormField, Field, HiddenField
from flask_wtf.file import FileField, FileAllowed
from wtforms.fields.html5 import DateField
from wtforms_sqlalchemy.fields import QuerySelectField
from sqlalchemy import or_
from flask_login import current_user


class LoginForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))

# def isEnglish(form, field):
#     english_alphabet = "abcdefghijklmnopqrstuvwxyz1234567890"
#     for letter in str(field.data).lower():
#         if letter not in english_alphabet:
#             raise ValidationError(_l('English letters or numbers required'))

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


def assigners_query():
    return Users.query.join(Users.roles).filter(or_(Roles.name == "Admin", 
        Roles.name == "Usual"), ~Users.roles.any(Roles.name == "God"))

def get_pk(obj):
    return str(obj)

def acceptors_query():
    return Users.query.join(Users.roles).filter(or_(Roles.name == "Client", 
        Roles.name == "Usual"), ~Users.roles.any(Roles.name == "God"), Users.id != current_user.id)

class TaskForm_edit(FlaskForm):
    assigner = QuerySelectField(_l('Assigner'), query_factory=assigners_query, 
        get_pk = get_pk, get_label ="email")
    acceptor = QuerySelectField(_l('Acceptor'), query_factory=acceptors_query, 
        get_pk = get_pk, get_label ="email")
    status = SelectField(_l('Status'), 
        choices=[('Issued',_l('Issued')),('In progress',_l('In progress')),('Done',_l('Done'))])
    submit = SubmitField(_l('Submit'))

class TaskForm_create(FlaskForm):
    acceptor = QuerySelectField(_l('Acceptor'), query_factory=acceptors_query, 
        get_pk = get_pk, get_label ="email")
    submit = SubmitField(_l('Submit'))

class AddFieldForm(FlaskForm):
    fields_list = SelectField(_l('Field type'), 
        choices=[('Text',_l('Text')), ('TextArea',_l('TextArea')),
            ('Date',_l('Date')),('File',_l('File')),('Picture',_l('Picture')),('Link',_l('Link'))])

class TemplateForm(FlaskForm):
    name = TextField(label = _l("Template name"))
    submit = SubmitField(_l('Submit'))

class MenuForm(FlaskForm):
    name = TextField(label = _l("Link name"))
    submit = SubmitField(_l('Submit'))





#______________________________________
#             Main Forms
# -------------------------------------

class FieldForm(Form):
    label_ = TextField(label = _l("Label"),validators=[Length(max=50)])
    is_displayed =  BooleanField(_l('Display'))
    order = HiddenField()


# text form
class ExtTextField(FieldForm):
    text = TextField()

class TextsForm(FlaskForm):
    text_fields = FieldList(
        FormField(ExtTextField)
    )


# text area form
class ExtTextAreaField(FieldForm):
    textArea = TextAreaField()

class TextAreasForm(FlaskForm):
    textArea_fields = FieldList(
        FormField(ExtTextAreaField)
    )


# date form
class ExtDateField(FieldForm):
    date = DateField()

class DatesForm(FlaskForm):
    date_fields = FieldList(
        FormField(ExtDateField)
    )


# link form
class LinkField(FieldForm):
    link = TextField()

class LinksForm(FlaskForm):
    link_fields = FieldList(
        FormField(LinkField)
    )


# file form
class ExtFileField(FieldForm):
    file = FileField()
    filename = HiddenField()
    encrypted_filename = HiddenField()

class FilesForm(FlaskForm):
    file_fields = FieldList(
        FormField(ExtFileField)
    )


# picture form
class PictureField(FieldForm):
    picture = FileField()
    filename = HiddenField()
    encrypted_filename = HiddenField()

class PicturesForm(FlaskForm):
    picture_fields = FieldList(
        FormField(PictureField)
    )

def check_file_label(form, field):
    if (form.filename.data == "") and (not field.data):
        raise ValidationError(_l('Please choose a file'))