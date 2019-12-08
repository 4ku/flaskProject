from flask_babel import _, lazy_gettext as _l
from flask import render_template, redirect, url_for, request, session, send_from_directory
from flask_login import current_user, login_manager, login_required
from functools import wraps
from flask import g
from flask_babel import get_locale

from werkzeug.urls import url_parse
# from werkzeug.utils import secure_filename
from datetime import datetime
import os
import secrets
from validator_collection import checkers
from PIL import Image

from app import app, db
from app.forms import *
from app.models import *

# Проверка роли пользователя
def roles_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))

            access = False
            for role in roles:
                for user_role in current_user.roles:
                    if role == user_role.name:
                        access = True

            if not access:
                flash(_l('You do not have access to that page. Sorry!'))
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for('auth.login'))

@login_required
@app.route('/toolbar_settings', methods=['GET'])
def toolbar_settings():
    return render_template("toolbar_settings.html", title=_l('Toolbar settings'))


#-------------------------------------------------------------
# Функции меню - добавление дополнительных ссылок
#-------------------------------------------------------------
# Добавление в верхнее меню нового аттрибута
@app.route('/add_extra_menu_field/')
@login_required
def add_extra_menu_field():
    name  = request.args.get('name', None)
    current_user.extra_menu_fields.append(Menu_fields(link = request.referrer, name = name))
    db.session.commit()
    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for('auth.login')
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

# Добавение в jinja, чтобы можно было пользоваться
# функциями в шаблоне
app.jinja_env.globals.update(is_link = is_link)
app.jinja_env.globals.update(append_http = append_http)

# Получение закодированного имени файла
# В основном нужно для хранения файлов,
# с одинаковыми именами
def encode_filename(filename):
    random_hex = secrets.token_hex(8)
    # filename = secure_filename(filename)
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
# и получение текущего языка перед каждым запросом
@app.before_request
def before_request():
    g.locale = str(get_locale())
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


def logo():
    directory = os.path.join(app.root_path, 'static/logo/')
    return os.listdir(directory)[0]
app.jinja_env.globals.update(logo = logo)

@app.route('/change_logo/',methods=['GET', 'POST'])
@login_required
def change_logo():
    form =  LogoForm()
    if form.validate_on_submit():
        #Удаление всех предыдущих файлов
        directory = os.path.join(app.root_path, 'static/logo/')
        filelist = os.listdir(directory)
        for f in filelist:
            os.remove(os.path.join(directory, f))

        #Сохранение
        file = form.file.data
        __, f_ext = os.path.splitext(file.filename)
        file.save(os.path.join(directory, 'logo'+f_ext))
        return redirect(url_for('toolbar_settings'))

    return render_template("change_logo.html", title=_l('Change logo'), form = form)




from wtforms import TextField, SubmitField, SelectField
from app.dynamic_fields.forms import *

@app.route('/test/',methods=['GET', 'POST'])
@login_required
def test():
    class TestForm(FlaskForm):
        select = SelectField(_l('Field type'),
        choices=[('Text',_l('Text')), ('TextArea',_l('TextArea')),
            ('Date',_l('Date'))])
        submit = SubmitField(_l('Submit'))

    # sub_form = CategoricalField(request.form)
    form = CategoriesForm()
    if request.method == 'GET':
        # sub_form.categories.append_entry()
        # sub_form.categories.append_entry()
        # data = {"categories": sub_form.categories.data}
        # form.categories_fields.append_entry({"categories": [{'category': 'qqqqqqqq'}, {'category': 'wwwww'}] })
        # form.categories_fields.append_entry({"categories": [{'category': 'rrrrr'}, {'category': '01'}] })
        pass
        # form.categories_fields[0].categories=sub_form

    elif form.validate():
        # for field in sub_form.categories:
        #     print(field.category.data)

        # print(sub_form.category)
        # print(sub_form.category.data)
        # print(sub_form.categories)
        # print(sub_form.categories.data)

        print(form)
        print(11111111111)
        print(form.categories_fields)
        print(2222222222)
        print(form.categories_fields.data)

    return render_template("test.html", form = form)


@app.route('/test2/',methods=['GET', 'POST'])
@login_required
def test2():
    class TestForm(FlaskForm):
        select = SelectField(_l('Field type'),
        choices=[('Text',_l('Text')), ('TextArea',_l('TextArea')),
            ('Date',_l('Date')), ('Date',_l('Date2'))], default = "Date")
        submit = SubmitField(_l('Submit'))

    form = TestForm()
    if request.method == 'GET':
        pass
    elif form.validate():
        print(list(dict(form.select.choices).keys()))
        print(1111111111111111)
        print(form.select.data)
        print(2222222222222222)
        # print(form.select.choices.keys)

    return render_template("test2.html", form = form)




