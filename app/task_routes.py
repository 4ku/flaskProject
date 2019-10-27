# Здесь добавлены все функции, связанные с созданиемб редактированием и удалением заданий и шаблонов к ним

from flask import render_template, flash, redirect, url_for, request, session
from flask_login import current_user
from flask_babel import _, lazy_gettext as _l
from werkzeug.urls import url_parse

from app import app, db
from app.forms import *
from app.models import *
from app.dynamic_fields import *
from app.routes import roles_required


#_____________________________________________
#            Templates - Шаблоны
#---------------------------------------------

def process_template(template, is_edit):
    form = TemplateForm()
    add_field_form = AddFieldForm()
    
    is_validated, text_form, textArea_form, date_form, link_form, \
         file_form, picture_form = dynamic_fields(template, template.fields, False)

    if request.method == 'GET':
        #Заполняем поля при отображении страницы
        form.name.data = template.name
        
    elif is_validated and form.validate_on_submit() :
        # Сохраняем данные в БД
        template.name = form.name.data
        if not is_edit:        
            db.session.add(template) 
        db.session.commit()
        return redirect(url_for('task_templates'))

    return render_template("create_or_edit_task_template.html", 
            add_field_form = add_field_form, form = form, is_template = True,
                text_form = text_form, textArea_form = textArea_form, date_form = date_form,
                link_form = link_form, file_form = file_form, picture_form = picture_form)

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
    db.session.commit()
    db.session.delete(template)
    db.session.commit()
    return redirect(url_for("task_templates"))


#_____________________________________________
#            Tasks - Задания
#---------------------------------------------

def process_task(form, task, fields, is_edit):
    #Формы для разных типов полей

    is_validated, text_form, textArea_form, date_form, link_form, \
         file_form, picture_form = dynamic_fields(task, fields, True)

    if request.method == 'GET' and is_edit:
        #Заполняем поля при отображении страницы
        form.status.data = task.status
        form.assigner.data = task.assigner
        form.acceptor.data = task.acceptor
 
    elif is_validated and form.validate_on_submit():
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

        if not is_edit:
            db.session.add(task)    
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('login'))
    
    return render_template("create_or_edit_task.html", form = form, is_edit = is_edit,
                text_form = text_form, textArea_form = textArea_form,
                date_form = date_form, link_form = link_form, file_form = file_form, 
                picture_form = picture_form, is_template = False)


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
    db.session.commit()
    db.session.delete(task)
    db.session.commit()
    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for('all_users')
    return redirect(next_page)







