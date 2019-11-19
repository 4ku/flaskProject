# Здесь добавлены все функции, связанные с созданием, редактированием и удалением секций и шаблонов к ним

from app import db
from app.sections import bp
from app.sections.forms import *
from app.models import *
from app.dynamic_fields.dynamic_fields import *
from app.dynamic_fields.forms import *
from app.routes import roles_required

from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required
from flask_babel import _, lazy_gettext as _l
from werkzeug.urls import url_parse


# Раздел, где будут отображаться все документы
@bp.route('/all_documents',methods=['GET', 'POST'])
@login_required
def all_documents():
    media = Media.query.all()
    files = []
    for field in media:
        if field.filename:
            files.append(field)
    return render_template("all_documents.html", files = files)


#---------------------------------------------------------------------
#                           Sections
#---------------------------------------------------------------------

def create_or_edit_section(section, is_edit):
    form = SectionForm(section.name)
    add_field_form = AddFieldForm()

    is_validated, dynamic_forms = dynamic_fields(section, section.fields, True)

    if request.method == "GET":
        form.name.data = section.name
        form.is_displayed.data = section.display


    elif is_validated and form.validate_on_submit():
        section.name = form.name.data
        section.display = form.is_displayed.data
        if not is_edit:
            db.session.add(section)
        db.session.commit()
        return redirect(url_for('sections.view_section', section_id=section.id))


    return render_template("create_or_edit_section.html", add_field_form = add_field_form, 
        form = form, is_template = True, dynamic_forms = dynamic_forms)

@bp.route('/create_section',methods=['GET', 'POST'])
@roles_required(['Admin'])
def create_section():
    section = Sections()
    return create_or_edit_section(section, False)

@bp.route('/edit_section/<section_id>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def edit_section(section_id):
    section = Sections.query.filter_by(id = section_id).first()
    return create_or_edit_section(section, True)

@bp.route('/delete_section/<section_id>')
@roles_required(['Admin'])
def delete_section(section_id):
    section = Sections.query.filter_by(id = section_id).first()
    if section.pages:
        for page in section.pages:
            _delete_page(page.id)
            db.session.commit()
    delete_fields(section.fields)
    db.session.commit()
    db.session.delete(section)
    db.session.commit()

    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for('sections.main')
    return redirect(next_page)


@bp.route('/sections/<section_id>', methods=['GET'])
@roles_required(['Admin'])
def view_section(section_id):
    section = Sections.query.filter_by(id = section_id).first()
    return render_template("section_pages.html", title = section.name,
        pages = section.pages, section_id = section_id)


#---------------------------------------------------------------------
#                           Pages
#---------------------------------------------------------------------

def create_or_edit_page(page, fields, section, is_edit):
    form = PageForm()
    is_validated, dynamic_forms = dynamic_fields(page, fields, False)
    if is_validated and form.validate_on_submit():
        page.section = section
        if not is_edit:
            db.session.add(page)
        db.session.commit()
        return redirect(url_for("sections.view_section", section_id = section.id))
    return render_template("create_or_edit_page.html", is_template = False, form = form,
         dynamic_forms = dynamic_forms)

@bp.route('/create_page/<section_id>',methods=['GET', 'POST'])
@roles_required(['Admin'])
def create_page(section_id):
    page = Pages()
    section = Sections.query.filter_by(id = section_id).first()
    fields = section.fields
    return create_or_edit_page(page,fields, section, False)

@bp.route('/edit_page/<page_id>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def edit_page(page_id):
    page = Pages.query.filter_by(id = page_id).first()
    return create_or_edit_page(page, page.fields, page.section , True)

def _delete_page(page_id):
    page = Pages.query.filter_by(id = page_id).first()
    delete_fields(page.fields)
    db.session.commit()
    db.session.delete(page)
    db.session.commit()

@bp.route('/delete_page/<page_id>')
@roles_required(['Admin'])
def delete_page(page_id):
    _delete_page(page_id)
    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for('sections.main')
    return redirect(next_page)

#Отображение всей информации о странице 
@bp.route('/view_full_page/<page_id>', methods=['GET'])
@roles_required(['Admin'])
def full_page(page_id):
    page = Pages.query.filter_by(id = page_id).first()
    return render_template("full_page.html",page = page)



# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------

@bp.route('/main', methods=['GET', 'POST'])
@login_required
def main():
    return render_template("main.html", title = _l("Main page"),
        sections = Sections.query.all())

# Глобальная функция, нужна для отображения списка секций в панели 
def get_sections():
    return Sections.query.all() 

app.jinja_env.globals.update(get_sections = get_sections)




