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

# FIELDS_NAME = ['text','textArea','date','encrypted_filename','link','picture']

# Данная функция используется при создании задания и его редактирования
def prepare_task(task, is_edit):
    class DynamicForm(FlaskForm):
        pass

    # Создание новых полей для задания
    for i, field_data in enumerate(task.media):
        field = None
        if field_data.text or field_data.text == "":
            field = TextField(label = "Text:", 
                validators=[Length(max=50), DataRequired()])
        if field_data.textArea or field_data.textArea == "":
            field = TextAreaField(label = "Text area:", 
                validators=[Length(max=140), DataRequired()])
        elif field_data.date:
            field = DateField(label = "Date: ", validators=[DataRequired()])
        elif field_data.filename or field_data.filename == "":
            label = {"filename": field_data.filename, "encrypted_filename": field_data.encrypted_filename}
            field = FileField(label = label, validators=[check_file_label])
        elif field_data.link:
            field = TextField(label = "Link:", 
                validators=[Length(), DataRequired()])
        elif field_data.picture:
            label = {"filename": field_data.picture, "encrypted_filename": field_data.encrypted_filename}
            field = FileField(label = label, validators=[check_file_label])
        setattr(DynamicForm, str(i), field)

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

        # Сохранение данных в task.media - массив экземпляров класса Task_media
        for i, field in enumerate(task.media):
            if field.text is not None:
                field.text = dynamic_form[str(i)].data
            if field.textArea is not None:
                field.textArea = dynamic_form[str(i)].data
            elif field.date:
                field.date = dynamic_form[str(i)].data 
            elif field.filename is not None:
                # Если добавляем свой файл (при редактировании - заменяем предшествующий)
                filename, encrypted_filename = "", ""
                if dynamic_form[str(i)].data:
                    if is_edit:
                        os.remove(os.path.join(app.root_path, 'static/files/', field.encrypted_filename))
                    file = dynamic_form[str(i)].data
                    filename, encrypted_filename = encode_filename(file.filename)
                    file.save(os.path.join(app.root_path, 'static/files/',  encrypted_filename))
                # Если хотим оставить файл, который был до этого при редактировании, то ничего не делаем
                # Если же создаётся задание, то выполняем следущий код - копируем файл шаблона, если этот файл существует
                elif not is_edit and dynamic_form[str(i)].label.text["filename"]:
                    src_path = os.path.join(app.root_path, 'static/files/', dynamic_form[str(i)].label.text["encrypted_filename"])
                    filename, encrypted_filename = encode_filename(dynamic_form[str(i)].label.text["filename"])
                    dst_path = os.path.join(app.root_path, 'static/files/', encrypted_filename)
                    copyfile(src_path, dst_path)
                field.filename = filename
                field.encrypted_filename = encrypted_filename
            elif field.link is not None:
                field.link = dynamic_form[str(i)].data
            elif field.picture is not None:
                pass

        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('login'))
    elif request.method == 'GET':
        # Заполнение полей существующими данными

        for i, field_data in enumerate(task.media):
            if field_data.text:
                dynamic_form[str(i)].data = field_data.text
            if field_data.textArea:
                dynamic_form[str(i)].data = field_data.textArea
            elif field_data.date:
                dynamic_form[str(i)].data = field_data.date
            elif field_data.filename:
                dynamic_form[str(i)].label = {"filename": field_data.filename, "encrypted_filename": field_data.encrypted_filename}

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
    # Копируем task_media из fields в new_fields
    task = Task()
    for field in fields:
        if field.text is not None:
            print(field.text)
            task.media.append(Task_media(text = field.text))
        elif field.textArea is not None:
            print(field.textArea)
            task.media.append(Task_media(textArea = field.textArea))
        elif field.date:
            task.media.append(Task_media(date = field.date))
        elif field.filename is not None:
            task.media.append(Task_media(filename = field.filename,
                     encrypted_filename = field.encrypted_filename))

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


def prepare_template(template, is_edit):
    class DynamicForm(FlaskForm):
        pass

    # fields = []
    # for field in template.fields:
    #     if field.textArea:
    #         fields.append("TextArea")
    #     elif field.date:
    #         fields.append("Date")
    #     elif field.filename or field.filename == "":
    #         fields.append("File")

    extra_fields = []
    if 'fields' in session:
        extra_fields = session['fields']
    extra_fields_objects = []
    for field in extra_fields:
        if field == "Text":
            extra_fields_objects.append(Task_media(text = ""))
        elif field == "TextArea":
            extra_fields_objects.append(Task_media(textArea = ""))
        elif field == "Date":
            date = datetime(1,1,1)
            extra_fields_objects.append(Task_media(date = date))
        elif field == "File":
            extra_fields_objects.append(Task_media(filename = ""))
        elif field == "Picture":
            extra_fields_objects.append(Task_media(picture = ""))
        elif field == "Link":
            extra_fields_objects.append(Task_media(link = ""))
    
    fields_objects = [field for field in template.fields] + extra_fields_objects
    # fields.append()
    
    
    # Создание полей для шаблона
    for i, field_data in enumerate(fields_objects):
        field = None
        if field_data.text or field_data.text == "":
            field = TextField(label = "Text:", 
                validators=[Length(max=50)])
        if field_data.textArea or field_data.textArea == "":
            field = TextAreaField(label = "Text area:", 
                validators=[Length(max=140)])
        elif field_data.date:
            field = DateField(label = "Date: ")
        elif field_data.filename or field_data.filename == "":
            label = {"filename": field_data.filename, "encrypted_filename": field_data.encrypted_filename}
            field = FileField(label = label)
        elif field_data.link:
            field = TextField(label = "Link:", 
                validators=[Length()])
        elif field_data.picture:
            label = {"filename": field_data.picture, "encrypted_filename": field_data.encrypted_filename}
            field = FileField(label = label)
        setattr(DynamicForm, str(i), field)



    # for i, field_label in enumerate(extra_fields):
    #     field = None
    #     if field_label == "Text":
    #         field = TextField(label = "Text:", 
    #             validators=[Length(max=50)])
    #     if field_label == "TextArea":
    #         field = TextAreaField(label = "Text area:", 
    #             validators=[Length(max=140)])
    #     elif field_label == "Date":
    #         field = DateField(label = "Date: ", validators=[])
    #     elif field_label == "File":
    #         field = FileField('Pick a file: ')
    #     setattr(DynamicForm, str(i), field)

    form = TemplateForm()
    add_field_form = AddFieldForm()
    dynamic_form = DynamicForm()

    # Если нажата кнопка добавить задание
    if form.submit.data and form.validate_on_submit() and (len(fields_objects)) > 0:
        session['fields'] = []
        template.name = form.name.data

        # if not is_edit:
        #     template = Task_templates()
        #     if form.name:
        #         template.name = form.name.data
        #     for field in dynamic_form:
        #         if field.type == "TextField":
        #             data = field.data if field.data else ""
        #             template.fields.append(Task_media(text = data))                   
        #         elif field.type == "TextAreaField":
        #             data = field.data if field.data else ""
        #             template.fields.append(Task_media(textArea = data)) 
        #         elif field.type == "DateField":
        #             data = field.data if field.data else datetime(1,1,1)
        #             template.fields.append(Task_media(date = data))
        #         elif field.type == "FileField":
        #             filename, encrypted_filename = "", ""
        #             if field.data:
        #                 file = field.data
        #                 filename, encrypted_filename = encode_filename(file.filename)
        #                 file.save(os.path.join(app.root_path, 'static/files/',  encrypted_filename))
        #             template.fields.append(Task_media(encrypted_filename = encrypted_filename, filename = filename))
        #         db.session.add(template)
        # else:

        # Изменение task.media
        for i, field_data in enumerate(template.fields):
            if field_data.text:
                field_data.text = dynamic_form[str(i)].data
            elif field_data.textArea:
                field_data.textArea = dynamic_form[str(i)].data
            elif field_data.date:
                field_data.date = dynamic_form[str(i)].data 
            elif field_data.filename:
                # Если добавляем свой файл (заменяем предшествующий)
                if dynamic_form[str(i)].data:
                    if is_edit:
                        os.remove(os.path.join(app.root_path, 'static/files/', field_data.encrypted_filename))
                    file = dynamic_form[str(i)].data
                    filename, encrypted_filename = encode_filename(file.filename)
                    field_data.filename = filename
                    field_data.encrypted_filename = encrypted_filename
                    file.save(os.path.join(app.root_path, 'static/files/',  encrypted_filename))
                    field.filename = filename
                    field.encrypted_filename = encrypted_filename
                # Если хотим оставить файл, который был до этого, то ничего не делаем

        i = len(template.fields)
        for field_data in enumerate(extra_fields_objects):
            field_data = field_data[1]
            if field_data.text is not None:
                field_data.text = dynamic_form[str(i)].data
            elif field_data.textArea is not None:
                field_data.textArea = dynamic_form[str(i)].data
            elif field_data.date:
                field_data.date = dynamic_form[str(i)].data 
            elif field_data.filename is not None:
                # Если добавляем свой файл (заменяем предшествующий)
                if dynamic_form[str(i)].data:
                    if is_edit:
                        os.remove(os.path.join(app.root_path, 'static/files/', field_data.encrypted_filename))
                    file = dynamic_form[str(i)].data
                    filename, encrypted_filename = encode_filename(file.filename)
                    field_data.filename = filename
                    field_data.encrypted_filename = encrypted_filename
                    file.save(os.path.join(app.root_path, 'static/files/',  encrypted_filename))
                    field.filename = filename
                    field.encrypted_filename = encrypted_filename
            i+=1
                # Если хотим оставить файл, который был до этого, то ничего не делаем
        for field in extra_fields_objects:
            template.fields.append(field)

        db.session.commit()
        return redirect(url_for('templates'))

    # Если нажата кнопка создания поля
    elif add_field_form.add_field.data and add_field_form.validate_on_submit():
        if "fields" not in session:
            session['fields'] = []
        session['fields'].append(add_field_form.fields_list.data) 
        # field_type = add_field_form.fields_list.data
        # if field_type == "Text":
        #     template.fields.append(Task_media(text = ""))
        # elif field_type == "TextArea":
        #     template.fields.append(Task_media(textArea = ""))
        # elif field_type == "Date":
        #     date = field.data if field.data else datetime(1,1,1)
        #     template.fields.append(Task_media(date = date))
        # elif field_type == "File":
        #     template.fields.append(Task_media(filename = ""))
        # elif field_type == "Picture":
        #     template.fields.append(Task_media(picture = ""))
        # elif field_type == "Link":
        #     template.fields.append(Task_media(link = ""))
        return redirect(request.referrer)

    elif request.method == 'GET' and is_edit:
        for i, field_data in enumerate(template.fields):
            if field_data.text:
                dynamic_form[str(i)].data = field_data.text
            elif field_data.textArea:
                dynamic_form[str(i)].data = field_data.textArea
            elif field_data.date:
                dynamic_form[str(i)].data = field_data.date
            elif field_data.filename:
                dynamic_form[str(i)].label = {"filename": field_data.filename, "encrypted_filename": field_data.encrypted_filename}

    title = None
    if is_edit:
        title = "Edit template"
    else:
        title = "Create template"
    return render_template("create_or_edit_template.html", title= title, 
        form=form, add_field_form = add_field_form, 
        extra_fields = dynamic_form, template_id = template.id)


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
    # fields = []
    # for field in template.fields:
    #     if field.textArea:
    #         fields.append("TextArea")
    #     elif field.date:
    #         fields.append("Date")
    #     elif field.filename or field.filename == "":
    #         fields.append("File")
    # session["fields"] = fields
    return prepare_template(template, True)


@app.route('/delete_field_in_template/<field_id>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def delete_field_in_template(field_id):
    del session['fields'][int(field_id)]
    return redirect(request.referrer)

@app.route('/delete_template/<template_id>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def delete_template(template_id):
    template = Task_templates.query.filter_by(id = template_id).first()
    #Удаляем все файлы, которые принадлежат этому шаблону
    for media in template.field:
        if media.filename:
            os.remove(os.path.join(app.root_path, 'static/files/', media.encrypted_filename))
        db.session.delete(media)
    db.session.delete(template)
    db.session.commit()
    return redirect(url_for("templates"))

