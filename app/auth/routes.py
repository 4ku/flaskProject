from app.auth import bp
from app.models import Users, Roles
from app import db

from flask_babel import _, lazy_gettext as _l
from flask import render_template, flash, redirect, url_for, request, session
from flask_login import current_user, login_user, logout_user, login_manager
from app.auth.forms import *

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('sections.main'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data) or user.roles[0].name == 'Not confirmed':
            flash(_l('Invalid email or password'))
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('users.user', id=user.id)
        return redirect(next_page)
    return render_template('login.html', title='Login', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# Регистрация пользователя
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('users.user', id=current_user.id))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Users(email = form.email.data, last_name=form.last_name.data,
            first_name=form.first_name.data)
        user.set_password(form.password.data)
        user.roles.append(Roles(name="Not confirmed"))
        db.session.add(user)
        db.session.commit()
        flash(_l('Wait for administrator register confirmation.'))
        return redirect(url_for('auth.login'))
    return render_template('register.html', title='Register', form=form)