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


def process_template(template, is_edit):
    add_field_form = AddFieldForm()
    form = TemplateForm()

    text_form, textArea_form, date_form, link_form, \
         file_form, picture_form = dynamic_fields(template, template.fields, False)

    if request.method == 'GET':
        #Заполняем поля при отображении страницы
        form.name.data = template.name
        
    elif form.validate_on_submit() :
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




