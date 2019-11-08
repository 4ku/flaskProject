from flask_babel import _, lazy_gettext as _l
from flask_wtf import FlaskForm
from app.models import Users, Roles
from wtforms import TextField, SubmitField, SelectField
from wtforms_sqlalchemy.fields import QuerySelectField
from sqlalchemy import or_
from flask_login import current_user


def assigners_query():
    return Users.query.join(Users.roles).filter(or_(Roles.name == "Admin", 
        Roles.name == "Usual"), ~Users.roles.any(Roles.name == "God"))

def get_pk(obj):
    return str(obj)

def acceptors_query():
    return Users.query.join(Users.roles).filter(or_(Roles.name == "Client", 
        Roles.name == "Usual"), ~Users.roles.any(Roles.name == "God"), Users.id != current_user.id)

class TaskForm_edit(FlaskForm):
    assigner = QuerySelectField(_l('Assigner'), query_factory=assigners_query, 
        get_pk = get_pk, get_label ="email")
    acceptor = QuerySelectField(_l('Acceptor'), query_factory=acceptors_query, 
        get_pk = get_pk, get_label ="email")
    status = SelectField(_l('Status'), 
        choices=[('Issued',_l('Issued')),('In progress',_l('In progress')),('Done',_l('Done'))])
    submit = SubmitField(_l('Submit'))

class TaskForm_create(FlaskForm):
    acceptor = QuerySelectField(_l('Acceptor'), query_factory=acceptors_query, 
        get_pk = get_pk, get_label ="email")
    submit = SubmitField(_l('Submit'))

class TemplateForm(FlaskForm):
    name = TextField(label = _l("Template name"))
    submit = SubmitField(_l('Submit'))