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


def add_and_fill_fields_to_form(forms, fields, is_template):
    text_validator = [Length(max=50)] if is_template else [Length(max=50), DataRequired()]
    textArea_validator = [Length(max=255)] if is_template else [Length(max=255), DataRequired()]
    date_validator = [validators.Optional()] if is_template else [DataRequired()]
    link_validator = [] if is_template else [DataRequired()] 
    file_validator = [] if is_template else [check_file_label] 
    picture_validator = [FileAllowed(['jpg', 'png','jpeg'])] if is_template else [check_file_label, FileAllowed(['jpg', 'png','jpeg'])]
    number_validator = [check_number] if is_template else [DataRequired(),check_number]
    category_validator = [DataRequired()] if is_template else [DataRequired()]


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
    delattr(CategoryField_template, "category")
    setattr(CategoryField_template, "category", TextField(label =_('Option'), validators=category_validator))
    delattr(CategoryField, "categories")
    setattr(CategoryField, "categories", SelectField(label =_('Categories'), choices = [], validators=category_validator))

    for field in fields:
        media = field.media
        data = {'label_': field.label, 'is_displayed': field.display,"order": field.order}
        if media.text:
            data["text"] = media.text.data
            forms["text_form"].text_fields.append_entry(data)
        elif media.textArea:
            data["textArea"] = media.textArea.data
            forms["textArea_form"].textArea_fields.append_entry(data)
        elif media.link:
            data["link"] = media.link.data 
            forms["link_form"].link_fields.append_entry(data)
        elif media.file:
            data["filename"] = media.file.data
            data["encrypted_filename"] = media.file.encrypted_filename
            data["file_type"] = media.file.file_type
            forms["file_form"].file_fields.append_entry(data)
        elif media.picture:
            data["filename"] = media.picture
            data["encrypted_filename"] = media.encrypted_filename
            forms["picture_form"].picture_fields.append_entry(data)
        elif media.number:
            data["number"] = media.number.data 
            forms["number_form"].number_fields.append_entry(data)
        elif media.date:
            data["date"] = media.date.data 
            forms["date_form"].date_fields.append_entry(data)
        elif media.category:
            if is_template:
                data_list = []
                for value in media.category.values:
                    data_list.append({'category': value})
                data["categories"] = data_list
                
            forms["category_form"].categories_fields.append_entry(data)

def update_categories_fields(forms, fields):
    categories = []
    for field in fields:
        if field.media.category:
            categories.append(field.media.category)
    for i, categories_field in enumerate(forms["category_form"].categories_fields):
        choices = []
        for value in categories[i].values:
            choices.append((value.value,value.value))
        categories_field.categories.choices = choices
        if request.method == 'GET':
            categories_field.categories.data = categories[i].selected_value

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


def save_fields(content, forms, is_template):
    #Записываем id старых полей, чтобы потом удалить в конце этого метода
    old_fields_id = [field.id for field in content.fields] 

    def save_field(field, media):
            label = field.label_.data
            is_displayed = field.is_displayed.data
            order = field.order.data
            field = Fields(label = label, display = is_displayed, media = media, order = order)
            content.fields.append(field)

    for field in forms["text_form"].text_fields:
        text = Text_field(data = field.text.data)
        media = Media(text = text)
        save_field(field, media)

    for field in forms["textArea_form"].textArea_fields:
        textArea = TextArea_field(data = field.textArea.data)
        media = Media(textArea = textArea)
        save_field(field, media)

    for field in forms["date_form"].date_fields:
        date = Date_field(data = field.date.data)
        media = Media(date = date)
        save_field(field, media)

    for field in forms["link_form"].link_fields:
        link = Link_field(data = field.link.data)
        media = Media(link = link)
        save_field(field, media)

    for field in forms["file_form"].file_fields:
        filename, encrypted_filename = save_file(field.file.data, field.filename.data, field.encrypted_filename.data)
        file = File_field(data = filename,
            encrypted_filename = encrypted_filename, file_type = field.file_type.data) 
        media = Media(file = file)            
        save_field(field, media)

    for field in forms["picture_form"].picture_fields:
        filename, encrypted_filename = save_file(field.picture.data, field.filename.data, field.encrypted_filename.data)
        picture = Picture_field(data = filename,
            encrypted_filename = encrypted_filename) 
        media = Media(picture = picture)
        save_field(field, media)

    for field in forms["number_form"].number_fields:
        data = field.number.data if field.number.data else None
        number = Number_field(data = data)
        media = Media(number = number) 
        save_field(field, media)

    for field in forms["category_form"].categories_fields:
        categorical_field = Categorical_field()
        if is_template:
            for category in field.categories:
                value = Categorical_values(value = category.category.data)
                categorical_field.values.append(value)
        else:
            for value in list(dict(field.categories.choices).keys()):
                categorical_field.values.append(Categorical_values(value = value))
            categorical_field.selected_value = field.categories.data
        media = Media(category = categorical_field) 
        save_field(field, media)

    #Удаляем старые поля
    old_fields = []
    for id_ in old_fields_id:
        field = Fields.query.filter_by(id = id_).first()
        old_fields.append(field)
    delete_fields(old_fields)


def delete_fields(fields):
    for field in fields:
        if field.media.file and field.media.file.data:
            os.remove(os.path.join(app.root_path, 'static/files/', field.media.file.encrypted_filename))
        elif field.media.picture and field.media.picture.data:
            os.remove(os.path.join(app.root_path, 'static/files/', field.media.picture.encrypted_filename))
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
    forms["category_form"] = CategoriesForm_template() if is_template else CategoriesForm()
        

    if request.method == 'GET':
        #Заполняем поля при отображении страницы
        add_and_fill_fields_to_form(forms, fields, is_template)
    
    update_categories_fields(forms, fields)
    is_validated = all([form.validate_on_submit() for form in forms.values()])
    
    if is_validated:
        save_fields(content, forms, is_template)

    return is_validated, forms
