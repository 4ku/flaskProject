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

def add_and_fill_fields_to_form(FieldForm, form, fields, is_task):
    text_validator = [Length(max=50), DataRequired()] if is_task else [Length(max=50)]
    textArea_validator = [Length(max=255), DataRequired()] if is_task else [Length(max=255)]
    date_validator = [DataRequired()] if is_task else [validators.Optional()]
    file_validator = [check_file_label] if is_task else []
    link_validator = [DataRequired()] if is_task else []
    picture_validator = [FileAllowed(['jpg', 'png','jpeg'])]
    for field in fields:
        extra_field_name = None
        extra_field = None
        field_data = field.media
        if field_data.text is not None:
            extra_field_name = "text"
            extra_field = TextField(label = _("Text"), validators=text_validator, default = field_data.text)
        if field_data.textArea is not None:
            extra_field_name = "textArea"
            extra_field = TextAreaField(label = _("Text area"), 
                validators=textArea_validator, default = field_data.textArea)
        elif field_data.date:
            extra_field_name = "date"
            extra_field = DateField(label = _("Date"), validators=date_validator, default = field_data.date)
        elif field_data.filename is not None:
            extra_field_name = "filename"
            label = {"label": _('File'), "filename": field_data.filename, \
                "encrypted_filename": field_data.encrypted_filename}
            extra_field = FileField(label = label, validators=file_validator)
        elif field_data.link is not None:
            extra_field_name = "link"
            extra_field = TextField(label = _("Link"), 
                validators=link_validator, default = field_data.link)
        elif field_data.picture is not None:
            extra_field_name = "picture"
            label = {"label": _('Picture'), "filename": field_data.picture, \
                "encrypted_filename": field_data.encrypted_filename}
            extra_field = FileField(label = label, validators=picture_validator)
        setattr(FieldForm, extra_field_name, extra_field)
        data = {'label': field.label, 'is_displayed': field.display}
        form.fields.append_entry(data)
        delattr(FieldForm, extra_field_name)

def save_fields(content):
    fields = []
    forms_names = " ".join([x for x in request.form])
    ind_names = re.compile(r"fields-([\d]+)-([\S]+)").findall(forms_names)
    ind_names = [x for x in ind_names if x[1]!='label']
    idx = [int(x[0]) for x in ind_names]
    field_types = [x[1] for x in ind_names]

    forms_names = " ".join([x for x in request.files])
    ind_names = re.compile(r"fields-([\d]+)-([\S]+)").findall(forms_names)
    idx_files = [int(x[0]) for x in ind_names]
    field_types_files = [x[1] for x in ind_names]

    idx = idx + idx_files
    field_types = field_types + field_types_files
    
    for index, field_type in sorted(zip(idx, field_types)):
        media = None
        value = request.form.get("fields-"+str(index)+"-"+field_type)
        if field_type == "text":
            value = request.form.get("fields-"+str(index)+"-"+field_type) 
            media = Media(text = value)
        elif field_type =="textArea":
            value = request.form.get("fields-"+str(index)+"-"+field_type) 
            media = Media(textArea = value)
        elif field_type =="date":
            value = request.form.get("fields-"+str(index)+"-"+field_type) 
            media = Media(date = value)
        elif field_type =="file":
            media = Media(filename = "", encrypted_filename = "")
        elif field_type =="picture":
            media = Media(picture = "")
        elif field_type =="link":
            value = request.form.get("fields-"+str(index)+"-"+field_type) 
            media = Media(link = value)
        label = request.form.get("fields-"+str(index)+"-label")
        is_displayed = "fields-"+str(index)+"-is_displayed" in request.form 
        field = Fields(label = label, display = is_displayed, media = media)
        content.fields.append(field)
    return fields

def create_dynamic_content(content, form, fields):
    add_and_fill_fields_to_form(FieldForm, form,fields,False)
    if form.validate_on_submit():
        save_fields(content)


@app.route('/create_task/<template_id>', methods=['GET', 'POST'])
@roles_required(['Admin', 'Usual'])
def create_task(template_id):
    
    task = Tasks()
    form = TaskForm_create()
    fields_form = ContentForm()
    is_edit = False
  
    fields = Task_templates.query.filter_by(id = template_id).first().fields
    create_dynamic_content(task, fields_form, fields)

    if request.method == 'GET':
        #QuerySelectField
        acceptors = Users.query.join(Users.roles).filter(or_(Roles.name == "Client", Roles.name == "Usual"), ~Users.roles.any(Roles.name == "God")).all()
        acceptor_choices = [ (user.id, user.email) for user in acceptors ]
        if (current_user.id, current_user.email) in acceptor_choices:
            acceptor_choices.remove((current_user.id, current_user.email))    
        form.acceptor.choices = acceptor_choices  

    elif form.validate_on_submit():
        #QuerySelectField
        assigner = None
        if is_edit:
            assigner = Users.query.filter_by(id = int(form.assigner.data)).first()
        else:
            assigner = current_user
        task.assigner = assigner
        task.assigner_id = assigner.id

        acceptor = Users.query.filter_by(id = int(form.acceptor.data)).first()
        task.acceptor = acceptor
        task.acceptor_id = acceptor.id

        if is_edit:
            task.status = form.status.data

        if not is_edit:
            db.session.add(task)    
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('login'))
    return render_template("create_or_edit_task.html", form = form, fields_form = fields_form)
    



# Создание шаблона
@app.route('/create_task_template', methods=['GET', 'POST'])
@roles_required(['Admin'])
def create_task_template():
    template = Task_templates()
    add_field_form = AddFieldForm()
    form = TemplateForm()
    fields_form = ContentForm()

    if form.validate_on_submit():
        save_fields(template)
        db.session.add(template)
        db.session.commit()
        return redirect(url_for('login'))
        
    return render_template("create_or_edit_task_template.html", 
            add_field_form = add_field_form, form = form, fields_form = fields_form)




















#-------------------------------------------------------
# Все функции, связанные с Media
#-------------------------------------------------------

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

# Сохранение данных в fields - массив экземпляров класса Media
def save_media(fields, dynamic_form, label_form, is_edit, start_ind):
    i = start_ind
    for field in fields:
        form_field = dynamic_form[str(i)]
        if field.text is not None and form_field.data:
            field.text = form_field.data
        if field.textArea is not None and form_field.data:
            field.textArea = form_field.data
        elif field.date and form_field.data:
            field.date = form_field.data 
        elif field.filename is not None:
            field.filename, field.encrypted_filename = save_file(form_field, 
                                field.filename, field.encrypted_filename, is_edit)
        elif field.link is not None:
            field.link = form_field.data
        elif field.picture is not None:
            field.picture, field.encrypted_filename = save_file(form_field, 
                    field.picture, field.encrypted_filename, is_edit)
        if label_form is not None:
            field.label = label_form["label" + str(i)].data
        i+=1

# Создание Media по тэгу из списка
def create_media_by_tags(fields):
    media = []
    for field in fields:
        if field == "Text":
            media.append(Media(text = ""))
        elif field == "TextArea":
            media.append(Media(textArea = ""))
        elif field == "Date":
            media.append(Media(date = datetime(1,1,1)))
        elif field == "File":
            media.append(Media(filename = "", encrypted_filename = ""))
        elif field == "Picture":
            media.append(Media(picture = ""))
        elif field == "Link":
            media.append(Media(link = ""))
    return media




# Копирование Media - используется пока только при создании задания (create_task)
def copy_media(fields, media):
    for field in fields:
        if field.text is not None:
            media.append(Media(text = field.text, label = field.label))
        elif field.textArea is not None:
            media.append(Media(textArea = field.textArea, label = field.label))
        elif field.date:
            media.append(Media(date = field.date, label = field.label))
        elif field.filename is not None:
            media.append(Media(filename = field.filename,
                     encrypted_filename = field.encrypted_filename, label = field.label))
        elif field.link is not None:
            media.append(Media(link = field.link, label = field.label))
        elif field.picture is not None:
            media.append(Media(picture = field.picture,
                     encrypted_filename = field.encrypted_filename, label = field.label))

#-------------------------------------------------------
# Функции, связанные с task
#-------------------------------------------------------





@app.route('/edit_task/<task_id>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def edit_task(task_id):
    task = Tasks.query.filter_by(id = task_id).first()
    return #prepare_task(task, True)

@app.route('/delete_task/<task_id>')
@roles_required(['Admin'])
def delete_task(task_id):
    task = Tasks.query.filter(Tasks.id == task_id).first()
    for media in task.media:
        if media.encrypted_filename:
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

@app.route('/edit_template/<template_id>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def edit_template(template_id):
    template = Task_templates.query.filter_by(id = template_id).first()
    return 1

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
                if field.encrypted_filename:
                    os.remove(os.path.join(app.root_path, 'static/files/', field.encrypted_filename))
                db.session.delete(field)
                db.session.commit()
    else:
        del session[str(template_id)][int(field_id)-length]
    return redirect(request.referrer)

@app.route('/delete_template/<template_id>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def delete_template(template_id):
    template = Task_templates.query.filter_by(id = template_id).first()
    #Удаляем все файлы, которые принадлежат этому шаблону
    for media in template.fields:
        if media.encrypted_filename:
            os.remove(os.path.join(app.root_path, 'static/files/', media.encrypted_filename))
        db.session.delete(media)
    db.session.delete(template)
    db.session.commit()
    return redirect(url_for("task_templates"))

