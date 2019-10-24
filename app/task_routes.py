# Здесь добавлены все функции, связанные с созданиемб редактированием и удалением заданий и шаблонов к ним

from flask import render_template, flash, redirect, url_for, request, session
from flask_login import current_user, login_required
from flask_babel import _, lazy_gettext as _l
from werkzeug.urls import url_parse
from wtforms import validators
from datetime import datetime
from sqlalchemy import or_
import os
from shutil import copyfile

from app import app, db
from app.forms import *
from app.models import *
import re

from app.routes import roles_required, encode_filename

# # Копирование Fields - используется пока только при создании задания (create_task)
# def copy_fields(fields, task_fields):
#     for field in fields:
#         media = None
#         if field.media.text is not None:
#            media = Media(text = field.media.text)
#         elif field.media.textArea is not None:
#            media = Media(textArea = field.media.textArea)
#         elif field.media.date:
#            media = Media(date = field.media.date)
#         elif field.media.filename is not None:
#            media = Media(filename = field.media.filename,
#                      encrypted_filename = field.media.encrypted_filename)
#         elif field.media.link is not None:
#            media = Media(link = field.media.link)
#         elif field.media.picture is not None:
#            media = Media(picture = field.media.picture,
#                      encrypted_filename = field.media.encrypted_filename)
#         copied_field = Fields(label = field.label, display = field.display, media = media)
#         task_fields.append(copied_field)


#_____________________________________________
#            Fields - Поля
#---------------------------------------------

def add_and_fill_fields_to_form(fields, text_form, textArea_form, is_task):
    text_validator = [Length(max=50), DataRequired()] if is_task else [Length(max=50)]
    textArea_validator = [Length(max=255), DataRequired()] if is_task else [Length(max=255)]
    # date_validator = [DataRequired()] if is_task else [validators.Optional()]
    # file_validator = [check_file_label] if is_task else []
    # link_validator = [DataRequired()] if is_task else []
    # picture_validator = [FileAllowed(['jpg', 'png','jpeg'])]

    delattr(ExtTextField, "text")
    setattr(ExtTextField, "text", TextField(label = _("Text"), validators = text_validator))
    delattr(ExtTextAreaField, "textArea")
    setattr(ExtTextAreaField, "textArea", TextAreaField(label = _("TextArea"), validators = textArea_validator))
    for field in fields:
        data = None
        field_data = field.media
        if field_data.text is not None:
            data = {'label_': field.label, 'is_displayed': field.display, "text": field_data.text}
            text_form.text_fields.append_entry(data)
        if field_data.textArea is not None:
            data = {'label_': field.label, 'is_displayed': field.display, "textArea": field_data.textArea}
            textArea_form.textArea_fields.append_entry(data)
        # elif field_data.date:
        #     extra_field_name = "date"
        #     extra_field = DateField(label = _("Date"), validators=date_validator, default = field_data.date)
        # elif field_data.filename is not None:
        #     extra_field_name = "filename"
        #     label = {"label": _('File'), "filename": field_data.filename, \
        #         "encrypted_filename": field_data.encrypted_filename}
        #     extra_field = FileField(label = label, validators=file_validator)
        # elif field_data.link is not None:
        #     extra_field_name = "link"
        #     extra_field = TextField(label = _("Link"), 
        #         validators=link_validator, default = field_data.link)
        # elif field_data.picture is not None:
        #     extra_field_name = "picture"
        #     label = {"label": _('Picture'), "filename": field_data.picture, \
        #         "encrypted_filename": field_data.encrypted_filename}
        #     extra_field = FileField(label = label, validators=picture_validator)


def save_fields(content, text_form, textArea_form):
    for field in text_form.text_fields:
        label = field.label_.data
        is_displayed = field.is_displayed.data
        media = Media(text = field.text.data)
        field = Fields(label = label, display = is_displayed, media = media)
        content.fields.append(field)

    for field in textArea_form.textArea_fields:
        label = field.label_.data
        is_displayed = field.is_displayed.data
        media = Media(textArea = field.textArea.data)
        field = Fields(label = label, display = is_displayed, media = media)
        content.fields.append(field)


def delete_fields(fields):
    for field in fields:
        if field.media.encrypted_filename:
            os.remove(os.path.join(app.root_path, 'static/files/', field.media.encrypted_filename))
        db.session.delete(field.media)
        db.session.delete(field)



#_____________________________________________
#            Templates - Шаблоны
#---------------------------------------------

def process_template(template, is_edit):
    add_field_form = AddFieldForm()
    form = TemplateForm()

    #Формы для разных типов полей
    text_form = TextsForm()
    textArea_form = TextAreasForm()

    if request.method == 'GET':
        #Заполняем поля при отображении страницы
        add_and_fill_fields_to_form(template.fields, text_form, textArea_form, False)
        form.name.data = template.name
        

    elif form.validate_on_submit():
        # Сохраняем данные в БД
        template.name = form.name.data
        if is_edit:
            delete_fields(template.fields)
        save_fields(template, text_form, textArea_form)
        if not is_edit:
            db.session.add(template) 
        db.session.commit()
        return redirect(url_for('task_templates'))

        
    return render_template("create_or_edit_task_template.html", 
            add_field_form = add_field_form, form = form, 
                text_form = text_form, textArea_form = textArea_form, is_template = False)

# Создание шаблона
@app.route('/create_task_template', methods=['GET', 'POST'])
@roles_required(['Admin'])
def create_task_template():
    template = Task_templates()
    return process_template(template, False)


@app.route('/edit_task_template/<template_id>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def edit_task_template(template_id):
    template = Task_templates.query.filter_by(id = template_id).first()
    return process_template(template, True)


@app.route('/delete_task_template/<template_id>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def delete_task_template(template_id):
    template = Task_templates.query.filter_by(id = template_id).first()
    delete_fields(template.fields)
    db.session.delete(template)
    db.session.commit()
    return redirect(url_for("task_templates"))






#_____________________________________________
#            Tasks - Задания
#---------------------------------------------

def process_task(form, task, fields, is_edit):
    #Формы для разных типов полей
    text_form = TextsForm()
    textArea_form = TextAreasForm()


    if request.method == 'GET':
        #Заполняем поля при отображении страницы
        add_and_fill_fields_to_form(fields, text_form, textArea_form, True)
        if is_edit:
            form.status.data = task.status
            form.assigner.data = task.assigner
            form.acceptor.data = task.acceptor
 
    if form.validate_on_submit():
        if is_edit:
            assigner = form.assigner.data
        else:
            assigner = current_user
        task.assigner = assigner
        task.assigner_id = assigner.id

        acceptor = form.acceptor.data
        task.acceptor = acceptor
        task.acceptor_id = acceptor.id

        if is_edit:
            task.status = form.status.data

        if is_edit:
            delete_fields(task.fields)
        save_fields(task, text_form, textArea_form)

        if not is_edit:
            db.session.add(task)    
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('login'))
    return render_template("create_or_edit_task.html", form = form, is_edit = is_edit,
                text_form = text_form, textArea_form = textArea_form, is_template = False)


@app.route('/create_task/<template_id>', methods=['GET', 'POST'])
@roles_required(['Admin', 'Usual'])
def create_task(template_id):
    task = Tasks()
    fields = Task_templates.query.filter_by(id = template_id).first().fields
    form = TaskForm_create()

    return process_task(form, task, fields, False)

    
@app.route('/edit_task/<task_id>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def edit_task(task_id):
    task = Tasks.query.filter_by(id = task_id).first()
    form = TaskForm_edit()
    return process_task(form, task, task.fields, True)


@app.route('/delete_task/<task_id>')
@roles_required(['Admin'])
def delete_task(task_id):
    task = Tasks.query.filter(Tasks.id == task_id).first()
    delete_fields(task.fields)
    db.session.delete(task)
    db.session.commit()
    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for('all_users')
    return redirect(next_page)






def save_file(form_field, field_filename, field_encrypted_filename, is_edit):
    filename, encrypted_filename = "", ""
    # Если добавляем свой файл 
    if form_field.data:
    # При редактировании - заменяем предшествующий, если был 
        if is_edit and field_filename:
            os.remove(os.path.join(app.root_path, 'static/files/', field_encrypted_filename))
        file = form_field.data
        filename, encrypted_filename = encode_filename(file.filename)
        file.save(os.path.join(app.root_path, 'static/files/',  encrypted_filename))
        return filename, encrypted_filename
    # Если хотим оставить файл, который был до этого при редактировании, то ничего не делаем
    # Если же оставляем пустым, то выполняем следущий код - копируем файл шаблона, если этот файл существует
    elif not is_edit and field_filename:
        src_path = os.path.join(app.root_path, 'static/files/', field_encrypted_filename)
        filename, encrypted_filename = encode_filename(field_filename)
        dst_path = os.path.join(app.root_path, 'static/files/', encrypted_filename)
        copyfile(src_path, dst_path)
        return filename, encrypted_filename
    return field_filename, field_encrypted_filename
