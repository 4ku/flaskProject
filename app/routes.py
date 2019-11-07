from flask_babel import _, lazy_gettext as _l
from flask import render_template, flash, redirect, url_for, request, session, send_from_directory
from flask_login import current_user, login_user, logout_user, login_manager, login_required
from functools import wraps
from flask import abort
from flask import g
from flask_babel import get_locale


from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy import or_
import os
from PIL import Image
import secrets
from flask_wtf import FlaskForm
from wtforms.fields import Field
from validator_collection import checkers

from app import app, db
from app.forms import *
from app.models import *

# Проверка роли пользователя
def roles_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))

            access = False
            for role in roles:
                for user_role in current_user.roles:
                    if role == user_role.name:
                        access = True
            
            if not access:
                flash(_l('You do not have access to that page. Sorry!'))
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/login')

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user', id=current_user.id))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data) or user.roles[0].name == 'Not confirmed':
            flash(_l('Invalid email or password'))
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('user', id=user.id)
        return redirect(next_page)
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# Регистрация пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('user', id=current_user.id))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Users(email = form.email.data, last_name=form.last_name.data,
            first_name=form.first_name.data)
        user.set_password(form.password.data)
        user.roles.append(Roles(name="Not confirmed"))
        db.session.add(user)
        db.session.commit()
        flash(_l('Wait for administrator register confirmation.'))
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


# Главная страница пользователя, с заданиями, которые он выдал
@app.route('/user/<id>', methods=['GET', 'POST'])
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


#-------------------------------------------------------------
# Админские страницы
#-------------------------------------------------------------

@app.route('/all_users', methods=['GET', 'POST'])
@roles_required(['Admin'])
def all_users():
    all_users = Users.query.filter(Users.id!=current_user.id, ~Users.roles.any(Roles.name == "God")).all()
    return render_template("all_users.html", title = _l("All users"), users = all_users)


@app.route('/all_tasks', methods=['GET', 'POST'])
@roles_required(['Admin'])
def all_tasks():
    return render_template("tasks.html", title = _l("All tasks"),
        tasks = Tasks.query.order_by(Tasks.timestamp.desc()).all())

def save_avatar(user, picture):
    if picture:
        __ , encrypted_filename = encode_filename(picture.filename)
        image = Image.open(picture)
        image.save(os.path.join(app.root_path, 'static/avatars/', encrypted_filename))
        user.avatar_path = encrypted_filename


@app.route('/edit_user/<id>', methods=['GET', 'POST'])
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
@app.route('/delete_user/<user_id>')
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

@app.route('/confirm_user/<id>')
@roles_required(['Admin'])
def confirm_user(id):
    user = Users.query.filter_by(id=id).first()
    user.roles[0].name = "Usual"
    db.session.commit()
    return redirect(url_for("all_users"))


#-------------------------------------------------------------
# Страницы, которые доступны и админу и обычному пользователю 
#-------------------------------------------------------------

# Страница с выбором существующего шаблона задания или создание нового шаблона (создание только для админа)
@app.route('/task_templates', methods=['GET', 'POST'])
@roles_required(['Admin', 'Usual'])
def task_templates():
    templates = Task_templates.query.all()
    return render_template('task_templates.html', templates = templates)


@app.route('/issued_tasks', methods=['GET', 'POST'])
@roles_required(['Admin', 'Usual'])
def issued_tasks():
    tasks = current_user.assign.order_by(Tasks.timestamp.desc()).all()
    return render_template("tasks.html", title=_l('Issued tasks'), tasks = tasks)

#-------------------------------------------------------------
# Доступные всем зарегестрированным пользователям страницы 
#-------------------------------------------------------------

@app.route('/your_tasks', methods=['GET', 'POST'])
@login_required
def your_tasks():
    tasks = current_user.accept.order_by(Tasks.timestamp.desc()).all()
    return render_template("tasks.html", title=_l('My tasks'), tasks = tasks)


#-------------------------------------------------------------
# Функции меню
#-------------------------------------------------------------
@login_required
@app.route('/toolbar_settings', methods=['GET'])
def toolbar_settings():
    return render_template("toolbar_settings.html", title=_l('Toolbar settings'))

# Добавление в верхнее меню нового аттрибута
@app.route('/add_extra_menu_field/')
@login_required
def add_extra_menu_field():
    name  = request.args.get('name', None)
    current_user.extra_menu_fields.append(Menu_fields(link = request.referrer, name = name))
    db.session.commit()
    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for('login')
    return redirect(next_page)

@app.route('/rename_link/<link_id>',methods=['GET', 'POST'])
@login_required
def rename_menu_field(link_id):
    link = Menu_fields.query.filter_by(id = link_id).first()
    form = MenuForm()
    if form.validate_on_submit():
        link.name = form.name.data
        db.session.commit()
        return redirect(url_for("toolbar_settings"))
    elif request.method == 'GET':
        form.name.data = link.name
    return render_template("rename_link.html", title=_l('Edit link'), form = form)

@app.route('/delete_link/<link_id>')
@login_required
def delete_menu_field(link_id):
    Menu_fields.query.filter_by(id = link_id).delete()
    db.session.commit()
    return redirect(url_for("toolbar_settings"))

# -------------------------
# Просто вспомогательные функции
# ------------------------

# добавление http перед ссылкой, если этого нет
def append_http(link):
    if not (link.startswith("https://") or link.startswith("http://")):
        link = "http://" + link
    return link

# Проверка, является ли текст ссылкой
def is_link(link):
    return checkers.is_url(append_http(link))

def get_sections():
    return Sections.query.all()

app.jinja_env.globals.update(is_link = is_link)
app.jinja_env.globals.update(append_http = append_http)
app.jinja_env.globals.update(get_sections = get_sections)
app.jinja_env.globals.update(now = datetime.utcnow)


def encode_filename(filename):
    random_hex = secrets.token_hex(8)
    filename = secure_filename(filename)
    __, f_ext = os.path.splitext(filename)
    encrypted_filename = random_hex + f_ext
    return (filename, encrypted_filename)

# Скачивание файла
@app.route('/uploads/<path:filename>')
@login_required
def download_file(filename):
    upload_folder = os.path.join(app.root_path, 'static/files/')
    return send_from_directory(upload_folder, filename, as_attachment=True)

@app.route("/change_language/<language>")
def change_language(language):
    session["CURRENT_LANGUAGE"] = language
    return redirect(request.referrer)

# Обновление времени последнего запроса пользователя на сайте
@app.before_request
def before_request():
    g.locale = str(get_locale())
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/all_documents',methods=['GET', 'POST'])
@login_required
def all_documents():
    media = Media.query.all()
    files = []
    for field in media:
        if field.filename:
            files.append(field)
    return render_template("all_documents.html", files = files)

    
@app.route('/profile_template',methods=['GET', 'POST'])
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
from app.task_routes import delete_task
from app.dynamic_fields import *






