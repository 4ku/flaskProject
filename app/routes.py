from flask import render_template, flash, redirect, url_for, request, session, send_from_directory
from flask_login import current_user, login_user, logout_user, login_manager, login_required
from functools import wraps

from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from datetime import datetime
from sqlalchemy import or_
import os
from PIL import Image
import secrets
from flask_wtf import FlaskForm
from wtforms.fields import Field
from wtforms import StringField, TextAreaField, SubmitField, RadioField, FieldList, FormField, TextField
from wtforms.fields.html5 import DateField
from sqlalchemy import exists
from shutil import copyfile

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

def encode_filename(filename):
    random_hex = secrets.token_hex(8)
    filename = secure_filename(filename)
    _, f_ext = os.path.splitext(filename)
    encrypted_filename = random_hex + f_ext
    return (filename, encrypted_filename)


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
    return render_template('user.html', user=user, 
        tasks = tasks)


#-------------------------------------------------------------
# Админские страницы
#-------------------------------------------------------------

@app.route('/all_users', methods=['GET', 'POST'])
@roles_required(['Admin'])
def all_users():
    all_users = User.query.filter(User.username!=current_user.username).all()
    return render_template("all_users.html", users = all_users)


@app.route('/all_tasks', methods=['GET', 'POST'])
@roles_required(['Admin'])
def all_tasks():
    return render_template("tasks.html", 
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
            current_user.avatar_path = save_picture(form.picture.data)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_user'))
    return render_template('edit_user.html', title='Edit Profile',
                           form=form, user = current_user)


# Данная функция используется при создании задания и его редактирования
def prepare_task(task, fields, is_edit):
    class DynamicForm(FlaskForm):
        pass

    # Создание новых полей для задания
    for i, field_data in enumerate(fields):
        field = Field()
        if field_data.text or field_data.text == "":
            field = TextAreaField(label = "Text area:", 
                validators=[Length(max=140), DataRequired()])
        elif field_data.date:
            field = DateField(label = "Date: ", validators=[DataRequired()])
        elif field_data.filename or field_data.filename == "":
            label = {"filename": field_data.filename, "encrypted_filename": field_data.encrypted_filename}
            field = FileField(label = label, validators=[check_file_label])
        setattr(DynamicForm, str(i), field)

    dynamic_form = DynamicForm()
    form = TaskForm_edit() if is_edit else TaskForm_create()

    assigners = User.query.join(User.roles).filter(or_(Role.name == "Admin", Role.name == "Usual")).all()
    assigner_choices =  [ (user.id, user.username) for user in assigners ]

    acceptors = User.query.join(User.roles).filter(or_(Role.name == "Client", Role.name == "Usual")).all()
    acceptor_choices = [ (user.id, user.username) for user in acceptors ]
    if (current_user.id, current_user.username) in acceptor_choices:
        acceptor_choices.remove((current_user.id, current_user.username))
        
    form.acceptor.choices = acceptor_choices    
    if is_edit:
        form.assigner.choices = assigner_choices
    
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

        # Сохранение данных в БД
        if is_edit:
            task.status = form.status.data
            # Изменение task.media
            for i, field_data in enumerate(task.media):
                if field_data.text:
                    field_data.text = dynamic_form[str(i)].data
                elif field_data.date:
                    field_data.date = dynamic_form[str(i)].data 
                elif field_data.filename:
                    # Если добавляем свой файл (заменяем предшествующий)
                    if dynamic_form[str(i)].data:
                        os.remove(os.path.join(app.root_path, 'static/files/', field_data.encrypted_filename))
                        file = dynamic_form[str(i)].data
                        filename, encrypted_filename = encode_filename(file.filename)
                        field_data.filename = filename
                        field_data.encrypted_filename = encrypted_filename
                        file.save(os.path.join(app.root_path, 'static/files/',  encrypted_filename))
                    # Если хотим оставить файл, который был до этого, то ничего не делаем
                                        
        else:
            # Создание task.media
            for field in dynamic_form:
                if field.type == "TextField":
                    task.media.append(Task_media(text = field.data))
                elif field.type == "TextAreaField":
                    task.media.append(Task_media(text = field.data)) 
                elif field.type == "DateField":
                    task.media.append(Task_media(date = field.data))
                elif field.type == "FileField":
                    filename, encrypted_filename = "", ""
                    # Если добавляем свой файл
                    if field.data:
                        file = field.data
                        filename, encrypted_filename = encode_filename(file.filename)
                        file.save(os.path.join(app.root_path, 'static/files/',  encrypted_filename))
                    # Если оставляем файл, который был в шаблоне
                    elif field.label.text["filename"]:
                        src_path = os.path.join(app.root_path, 'static/files/', field.label.text["encrypted_filename"])
                        filename, encrypted_filename = encode_filename(field.label.text["filename"])
                        dst_path = os.path.join(app.root_path, 'static/files/', encrypted_filename)
                        copyfile(src_path, dst_path)
                    task.media.append(Task_media(encrypted_filename = encrypted_filename, filename = filename))
            db.session.add(task)

        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('login'))
    elif request.method == 'GET':
        # Заполнение полей существующими данными

        for i, field_data in enumerate(fields):
            if field_data.text:
                dynamic_form[str(i)].data = field_data.text
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


@app.route('/edit_task/<task_id>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def edit_task(task_id):
    task = Task.query.filter_by(id = task_id).first()
    return prepare_task(task, task.media, True)


# --- Удаление пользователя и заданий ----
@app.route('/delete_user/<user_id>')
@roles_required(['Admin'])
def delete_user(user_id):
    #Удаление всех заданий пользователя
    acceptor_tasks = Task.query.filter(Task.acceptor_id == user_id).all()
    assigner_tasks = Task.query.filter(Task.assigner_id == user_id).all()
    for task in acceptor_tasks:
        delete_task(task.id)
    for task in assigner_tasks:
        delete_task(task.id)
    
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    return redirect(url_for("all_users"))

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

# Создание шаблона
@app.route('/create_new_template', methods=['GET', 'POST'])
@roles_required(['Admin'])
def create_new_template():
    class DynamicForm(FlaskForm):
        pass

    extra_fields = []
    if 'fields' in session:
        extra_fields = session['fields']
    
    for i, field_label in enumerate(extra_fields):
        field = Field()
        if field_label == "Text":
            field = TextAreaField(label = "Text area:", 
                validators=[Length(max=140)])
        elif field_label == "Date":
            field = DateField(label = "Date: ", validators=[])
        elif field_label == "File":
            field = FileField('Pick a file: ')
        setattr(DynamicForm, str(i), field)

    class myForm(FlaskForm):
        submit = SubmitField('Submit')

    form = myForm()
    add_field_form = AddFieldForm()
    dynamic_form = DynamicForm()

    # Если нажата кнопка добавить задание
    if form.submit.data and form.validate_on_submit() and len(extra_fields) > 0:
        session['fields'] = []
        template = Task_templates()
        for field in dynamic_form:
            if field.type == "TextField":
                pass
            elif field.type == "TextAreaField":
                data = field.data if field.data else ""
                template.field.append(Task_media(text = data)) 
            elif field.type == "DateField":
                data = field.data if field.data else datetime(1,1,1)
                template.field.append(Task_media(date = data))
            elif field.type == "FileField":
                filename, encrypted_filename = "", ""
                if field.data:
                    file = field.data
                    filename, encrypted_filename = encode_filename(file.filename)
                    file.save(os.path.join(app.root_path, 'static/files/',  encrypted_filename))
                template.field.append(Task_media(encrypted_filename = encrypted_filename, filename = filename))

            
        db.session.add(template)
        db.session.commit()
        return redirect(url_for('templates'))

    # Если нажата кнопка создания поля
    if add_field_form.add_field.data and add_field_form.validate_on_submit(): 
        if "fields" not in session:
            session['fields'] = []
        session['fields'].append(add_field_form.fields_list.data)
        return redirect(url_for('create_new_template'))

    return render_template("create_new_template.html", title='Create template', 
        form=form, add_field_form = add_field_form, 
        extra_fields = dynamic_form)


#-------------------------------------------------------------
# Страницы, которые доступны и админу и обычному пользователю 
#-------------------------------------------------------------

# Выбор шаблона задания или создание нового шаблона (только для админа)
@app.route('/templates', methods=['GET', 'POST'])
@roles_required(['Admin', 'Usual'])
def templates():
    templates = Task_templates.query.all()
    return render_template('templates.html', templates = templates)

# Сразу же после выбора шаблона, можем создать задание по выбранному шаблону
@app.route('/create_task/<template_id>', methods=['GET', 'POST'])
@roles_required(['Admin', 'Usual'])
def create_task(template_id):
    fields = Task_templates.query.filter_by(id = template_id).first().field
    return prepare_task(Task(), fields, False)


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

# Добавление в верхнее меню нового аттрибута
@app.route('/add_extra_menu_field/')
@login_required
def add_extra_menu_field():
    if current_user.is_authenticated:
        current_user.extra_menu_fields.append(Menu_field(link = request.referrer))
        db.session.commit()
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('login')
        return redirect(next_page)

# Скачивание файла
@app.route('/uploads/<path:filename>')
@login_required
def download_file(filename):
    upload_folder = os.path.join(app.root_path, 'static/files/')
    return send_from_directory(upload_folder, filename, as_attachment=True)

# -------------------------
# Просто вспомогательные функции
# ------------------------

# Обновление времени последнего запроса пользователя на сайте
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

