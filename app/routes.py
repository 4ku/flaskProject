from flask import render_template, flash, redirect, url_for, request, session, send_from_directory
from flask_login import login_user, logout_user, login_manager,login_required
from flask_user import current_user,roles_required

from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy import or_
import os
from PIL import Image
import secrets
from flask_wtf import FlaskForm
from wtforms.fields import Field
from wtforms import StringField, TextAreaField, SubmitField, RadioField, FieldList, FormField, TextField
from wtforms.fields.html5 import DateField

from app import app, db
from app.forms import *
from app.models import *



@app.login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('login')

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
        Task.acceptor_id == user.id)).all()
    return render_template('user.html', user=user, tasks = tasks)


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


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/avatars/', picture_fn)
    # output_size = (125, 125)
    i = Image.open(form_picture)
    # i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route('/edit_user/<username>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def edit_user(username):
    user = User.query.filter_by(username=username).first()
    form = EditProfileForm(user.username)
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            user.avatar_path = picture_file
        user.username = form.username.data
        user.roles[0] = (Role(name=form.role_list.data))
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_user', username = form.username.data))
    elif request.method == 'GET':
        form.username.data = user.username
        form.role_list.data = user.roles[0].name
        db.session.commit()

    return render_template('edit_user.html', title='Edit Profile',
                           form=form, user = user)


@app.route('/edit_task/<task_id>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def edit_task(task_id):
    task = Task.query.filter_by(id = task_id).first()
    form = EditTaskForm()
    all_users = User.query.all()
    
    choices_assigner = []
    for user in all_users:
        # if current_user.username == user.username:
        #     continue
        for role in user.roles:
            if((role.name == "Usual") or (role.name == "Admin")):
                choices_assigner.append((user.id, user.username))
                break
    
    choices_acceptor = []
    for user in all_users:
        # if current_user.username == user.username:
        #     continue
        for role in user.roles:
            if((role.name == "Client") or (role.name == "Usual")):
                choices_acceptor.append((user.id, user.username))
                break
    
    form.assigner.choices = choices_assigner
    form.acceptor.choices = choices_acceptor


    class DynamicForm(FlaskForm):
        pass

    for i, field_data in enumerate(task.media):
        label_field = TextField(label = "Label: ")
        field = Field()
        if field_data.label:
            label_field.data = field_data.label
        if field_data.text:
            field = TextAreaField(label = "Text area:", 
                validators=[Length(max=140), DataRequired()])
            field.data = field_data.text
        elif field_data.date:
            field = DateField(label = "Date: ", validators=[DataRequired()])
            field.data = field_data.date
        elif field_data.filename:
            field = FileField('Pick a file: ',
                 validators=[FileAllowed(['jpg', 'png','jpeg']), DataRequired("fd")])
        setattr(DynamicForm, str(i*2), label_field)        
        setattr(DynamicForm, str(i*2+1), field)
    
    dynamic_form = DynamicForm()
    for i, field_data in enumerate(task.media):
        if field_data.label:
            dynamic_form[str(2*i)].data = field_data.label
        if field_data.text:
            dynamic_form[str(2*i+1)].data = field_data.text
        elif field_data.date:
            dynamic_form[str(2*i+1)].data = field_data.date
        elif field_data.filename:
            pass
            # field = FileField('Pick a file: ',
            #      validators=[FileAllowed(['jpg', 'png','jpeg']), DataRequired("fd")])


    if form.validate_on_submit():
        acceptor = User.query.filter_by(id = int(form.acceptor.data)).first()
        assigner = User.query.filter_by(id = int(form.assigner.data)).first()

        task.acceptor = acceptor
        task.assigner = assigner
        task.acceptor_id = acceptor.id
        task.assigner_id = assigner.id
        task.status = form.status.data

        Task_media.query.filter(Task_media.task_id == task.id).delete()

        label = ""
        for field in dynamic_form:
            if field.type == "TextField":
                label = field.data
            elif field.type == "TextAreaField":
                task.media.append(Task_media(label = label, text = field.data)) 
            elif field.type == "DateField":
                task.media.append(Task_media(label = label, date = field.data))
            elif field.type == "FileField":
                file = field.data
                random_hex = secrets.token_hex(8)
                filename = secure_filename(file.filename)
                _, f_ext = os.path.splitext(filename)
                encrypted_filename = random_hex + f_ext
                file.save(os.path.join(app.root_path, 'static/files/', encrypted_filename))
                task.media.append(Task_media(label = label, encrypted_filename = encrypted_filename, filename = filename))
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_task', task_id = task_id))
    elif request.method == 'GET':
        form.acceptor.data = task.acceptor.id
        form.assigner.data = task.assigner.id
        form.status.data = task.status

    return render_template('edit_task.html', title='Edit task',
                           form=form, extra_fields = dynamic_form)


# --- Удаление пользователя и заданий ----
@app.route('/delete_user/<user_id>')
@roles_required(['Admin'])
def delete_user(user_id):
    Task.query.filter(Task.acceptor_id == user_id).delete()
    Task.query.filter(Task.assigner_id == user_id).delete()
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    return redirect(url_for("all_users"))

@app.route('/delete_task/<task_id>')
@roles_required(['Admin'])
def delete_task(task_id):
    Task_media.query.filter(Task_media.task_id == task_id).delete()
    Task.query.filter(Task.id == task_id).delete()
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
        label_field = TextField(label = "Label: ")
        field = Field()
        if field_label == "Text":
            field = TextAreaField(label = "Text area:", 
                validators=[Length(max=140), DataRequired()])
        elif field_label == "Date":
            field = DateField(label = "Date: ", validators=[DataRequired()])
        elif field_label == "File":
            field = FileField('Pick a file: ',
                 validators=[FileAllowed(['jpg', 'png','jpeg']), DataRequired("fd")])
        setattr(DynamicForm, str(i*2), label_field)        
        setattr(DynamicForm, str(i*2+1), field)


    class myForm(FlaskForm):
        submit = SubmitField('Submit')

    form = myForm()
    add_field_form = AddFieldForm()
    dynamic_form = DynamicForm()

    # Если нажата кнопка добавить задание
    if form.submit.data and form.validate_on_submit() and dynamic_form.validate():
        session['fields'] = []
        template = Task_templates()
        label = ""
        print(template.field)
        for field in dynamic_form:
            if field.type == "TextField":
                label = field.data
            elif field.type == "TextAreaField":
                template.field.append(Task_media(label = label, text = field.data)) 
            elif field.type == "DateField":
                template.field.append(Task_media(label = label, date = field.data))
            elif field.type == "FileField":
                template.field.append(Task_media(label = label, filename = "1"))
            
        db.session.add(template)
        db.session.commit()
        return redirect(url_for('templates'))

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

    class DynamicForm(FlaskForm):
        pass

    for i, field_data in enumerate(fields):
        label_field = TextField(label = "Label: ")
        field = Field()
        if field_data.label:
            label_field.data = field_data.label
        if field_data.text:
            field = TextAreaField(label = "Text area:", 
                validators=[Length(max=140), DataRequired()])
            field.data = field_data.text
        elif field_data.date:
            field = DateField(label = "Date: ", validators=[DataRequired()])
            field.data = field_data.date
        elif field_data.filename:
            field = FileField('Pick a file: ',
                 validators=[FileAllowed(['jpg', 'png','jpeg']), DataRequired()])
        setattr(DynamicForm, str(i*2), label_field)        
        setattr(DynamicForm, str(i*2+1), field)

    class myForm(FlaskForm):
        user_list = SelectField('users', choices=[], coerce = int)
        submit = SubmitField('Submit')

    form = myForm()
    dynamic_form = DynamicForm()
    all_users = User.query.all()

    for i, field_data in enumerate(fields):
        if field_data.label:
            dynamic_form[str(2*i)].data = field_data.label
        if field_data.text:
            dynamic_form[str(2*i+1)].data = field_data.text
        elif field_data.date:
            dynamic_form[str(2*i+1)].data = field_data.date
        elif field_data.filename:
            pass

    # Устанавливаем в меню список всех пользователей и клиентов
    choices = []
    for user in all_users:
        if current_user.username == user.username:
            continue
        for role in user.roles:
            if((role.name == "Client") or (role.name == "Usual")):
                choices.append((user.id, user.username))
                break
    form.user_list.choices = choices

    # Если нажата кнопка добавить задание
    if form.submit.data and form.validate_on_submit() and dynamic_form.validate():
        task = Task()
        label = ""
        for field in dynamic_form:
            if field.type == "TextField":
                label = field.data
            elif field.type == "TextAreaField":
                task.media.append(Task_media(label = label, text = field.data)) 
            elif field.type == "DateField":
                task.media.append(Task_media(label = label, date = field.data))
            elif field.type == "FileField":
                print(type(field.data))
                file = field.data
                random_hex = secrets.token_hex(8)
                filename = secure_filename(file.filename)
                _, f_ext = os.path.splitext(filename)
                encrypted_filename = random_hex + f_ext
                file.save(os.path.join(app.root_path, 'static/files/', encrypted_filename))
                task.media.append(Task_media(label = label, encrypted_filename = encrypted_filename, filename = filename))
            
        current_user.assign.append(task)
        user = User.query.filter_by(id=form.user_list.data).first()
        user.accept.append(task)
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('give_task'))

    # Получаем все задания, выданные данным пользователем
    tasks = current_user.assign.all()

    return render_template("create_task.html", title='Create task', 
        form=form,  
        extra_fields = dynamic_form)


#-------------------------------------------------------------
# Доступные всем зарегестрированным пользователям страницы 
#-------------------------------------------------------------

@app.route('/your_tasks', methods=['GET', 'POST'])
@login_required
def your_tasks():
    tasks = current_user.accept.all()
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



# Some shit
@app.route('/give_task', methods=['GET', 'POST'])
@roles_required(['Admin', 'Usual'])
def give_task():

    class DynamicForm(FlaskForm):
        pass

    extra_fields = []
    if 'fields' in session:
        extra_fields = session['fields']
    
    for i, field_label in enumerate(extra_fields):
        label_field = TextField(label = "Label: ")
        field = Field()
        if field_label == "Text":
            field = TextAreaField(label = "Text area:", 
                validators=[Length(max=140), DataRequired()])
        elif field_label == "Date":
            field = DateField(label = "Date: ", validators=[DataRequired()])
        elif field_label == "File":
            field = FileField('Pick a file: ',
                 validators=[FileAllowed(['jpg', 'png','jpeg']), DataRequired("fd")])
        setattr(DynamicForm, str(i*2), label_field)        
        setattr(DynamicForm, str(i*2+1), field)

    form = PostForm()
    add_field_form = AddFieldForm()
    dynamic_form = DynamicForm()
    all_users = User.query.all()

    # Устанавливаем в меню список всех пользователей и клиентов
    choices = []
    for user in all_users:
        if current_user.username == user.username:
            continue
        for role in user.roles:
            if((role.name == "Client") or (role.name == "Usual")):
                choices.append((user.id, user.username))
                break
    form.user_list.choices = choices

    # Если нажата кнопка добавить задание
    if form.submit.data and form.validate_on_submit() and dynamic_form.validate():
        session['fields'] = []
        task = Task()
        task.media.append(Task_media(text = form.post.data))
        label = ""
        for field in dynamic_form:
            if field.type == "TextField":
                label = field.data
            elif field.type == "TextAreaField":
                task.media.append(Task_media(label = label, text = field.data)) 
            elif field.type == "DateField":
                task.media.append(Task_media(label = label, date = field.data))
            elif field.type == "FileField":
                print(type(field.data))
                file = field.data
                random_hex = secrets.token_hex(8)
                filename = secure_filename(file.filename)
                _, f_ext = os.path.splitext(filename)
                encrypted_filename = random_hex + f_ext
                file.save(os.path.join(app.root_path, 'static/files/', encrypted_filename))
                task.media.append(Task_media(label = label, encrypted_filename = encrypted_filename, filename = filename))
            
        current_user.assign.append(task)
        user = User.query.filter_by(id=form.user_list.data).first()
        user.accept.append(task)
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('give_task'))

    if add_field_form.add_field.data and add_field_form.validate_on_submit(): 
        if "fields" not in session:
            session['fields'] = []
        session['fields'].append(add_field_form.fields_list.data)
        return redirect(url_for('give_task'))

    # Получаем все задания, выданные данным пользователем
    tasks = current_user.assign.all()

    return render_template("tasks.html", title='Give task', 
        form=form, add_field_form = add_field_form, 
        extra_fields = dynamic_form, tasks=tasks)

