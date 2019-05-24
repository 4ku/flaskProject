# Здесь добавлены все функции, связанные с созданиемб редактированием и удалением заданий и шаблонов к ним

from flask import render_template, flash, redirect, url_for, request, session
from flask_login import current_user, login_required

from werkzeug.urls import url_parse
from datetime import datetime
from sqlalchemy import or_
import os
from flask_wtf import FlaskForm
from wtforms import TextAreaField, TextField
from wtforms.fields.html5 import DateField
from shutil import copyfile

from app import app, db
from app.forms import *
from app.models import *

from app.routes import roles_required, encode_filename

# Сохранение данных в fields - массив экземпляров класса Task_media
def save_media(fields, dynamic_form, is_edit, start_ind):
    i = start_ind
    for field in fields:
        form_data = dynamic_form[str(i)].data
        if field.text is not None and form_data:
            field.text = form_data
        if field.textArea is not None and form_data:
            field.textArea = form_data
        elif field.date and form_data:
            field.date = form_data 
        elif field.filename is not None:
            filename, encrypted_filename = "", ""
            # Если добавляем свой файл 
            if form_data:
            # При редактировании - заменяем предшествующий, если был 
                if is_edit and field.filename:
                    os.remove(os.path.join(app.root_path, 'static/files/', field.encrypted_filename))
                file = form_data
                filename, encrypted_filename = encode_filename(file.filename)
                file.save(os.path.join(app.root_path, 'static/files/',  encrypted_filename))
                field.filename = filename
                field.encrypted_filename = encrypted_filename
            # Если хотим оставить файл, который был до этого при редактировании, то ничего не делаем
            # Если же оставляем пустым, то выполняем следущий код - копируем файл шаблона, если этот файл существует
            elif not is_edit and dynamic_form[str(i)].label.text["filename"]:
                src_path = os.path.join(app.root_path, 'static/files/', dynamic_form[str(i)].label.text["encrypted_filename"])
                filename, encrypted_filename = encode_filename(dynamic_form[str(i)].label.text["filename"])
                dst_path = os.path.join(app.root_path, 'static/files/', encrypted_filename)
                copyfile(src_path, dst_path)
                field.filename = filename
                field.encrypted_filename = encrypted_filename
        elif field.link is not None:
            field.link = form_data
        elif field.picture is not None:
            pass
        i+=1

# Создание Task_media по тэгу из списка
def create_media_by_tags(fields):
    media = []
    for field in fields:
        if field == "Text":
            media.append(Task_media(text = ""))
        elif field == "TextArea":
            media.append(Task_media(textArea = ""))
        elif field == "Date":
            media.append(Task_media(date = datetime(1,1,1)))
        elif field == "File":
            media.append(Task_media(filename = ""))
        elif field == "Picture":
            media.append(Task_media(picture = ""))
        elif field == "Link":
            media.append(Task_media(link = ""))
    return media

# Создание динамических полей
def create_fields_to_form(DynamicForm, fields, is_task):
    text_validator = [Length(max=50), DataRequired()] if is_task else [Length(max=50)]
    textArea_validator = [Length(max=140), DataRequired()] if is_task else [Length(max=50)]
    date_validator = [DataRequired()] if is_task else []
    file_validator = [check_file_label] if is_task else []
    link_validator = [DataRequired()] if is_task else []
    picture_validator = [check_file_label] if is_task else []

    for i, field_data in enumerate(fields):
        field = None
        if field_data.text or field_data.text == "":
            field = TextField(label = "Text:", 
                validators=text_validator)
        if field_data.textArea or field_data.textArea == "":
            field = TextAreaField(label = "Text area:", 
                validators=textArea_validator)
        elif field_data.date:
            field = DateField(label = "Date: ", validators=date_validator)
        elif field_data.filename or field_data.filename == "":
            label = {"filename": field_data.filename, "encrypted_filename": field_data.encrypted_filename}
            field = FileField(label = label, validators=file_validator)
        elif field_data.link:
            field = TextField(label = "Link:", 
                validators=link_validator)
        elif field_data.picture:
            label = {"filename": field_data.picture, "encrypted_filename": field_data.encrypted_filename}
            field = FileField(label = label, validators=picture_validator)
        setattr(DynamicForm, str(i), field)

# Копирование Task_media - используется пока только при создании задания (create_task)
def copy_media(fields, media):
    for field in fields:
        if field.text is not None:
            media.append(Task_media(text = field.text))
        elif field.textArea is not None:
            media.append(Task_media(textArea = field.textArea))
        elif field.date:
            media.append(Task_media(date = field.date))
        elif field.filename is not None:
            media.append(Task_media(filename = field.filename,
                     encrypted_filename = field.encrypted_filename))

# Заполнение динамических полей данными
def fill_data(dynamic_form, fields):
    for i, field_data in enumerate(fields):
        if field_data.text:
            dynamic_form[str(i)].data = field_data.text
        elif field_data.textArea:
            dynamic_form[str(i)].data = field_data.textArea
        elif field_data.date:
            dynamic_form[str(i)].data = field_data.date
        elif field_data.filename:
            dynamic_form[str(i)].label = {"filename": field_data.filename, "encrypted_filename": field_data.encrypted_filename}


#-------------------------------------------------------
# Функции, связанные с task
#-------------------------------------------------------

# Данная функция используется при создании задания и его редактирования
def prepare_task(task, is_edit):
    class DynamicForm(FlaskForm):
        pass

    # Создание новых полей для задания
    create_fields_to_form(DynamicForm, task.media, True)

    dynamic_form = DynamicForm()
    form = TaskForm_edit() if is_edit else TaskForm_create()

    # Создание списка кто создаёт задание и кто принимает это задание
    assigners = User.query.join(User.roles).filter(or_(Role.name == "Admin", Role.name == "Usual")).all()
    assigner_choices =  [ (user.id, user.username) for user in assigners ]

    acceptors = User.query.join(User.roles).filter(or_(Role.name == "Client", Role.name == "Usual")).all()
    acceptor_choices = [ (user.id, user.username) for user in acceptors ]
    # Удаление текущего пользователя из списка
    if (current_user.id, current_user.username) in acceptor_choices:
        acceptor_choices.remove((current_user.id, current_user.username))
        
    form.acceptor.choices = acceptor_choices    
    if is_edit:
        form.assigner.choices = assigner_choices
    
    # Если нажата кнопка submit, то заносим данные в БД
    if form.validate_on_submit() and dynamic_form.validate():
        # Назначение, кто создал задание и кому оно адресовано
        assigner = None
        if is_edit:
            assigner = User.query.filter_by(id = int(form.assigner.data)).first()
        else:
            assigner = current_user
        task.assigner = assigner
        task.assigner_id = assigner.id

        acceptor = User.query.filter_by(id = int(form.acceptor.data)).first()
        task.acceptor = acceptor
        task.acceptor_id = acceptor.id

        if is_edit:
            task.status = form.status.data

        # Сохранение task.media в БД
        save_media(task.media, dynamic_form, is_edit, 0)    

        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('login'))
    elif request.method == 'GET':
        # Заполнение полей существующими данными
        fill_data(dynamic_form, task.media)

        if is_edit:
            form.acceptor.data = task.acceptor.id
            form.assigner.data = task.assigner.id
            form.status.data = task.status

    title = "Edit task" if is_edit else "Create task"
    return render_template('create_or_edit_task.html', title=title, form=form, 
        extra_fields = dynamic_form, edit_task = is_edit)

# Сразу же после выбора шаблона, можем создать задание по выбранному шаблону
@app.route('/create_task/<template_id>', methods=['GET', 'POST'])
@roles_required(['Admin', 'Usual'])
def create_task(template_id):
    fields = Task_templates.query.filter_by(id = template_id).first().fields
    task = Task()
    # Копируем task_media из fields, которые взяли из шаблона, в новый Task
    copy_media(fields, task.media)
    db.session.add(task)    
    return prepare_task(task, False)

@app.route('/edit_task/<task_id>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def edit_task(task_id):
    task = Task.query.filter_by(id = task_id).first()
    return prepare_task(task, True)

@app.route('/delete_task/<task_id>')
@roles_required(['Admin'])
def delete_task(task_id):
    task = Task.query.filter(Task.id == task_id).first()
    for media in task.media:
        if media.filename:
            os.remove(os.path.join(app.root_path, 'static/files/', media.encrypted_filename))
        db.session.delete(media)
    db.session.delete(task)
    db.session.commit()
    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for('all_users')
    return redirect(next_page)

#-------------------------------------------------------
# Функции, связанные с template
#-------------------------------------------------------

# Используется при создании шаблона и его редактировани
def prepare_template(template, is_edit):
    class DynamicForm(FlaskForm):
        pass

    extra_fields = []
    if 'fields' in session:
        extra_fields = session['fields']
    extra_fields_objects = create_media_by_tags(extra_fields)
    fields_objects = [field for field in template.fields] + extra_fields_objects
    
    # Создание полей для шаблона
    create_fields_to_form(DynamicForm, fields_objects, False)

    form = TemplateForm()
    add_field_form = AddFieldForm()
    dynamic_form = DynamicForm()

    # Если нажата кнопка добавить задание
    if form.submit.data and form.validate_on_submit() and (len(fields_objects)) > 0:
        session['fields'] = []
        template.name = form.name.data
        save_media(template.fields, dynamic_form, is_edit, 0)
        
        #Обновление полей, которые были созданы дополнительно
        save_media(extra_fields_objects, dynamic_form, is_edit, len(template.fields))
        for field in extra_fields_objects:
            template.fields.append(field)

        db.session.commit()
        return redirect(url_for('templates'))

    # Если нажата кнопка создания поля
    elif add_field_form.add_field.data and add_field_form.validate_on_submit():
        if "fields" not in session:
            session['fields'] = []
        session['fields'].append(add_field_form.fields_list.data) 
        return redirect(request.referrer)

    elif request.method == 'GET' and is_edit:
        # Заполнение полей существующими данными
        if template.name:
            form.name.data = template.name
        fill_data(dynamic_form, template.fields)

    title, template_id = None, None
    if is_edit:
        title = "Edit template"
        template_id = template.id
    else:
        title = "Create template"
        template_id = -1

    return render_template("create_or_edit_template.html", title= title, 
        form=form, add_field_form = add_field_form, 
        extra_fields = dynamic_form, template_id = template_id)

# Создание шаблона
@app.route('/create_new_template', methods=['GET', 'POST'])
@roles_required(['Admin'])
def create_new_template():
    template = Task_templates()
    db.session.add(template)
    return prepare_template(template, False)

@app.route('/edit_template/<template_id>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def edit_template(template_id):
    template = Task_templates.query.filter_by(id = template_id).first()
    return prepare_template(template, True)

# Немножко говнокода (хз как нормально реализовать удаление одного поля)
@app.route('/delete_field_in_template/', methods=['GET', 'POST'])
@roles_required(['Admin'])
def delete_field_in_template():
    field_id  = request.args.get('field_id', 1, type = int)
    template_id  = request.args.get('template_id',  1, type = int)
    template = Task_templates.query.filter_by(id = template_id).first()
    length = len(template.fields) if template is not None else 0
    if template_id!=-1 and field_id < length:
        for i, field in enumerate(template.fields):
            if i == field_id:
                db.session.delete(field)
                db.session.commit()
    else:
        del session['fields'][int(field_id)-length]
    return redirect(request.referrer)

@app.route('/delete_template/<template_id>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def delete_template(template_id):
    template = Task_templates.query.filter_by(id = template_id).first()
    #Удаляем все файлы, которые принадлежат этому шаблону
    for media in template.fields:
        if media.filename:
            os.remove(os.path.join(app.root_path, 'static/files/', media.encrypted_filename))
        db.session.delete(media)
    db.session.delete(template)
    db.session.commit()
    return redirect(url_for("templates"))

