from flask import request, session
from shutil import copyfile
import os
from wtforms import validators
from datetime import datetime
from flask_babel import _, lazy_gettext as _l

from app import app, db
from app.models import *
from app.routes import encode_filename
from app.dynamic_fields.forms import *


def add_and_fill_fields_to_form(fields, is_template, forms):
    text_validator = [Length(max=50)] if is_template else [Length(max=50), DataRequired()]
    textArea_validator = [Length(max=255)] if is_template else [Length(max=255), DataRequired()]
    date_validator = [validators.Optional()] if is_template else [DataRequired()]
    link_validator = [] if is_template else [DataRequired()] 
    file_validator = [] if is_template else [check_file_label] 
    picture_validator = [FileAllowed(['jpg', 'png','jpeg'])] if is_template else [check_file_label, FileAllowed(['jpg', 'png','jpeg'])]
    number_validator = [check_number] if is_template else [DataRequired(),check_number]

    delattr(ExtTextField, "text")
    setattr(ExtTextField, "text", TextField(label = _("Text"), validators = text_validator))
    delattr(ExtTextAreaField, "textArea")
    setattr(ExtTextAreaField, "textArea", TextAreaField(label = _("TextArea"), validators = textArea_validator))
    delattr(ExtDateField, "date")
    setattr(ExtDateField, "date", DateField(label = _("Date"), validators=date_validator))
    delattr(LinkField, "link")
    setattr(LinkField, "link", TextField(label = _("Link"), validators=link_validator))
    delattr(ExtFileField, "file")
    setattr(ExtFileField, "file", FileField(label = _('File'), validators=file_validator))
    delattr(PictureField, "picture")
    setattr(PictureField, "picture", FileField(label =_('Picture'), validators=picture_validator))
    delattr(NumberField, "number")
    setattr(NumberField, "number", TextField(label =_('number'), validators=number_validator))

    for field in fields:
        field_data = field.media
        data = {'label_': field.label, 'is_displayed': field.display,"order": field.order}
        if field_data.text is not None:
            data["text"] = field_data.text
            forms["text_form"].text_fields.append_entry(data)
        elif field_data.textArea is not None:
            data["textArea"] = field_data.textArea
            forms["textArea_form"].textArea_fields.append_entry(data)
        elif field_data.link is not None:
            data["link"] = field_data.link 
            forms["link_form"].link_fields.append_entry(data)
        elif field_data.filename is not None:
            data["filename"] = field_data.filename
            data["encrypted_filename"] = field_data.encrypted_filename
            data["file_type"] = field_data.file_type
            forms["file_form"].file_fields.append_entry(data)
        elif field_data.picture is not None:
            data["filename"] = field_data.picture
            data["encrypted_filename"] = field_data.encrypted_filename
            forms["picture_form"].picture_fields.append_entry(data)
        elif field_data.number is not None:
            data["number"] = field_data.number 
            forms["number_form"].number_fields.append_entry(data)
        else:
            data["date"] = field_data.date 
            forms["date_form"].date_fields.append_entry(data)


def save_file(file, field_filename, field_encrypted_filename):
    filename, encrypted_filename = "", ""
    # Если добавляем свой файл 
    if file:
    # Неважно редактирование или нет - просто сохраняем новый файл, старые, если они были, потом удалятся  
        filename, encrypted_filename = encode_filename(file.filename)
        file.save(os.path.join(app.root_path, 'static/files/',  encrypted_filename))
        return filename, encrypted_filename

    # Если есть предыдущий файл, то делаем его копию, оригинал позже удалится.
    elif field_filename:
        src_path = os.path.join(app.root_path, 'static/files/', field_encrypted_filename)
        filename, encrypted_filename = encode_filename(field_filename)
        dst_path = os.path.join(app.root_path, 'static/files/', encrypted_filename)
        copyfile(src_path, dst_path)
        return filename, encrypted_filename
    return field_filename, field_encrypted_filename   


def save_fields(content, forms):
    #Записываем id старых полей, чтобы потом удалить в конце этого метода
    old_fields_id = [field.id for field in content.fields] 

    def save_field(field, media):
            label = field.label_.data
            is_displayed = field.is_displayed.data
            order = field.order.data
            field = Fields(label = label, display = is_displayed, media = media, order = order)
            content.fields.append(field)

    for field in forms["text_form"].text_fields:
        media = Media(text = field.text.data)
        save_field(field, media)

    for field in forms["textArea_form"].textArea_fields:
        media = Media(textArea = field.textArea.data)
        save_field(field, media)

    for field in forms["date_form"].date_fields:
        date = field.date.data if field.date.data else None
        media = Media(date = date)
        save_field(field, media)

    for field in forms["link_form"].link_fields:
        media = Media(link = field.link.data)
        save_field(field, media)

    for field in forms["file_form"].file_fields:
        filename, encrypted_filename = save_file(field.file.data, field.filename.data, field.encrypted_filename.data)
        media = Media(filename = filename, 
            encrypted_filename = encrypted_filename, file_type = field.file_type.data) 
        save_field(field, media)

    for field in forms["picture_form"].picture_fields:
        filename, encrypted_filename = save_file(field.picture.data, field.filename.data, field.encrypted_filename.data)
        media = Media(picture = filename, encrypted_filename = encrypted_filename) 
        save_field(field, media)

    for field in forms["number_form"].number_fields:
        data = None
        if field.number.data:
            data = field.number.data
        media = Media(number = data) 
        save_field(field, media)

    #Удаляем старые поля
    old_fields = []
    for id_ in old_fields_id:
        field = Fields.query.filter_by(id = id_).first()
        old_fields.append(field)
    delete_fields(old_fields)


def delete_fields(fields):
    for field in fields:
        if field.media.encrypted_filename:
            os.remove(os.path.join(app.root_path, 'static/files/', field.media.encrypted_filename))
        db.session.delete(field.media)
        db.session.delete(field)


def dynamic_fields(content, fields, is_template):
    #Формы для разных типов полей
    forms = {}
    forms["text_form"] = TextsForm()
    forms["textArea_form"] = TextAreasForm()
    forms["date_form"] = DatesForm()
    forms["link_form"] = LinksForm()
    forms["file_form"] = FilesForm()
    forms["picture_form"] = PicturesForm()
    forms["number_form"] = NumbersForm()

    is_validated = all([form.validate_on_submit() for form in forms.values()])

    if request.method == 'GET':
        #Заполняем поля при отображении страницы
        add_and_fill_fields_to_form(fields, is_template, forms)

    elif is_validated:
        save_fields(content, forms)

    return is_validated, forms
