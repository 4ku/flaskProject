from flask_babel import _, lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms.validators import ValidationError, DataRequired, Length
from wtforms import Form, TextField, TextAreaField, \
    FieldList, FormField, HiddenField, BooleanField, SelectField
from flask_wtf.file import FileField, FileAllowed
from wtforms.fields.html5 import DateField

# Форма для кнопки добавления поля
class AddFieldForm(FlaskForm):
    fields_list = SelectField(_l('Field type'), 
        choices=[('Text',_l('Text')), ('TextArea',_l('TextArea')),
            ('Date',_l('Date')),('File',_l('File')),('Picture',_l('Picture')),('Link',_l('Link'))])


# Это основная форма, от которой все наследуются
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
    file_type = SelectField('File type', 
        choices=[('1',_l('Счёт фактура')),('2',_l('Не счёт фатура')),('3',_l('Что-то ещё'))])

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