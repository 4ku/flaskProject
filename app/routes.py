from flask import render_template, flash, redirect, url_for, request, session
from flask_login import login_user, logout_user, login_manager,login_required
from flask_user import current_user,roles_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import *
from app.models import User, Role, Task
from datetime import datetime
from sqlalchemy import or_
from werkzeug.utils import secure_filename
import os
from PIL import Image
import secrets
from flask_wtf import FlaskForm
from wtforms.fields import Field
from wtforms import StringField, TextAreaField, SubmitField, RadioField, FieldList, FormField



@app.login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('login')


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


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



@app.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    tasks = Task.query.filter(or_(Task.assigner_id == user.id, 
        Task.acceptor_id == user.id)).all()
    return render_template('user.html', user=user, tasks = tasks)





@app.route('/give_task', methods=['GET', 'POST'])
@roles_required(['Admin', 'Usual'])
def give_task():
    extra_fields = []
    if 'fields' in session:
        extra_fields = session['fields']
    
    for i, field_label in enumerate(extra_fields):
        field = Field()
        if field_label == "textArea":
            field = TextAreaField()
        elif field_label == "text":
            field = TextAreaField()
        setattr(PostForm, str(i), field)
    
    form = PostForm()
    all_users = User.query.all()

    choices = []
    for user in all_users:
        if current_user.username == user.username:
            continue
        for role in user.roles:
            if((role.name == "Client") or (role.name == "Usual")):
                choices.append((user.id, user.username))
                break
    form.user_list.choices = choices

    if form.validate_on_submit():
        print(form.submit.data)
        print(form.add_field.data)

        if form.submit.data:
            session['fields'] = []
            task = Task(description=form.post.data)
            current_user.assign.append(task)
            user = User.query.filter_by(id=form.user_list.data).first()
            user.accept.append(task)
            db.session.add(task)
            db.session.commit()
            return redirect(url_for('give_task'))
        elif form.add_field.data:
            session['fields'].append("textArea")
            print(session['fields'])
            return redirect(url_for('give_task'))


    tasks = current_user.assign.all()

    return render_template("tasks.html", title='Give task',
     form=form, tasks=tasks)


@app.route('/your_tasks', methods=['GET', 'POST'])
@login_required
def your_tasks():
    tasks = current_user.accept.all()
    return render_template("tasks.html", title='My tasks', tasks = tasks)



@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))



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


@app.route('/delete_user/<user_id>')
@roles_required(['Admin'])
def delete_user(user_id):
    Task.query.filter(Task.acceptor_id == user_id).delete()
    Task.query.filter(Task.assigner_id == user_id).delete()
    User.query.filter_by(id=user_id).delete()
    db.session.commit()
    return redirect(url_for("all_users"))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/', picture_fn)

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

    return render_template('edit_profile.html', title='Edit Profile',
                           form=form, user = user)


@app.route('/delete_task/<task_id>')
@roles_required(['Admin'])
def delete_task(task_id):
    Task.query.filter(Task.id == task_id).delete()
    db.session.commit()
    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for('all_users')
    return redirect(next_page)


@app.route('/edit_task/<task_id>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def edit_task(task_id):
    task = Task.query.filter_by(id = task_id).first()
    form = EditTaskForm()
    
    all_users = User.query.all()
    
    choices_assigner = []
    for user in all_users:
        if current_user.username == user.username:
            continue
        for role in user.roles:
            if((role.name == "Usual")):
                choices_assigner.append((user.id, user.username))
                break
    
    choices_acceptor = []
    for user in all_users:
        if current_user.username == user.username:
            continue
        for role in user.roles:
            if((role.name == "Client") or (role.name == "Usual")):
                choices_acceptor.append((user.id, user.username))
                break

    form.assigner.choices = choices_assigner
    form.acceptor.choices = choices_acceptor

    if form.validate_on_submit():
        acceptor = User.query.filter_by(id = int(form.acceptor.data)).first()
        assigner = User.query.filter_by(id = int(form.assigner.data)).first()

        task.acceptor = acceptor
        task.assigner = assigner
        task.acceptor_id = acceptor.id
        task.assigner_id = assigner.id
        task.description = form.post.data
        task.status = form.status.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_task', task_id = task_id))
    elif request.method == 'GET':
        form.acceptor.data = task.acceptor.id
        form.assigner.data = task.assigner.id
        form.post.data = task.description
        form.status.data = task.status
    return render_template('edit_task.html', title='Edit task',
                           form=form)