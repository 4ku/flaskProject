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

from app.routes import roles_required, encode_filename


from app.task_routes import copy_media, create_media_by_tags, save_file,save_media,create_fields_to_form,fill_data


# Данная функция используется при создании задания и его редактирования
def prepare_post(post, is_edit):
    class DynamicForm(FlaskForm):
        pass

    # Создание новых полей для задания
    create_fields_to_form(DynamicForm, None, post.media, True)
    dynamic_form = DynamicForm()

    
    form = PostForm_edit() if is_edit else PostForm_create()

    # Создание списка кто создаёт задание и кто принимает это задание
    assigners = Users.query.join(Users.roles).filter(or_(Roles.name == "Admin", Roles.name == "Usual"), ~Users.roles.any(Roles.name == "God")).all()
    assigner_choices =  [ (user.id, user.email) for user in assigners ]
 
    if is_edit:
        form.assigner.choices = assigner_choices
    

    # Если нажата кнопка submit, то заносим данные в БД
    if form.validate_on_submit() and dynamic_form.validate():
        # Назначение, кто создал задание и кому оно адресовано
        author = None
        if is_edit:
            author = Users.query.filter_by(id = int(form.assigner.data)).first()
        else:
            author = current_user
        post.author = author
        # post.assigner_id = assigner.id

        # Сохранение post.media в БД
        save_media(post.media, dynamic_form, None, is_edit, 0)    

        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('login'))
    elif request.method == 'GET':
        # Заполнение полей существующими данными
        fill_data(dynamic_form, None, post.media)

        if is_edit:
            form.assigner.data = post.author.id


    title = _("Edit post") if is_edit else _("Create post")
    return render_template('create_or_edit_task.html', title=title, form=form, 
        extra_fields = zip(dynamic_form, post.media), edit_task = is_edit)

# Сразу же после выбора шаблона, можем создать задание по выбранному шаблону
@app.route('/create_post/<template_id>', methods=['GET', 'POST'])
@roles_required(['Admin', 'Usual'])
def create_post(template_id):
    fields = Post_templates.query.filter_by(id = template_id).first().fields
    post = Posts()
    # Копируем post_media из fields, которые взяли из шаблона, в новый Tasks
    copy_media(fields, post.media)
    db.session.add(post)    
    return prepare_post(post, False)

@app.route('/edit_post/<post_id>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def edit_post(post_id):
    post = Posts.query.filter_by(id = post_id).first()
    return prepare_post(post, True)

@app.route('/delete_post/<post_id>')
@roles_required(['Admin'])
def delete_post(post_id):
    post = Posts.query.filter(Posts.id == post_id).first()
    for media in post.media:
        if media.encrypted_filename:
            os.remove(os.path.join(app.root_path, 'static/files/', media.encrypted_filename))
        db.session.delete(media)
    db.session.delete(post)
    db.session.commit()
    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for('all_users')
    return redirect(next_page)

#-------------------------------------------------------
# Функции, связанные с template
#-------------------------------------------------------

# Используется при создании шаблона и его редактировани
def prepare_post_template(template, is_edit):
    class DynamicForm(FlaskForm):
        pass
    class LabelForm(FlaskForm):
        pass
    template_id = template.id if is_edit else -1
    extra_fields = []
    if "post"+str(template_id) in session:
        extra_fields = session["post"+str(template_id)]
    extra_fields_objects = create_media_by_tags(extra_fields)
    fields_objects = [field for field in template.fields] + extra_fields_objects
    
    # Создание полей для шаблона
    create_fields_to_form(DynamicForm, LabelForm, fields_objects, False)

    form = TemplateForm()
    add_field_form = AddFieldForm()
    dynamic_form = DynamicForm()
    label_form = LabelForm()

    # Если нажата кнопка добавить задание
    if form.submit.data and form.validate_on_submit() and dynamic_form.validate() \
        and dynamic_form.validate() and (len(fields_objects)) > 0:
        session["post"+str(template_id)] = []
        template.name = form.name.data
        save_media(template.fields, dynamic_form, label_form, is_edit, 0)
        
        #Обновление полей, которые были созданы дополнительно
        save_media(extra_fields_objects, dynamic_form, label_form, is_edit, len(template.fields))
        for field in extra_fields_objects:
            template.fields.append(field)

        db.session.commit()
        return redirect(url_for('post_templates'))

    # Если нажата кнопка создания поля
    elif add_field_form.add_field.data and add_field_form.validate_on_submit():
        if "post"+str(template_id) not in session:
            session["post"+str(template_id)] = []
        session["post"+str(template_id)].append(add_field_form.fields_list.data) 
        return redirect(request.referrer)

    elif request.method == 'GET' and is_edit:
        # Заполнение полей существующими данными
        if template.name:
            form.name.data = template.name
        fill_data(dynamic_form, label_form, template.fields)

    title = _l("Edit template") if is_edit else _l("Create template")

    return render_template("create_or_edit_template.html", title= title, 
        form=form, add_field_form = add_field_form, 
        extra_fields = zip(dynamic_form, label_form), template_id = template_id)

# Создание шаблона
@app.route('/create_new_post_template', methods=['GET', 'POST'])
@roles_required(['Admin'])
def create_new_post_template():
    template = Post_templates()
    db.session.add(template)
    return prepare_post_template(template, False)

@app.route('/edit_post_template/<template_id>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def edit_post_template(template_id):
    template = Post_templates.query.filter_by(id = template_id).first()
    return prepare_post_template(template, True)

# Немножко говнокода (хз как нормально реализовать удаление одного поля)
@app.route('/delete_field_in_post_template/', methods=['GET', 'POST'])
@roles_required(['Admin'])
def delete_field_in_post_template():
    field_id  = request.args.get('field_id', 1, type = int)
    template_id  = request.args.get('template_id',  1, type = int)
    template = Post_templates.query.filter_by(id = template_id).first()
    length = len(template.fields) if template is not None else 0
    if template_id!=-1 and field_id < length:
        for i, field in enumerate(template.fields):
            if i == field_id:
                if field.encrypted_filename:
                    os.remove(os.path.join(app.root_path, 'static/files/', field.encrypted_filename))
                db.session.delete(field)
                db.session.commit()
    else:
        del session["post"+str(template_id)][int(field_id)-length]
    return redirect(request.referrer)

@app.route('/delete_post_template/<template_id>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def delete_post_template(template_id):
    template = Post_templates.query.filter_by(id = template_id).first()
    #Удаляем все файлы, которые принадлежат этому шаблону
    for media in template.fields:
        if media.encrypted_filename:
            os.remove(os.path.join(app.root_path, 'static/files/', media.encrypted_filename))
        db.session.delete(media)
    db.session.delete(template)
    db.session.commit()
    return redirect(url_for("post_templates"))

