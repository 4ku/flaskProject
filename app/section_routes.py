# Здесь добавлены все функции, связанные с созданиемб редактированием и удалением заданий и шаблонов к ним

from flask import render_template, flash, redirect, url_for, request, session
from flask_login import current_user, login_required
from flask_babel import _, lazy_gettext as _l
from werkzeug.urls import url_parse

from app import app, db
from app.forms import *
from app.models import *
from app.dynamic_fields import *
from app.routes import roles_required


def create_or_edit_section(section, is_edit):
    form = SectionForm()
    add_field_form = AddFieldForm()

    is_validated, dynamic_forms = dynamic_fields(section, section.fields, False)

    if request.method == "GET":
        form.name.data = section.name

    elif is_validated and form.validate_on_submit():
        section.name = form.name.data
        if not is_edit:
            db.session.add(section)
        db.session.commit()
        return redirect(url_for("all_users"))

    return render_template("create_or_edit_section.html", add_field_form = add_field_form, 
        form = form, is_template = True, dynamic_forms = dynamic_forms)


@app.route('/create_section',methods=['GET', 'POST'])
@roles_required(['Admin'])
def create_section():
    section = Sections()
    return create_or_edit_section(section, False)

@app.route('/edit_section/<section_id>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def edit_section(section_id):
    section = Sections.query.filter_by(id = section_id).first()
    return create_or_edit_section(section, True)

@app.route('/delete_section/<section_id>')
@roles_required(['Admin'])
def delete_section(section_id):
    section = Sections.query.filter_by(id == section_id).first()
    for page in section.pages:
        _delete_page(page.id)
        db.session.commit()
    delete_fields(section.fields)
    db.session.commit()
    db.session.delete(section)
    db.session.commit()

    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for('all_users')
    return redirect(next_page)


@app.route('/sections/<section_id>', methods=['GET'])
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
    is_validated, dynamic_forms = dynamic_fields(page, fields, True)
    if is_validated and form.validate_on_submit():
        page.section = section
        if not is_edit:
            db.session.add(page)
        db.session.commit()
        return redirect(url_for("view_section", section_id = section.id))
    return render_template("create_or_edit_page.html", is_template = False, form = form,
         dynamic_forms = dynamic_forms)


@app.route('/create_page/<section_id>',methods=['GET', 'POST'])
@roles_required(['Admin'])
def create_page(section_id):
    page = Pages()
    section = Sections.query.filter_by(id = section_id).first()
    fields = section.fields
    return create_or_edit_page(page,fields, section, False)


@app.route('/edit_page/<page_id>', methods=['GET', 'POST'])
@roles_required(['Admin'])
def edit_page(page_id):
    page = Pages.query.filter_by(id = page_id).first()
    return create_or_edit_page(page, page.fields, page.section_id, True)


def _delete_page(page_id):
    page = Pages.query.filter_by(id == page_id).first()
    delete_fields(page.fields)
    db.session.commit()
    db.session.delete(page)
    db.session.commit()

@app.route('/delete_page/<page_id>')
@roles_required(['Admin'])
def delete_page(page_id):
    _delete_page(page_id)
    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for('all_users')
    return redirect(next_page)

@app.route('/view_full_page/<page_id>', methods=['GET'])
@roles_required(['Admin'])
def full_page(page_id):
    page = Pages.query.filter_by(id = page_id).first()
    return render_template("full_page.html",page = page)


# @app.route('/main', methods=['GET', 'POST'])
# @login_required
# def main():
#     return render_template("pages.html", title = _l("Main page"),
#         pages = Pages.query.all())








