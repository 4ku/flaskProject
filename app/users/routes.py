from flask_babel import _, lazy_gettext as _l
from flask import render_template, flash, redirect, url_for, request, session
from flask_login import current_user, login_required
from flask import abort

from werkzeug.urls import url_parse
from sqlalchemy import or_
import os
from PIL import Image
from flask_wtf import FlaskForm

from app.routes import roles_required

from app import app, db
from app.users import bp
from app.users.forms import *
from app.models import *



# Главная страница пользователя, с заданиями, которые он выдал
@bp.route('/user/<id>', methods=['GET', 'POST'])
@login_required
def user(id):
    user = Users.query.filter_by(id=id).first_or_404()
    user_roles = [role.name for role in user.roles]
    if "God" in user_roles and current_user.id != user.id:
        return abort(404)
    tasks = Tasks.query.filter(or_(Tasks.assigner_id == user.id, 
        Tasks.acceptor_id == user.id)).order_by(Tasks.timestamp.desc()).all()
    return render_template('user.html', title = user.last_name+" "+ user.first_name, 
        user=user, tasks = tasks)


@bp.route('/all_users', methods=['GET', 'POST'])
@roles_required(['Admin'])
def all_users():
    all_users = Users.query.filter(Users.id!=current_user.id, ~Users.roles.any(Roles.name == "God")).all()
    return render_template("all_users.html", title = _l("All users"), users = all_users)


def save_avatar(user, picture):
    if picture:
        __ , encrypted_filename = encode_filename(picture.filename)
        image = Image.open(picture)
        image.save(os.path.join(app.root_path, 'static/avatars/', encrypted_filename))
        user.avatar_path = encrypted_filename


@bp.route('/edit_user/<id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    is_admin = (current_user.roles[0].name == "Admin")
    user = Users.query.filter_by(id=id).first()
    
    print(current_user.id)
    if not is_admin and current_user.id != user.id:
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('all_users')
        return redirect(next_page)

    if is_admin:
        form = EditProfileForm_Admin(user.email)
    else:
        form = EditProfileForm()

    if user.profile:
        profile = user.profile
        fields = profile.fields
    else:
        profile = Profiles()
        profile_template = Profile_template.query.filter_by(id=1).first()
        fields = profile_template.fields

    is_validated, dynamic_forms = dynamic_fields(profile, fields, False)

    if request.method == 'GET' and is_admin:
        # Предзаполнение полей
        form.email.data = user.email
        form.role_list.data = user.roles[0].name

    elif is_validated and form.validate_on_submit():
        save_avatar(user, form.picture.data)
        if is_admin:
            user.email = form.email.data
            user.roles[0].name = form.role_list.data
            
        if not user.profile:
            user.profile = profile
            db.session.add(profile)
        db.session.commit()
        flash(_l('Your changes have been saved.'))
    
    return render_template('edit_user.html', title=_l('Edit Profile'),
        form=form, user = user, is_template = False, dynamic_forms = dynamic_forms)


# --- Удаление пользователя и заданий ----
@bp.route('/delete_user/<user_id>')
@roles_required(['Admin'])
def delete_user(user_id):
    user = Users.query.filter_by(id=user_id).first()

    # Удаление аватарки
    if user.avatar_path:
        os.remove(os.path.join(app.root_path, 'static/avatars/', user.avatar_path))

    #Удаление всех заданий пользователя
    acceptor_tasks = Tasks.query.filter(Tasks.acceptor_id == user.id).all()
    assigner_tasks = Tasks.query.filter(Tasks.assigner_id == user.id).all()
    for task in acceptor_tasks:
        delete_task(task.id)
    for task in assigner_tasks:
        delete_task(task.id)
    
    Users.query.filter_by(id=user_id).delete()
    db.session.commit()
    return redirect(url_for("all_users"))

@bp.route('/confirm_user/<id>')
@roles_required(['Admin'])
def confirm_user(id):
    user = Users.query.filter_by(id=id).first()
    user.roles[0].name = "Usual"
    db.session.commit()
    return redirect(url_for("all_users"))


@bp.route('/profile_template',methods=['GET', 'POST'])
@roles_required(['Admin'])
def profile_template():

    class TemplateProfileForm(FlaskForm):
        submit = SubmitField(_l('Submit'))

    template = Profile_template.query.filter_by(id=1).first()
    form = TemplateProfileForm()
    add_field_form = AddFieldForm()
    
    is_validated, dynamic_forms = dynamic_fields(template, template.fields, False)

    if is_validated:
        db.session.commit()

    return render_template("profile_template.html", add_field_form = add_field_form, 
        form = form, is_template = True, dynamic_forms = dynamic_forms)

# delete_task нужен в delete_user
from app.tasks.routes import delete_task
from app.dynamic_fields.dynamic_fields import *