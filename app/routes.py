from flask import render_template, flash, redirect, url_for, request, session, send_from_directory
from flask_login import current_user, login_user, logout_user, login_manager, login_required
from functools import wraps

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
                flash('You do not have access to that page. Sorry!')
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
        return redirect(url_for('user', username=current_user.username))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('user', username=user.username)
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
        return redirect(url_for('user', username=current_user.username))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, email_confirmed_at=datetime.utcnow() )
        user.set_password(form.password.data)
        user.roles.append(Role(name=form.user_role.data))
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


# Главная страница пользователя, с заданиями, которые он выдал
@app.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    tasks = Task.query.filter(or_(Task.assigner_id == user.id, 
        Task.acceptor_id == user.id)).order_by(Task.timestamp.desc()).all()
    return render_template('user.html', title = user.username, user=user, 
        tasks = tasks)


#-------------------------------------------------------------
# Админские страницы
#-------------------------------------------------------------

@app.route('/all_users', methods=['GET', 'POST'])
@roles_required(['Admin'])
def all_users():
    all_users = User.query.filter(User.username!=current_user.username).all()
    return render_template("all_users.html", title = "All users", users = all_users)


@app.route('/all_tasks', methods=['GET', 'POST'])
@roles_required(['Admin'])
def all_tasks():
    return render_template("tasks.html", title = "All tasks",
        tasks = Task.query.order_by(Task.timestamp.desc()).all())


@app.route('/edit_user_admin/<username>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def edit_user_admin(username):
    user = User.query.filter_by(username=username).first()
    form = EditProfileForm_Admin(user.username)
    if form.validate_on_submit():
        if form.picture.data:
            _ , encrypted_filename = encode_filename(form.picture.data.filename)
            image = Image.open(form.picture.data)
            image.save(os.path.join(app.root_path, 'static/avatars/', encrypted_filename))
            user.avatar_path = encrypted_filename
        user.username = form.username.data
        user.roles[0] = (Role(name=form.role_list.data))
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_user_admin', username = form.username.data))
    elif request.method == 'GET':
        # Предзаполнение полей
        form.username.data = user.username
        form.role_list.data = user.roles[0].name

    return render_template('edit_user.html', title='Edit Profile',
                           form=form, user = user)


# Такая же функция, только для обычных пользователей
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        if form.picture.data:
            _ , encrypted_filename = encode_filename(form.picture.data.filename)
            image = Image.open(form.picture.data)
            image.save(os.path.join(app.root_path, 'static/avatars/', encrypted_filename))
            current_user.avatar_path = encrypted_filename
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    return render_template('edit_user.html', title='Edit Profile',
                           form=form, user = current_user)

# --- Удаление пользователя и заданий ----
@app.route('/delete_user/<user_id>')
@roles_required(['Admin'])
def delete_user(user_id):

    user = User.query.filter_by(id=user_id).first()

    # Удаление аватарки
    if user.avatar_path:
        os.remove(os.path.join(app.root_path, 'static/avatars/', user.avatar_path))

    #Удаление всех заданий пользователя
    acceptor_tasks = Task.query.filter(Task.acceptor_id == user.id).all()
    assigner_tasks = Task.query.filter(Task.assigner_id == user.id).all()
    for task in acceptor_tasks:
        delete_task(task.id)
    for task in assigner_tasks:
        delete_task(task.id)
    
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    return redirect(url_for("all_users"))

#-------------------------------------------------------------
# Страницы, которые доступны и админу и обычному пользователю 
#-------------------------------------------------------------

# Страница с выбором существующего шаблона задания или создание нового шаблона (создание только для админа)
@app.route('/templates', methods=['GET', 'POST'])
@roles_required(['Admin', 'Usual'])
def templates():
    templates = Task_templates.query.all()
    return render_template('templates.html', templates = templates)


@app.route('/issued_tasks', methods=['GET', 'POST'])
@roles_required(['Admin', 'Usual'])
def issued_tasks():
    tasks = current_user.assign.order_by(Task.timestamp.desc()).all()
    return render_template("tasks.html", title='Issued tasks', tasks = tasks)

#-------------------------------------------------------------
# Доступные всем зарегестрированным пользователям страницы 
#-------------------------------------------------------------

@app.route('/your_tasks', methods=['GET', 'POST'])
@login_required
def your_tasks():
    tasks = current_user.accept.order_by(Task.timestamp.desc()).all()
    return render_template("tasks.html", title='My tasks', tasks = tasks)


#-------------------------------------------------------------
# Функции меню
#-------------------------------------------------------------
@app.route('/toolbar_settings', methods=['GET'])
@login_required
def toolbar_settings():
    return render_template("toolbar_settings.html", title='Toolbar settings')

# Добавление в верхнее меню нового аттрибута
@app.route('/add_extra_menu_field/')
@login_required
def add_extra_menu_field():
    name  = request.args.get('name', None)
    current_user.extra_menu_fields.append(Menu_field(link = request.referrer, name = name))
    db.session.commit()
    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for('login')
    return redirect(next_page)

@app.route('/rename_link/<link_id>',methods=['GET', 'POST'])
@login_required
def rename_menu_field(link_id):
    link = Menu_field.query.filter_by(id = link_id).first()
    form = MenuForm()

    if form.validate_on_submit():
        link.name = form.name.data
        db.session.commit()
        return redirect(url_for("toolbar_settings"))
    return render_template("rename_link.html", title='Edit link', form = form)

@app.route('/delete_link/<link_id>')
@login_required
def delete_menu_field(link_id):
    Menu_field.query.filter_by(id = link_id).delete()
    db.session.commit()
    return redirect(url_for("toolbar_settings"))

# -------------------------
# Просто вспомогательные функции
# ------------------------

# Проверка, является ли текст ссылкой, а файл - картинкой
def is_link(link):
    if not (link.startswith("https://") or link.startswith("http://")):
        link = "http://" + link
    return checkers.is_url(link)

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
def is_picture(picture_name):
    return picture_name.rsplit('.', 1)[-1].lower() in ALLOWED_EXTENSIONS

app.jinja_env.globals.update(is_link = is_link)
app.jinja_env.globals.update(is_picture = is_picture)

def encode_filename(filename):
    random_hex = secrets.token_hex(8)
    filename = secure_filename(filename)
    _, f_ext = os.path.splitext(filename)
    encrypted_filename = random_hex + f_ext
    return (filename, encrypted_filename)

# Скачивание файла
@app.route('/uploads/<path:filename>')
@login_required
def download_file(filename):
    upload_folder = os.path.join(app.root_path, 'static/files/')
    return send_from_directory(upload_folder, filename, as_attachment=True)

# Обновление времени последнего запроса пользователя на сайте
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


