from datetime import datetime
from app import db
from flask_login import UserMixin
from hashlib import md5
from werkzeug.security import generate_password_hash, check_password_hash
from flask import url_for

from app.dynamic_fields.models import *


#---------------------------------------------------------------------
#                           Tasks
#---------------------------------------------------------------------
task_template_field_connection = db.Table("task_template_field_connection",
    db.Column('template_id', db.Integer, db.ForeignKey('task_templates.id')),
    db.Column('field_id', db.Integer, db.ForeignKey('fields.id'))
 )

class Task_templates(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64))
    fields = db.relationship("Fields", 
        secondary = task_template_field_connection, 
        primaryjoin =(task_template_field_connection.c.template_id == id),
        secondaryjoin = (task_template_field_connection.c.field_id == Fields.id),
        backref = "task_template", order_by = "Fields.order")

task_field_connection = db.Table("task_field_connection",
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id')),
    db.Column('field_id', db.Integer, db.ForeignKey('fields.id'))
 )

class Tasks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    assigner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    acceptor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.Unicode(32), default ="Issued")
    fields = db.relationship("Fields", 
        secondary = task_field_connection, 
        primaryjoin =(task_field_connection.c.task_id == id),
        secondaryjoin = (task_field_connection.c.field_id == Fields.id),
        backref = "task", order_by = "Fields.order")


#---------------------------------------------------------------------
#                           Users
#---------------------------------------------------------------------
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    #Обязательные поля
    email = db.Column(db.Unicode(64), index=True, unique=True)
    first_name = db.Column(db.Unicode(64))
    last_name = db.Column(db.Unicode(64))
    password = db.Column(db.Unicode(255))

    # Второстепенные
    # Здесь должно быть media
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    avatar_path = db.Column(db.Unicode(255), default = None)
    roles = db.relationship('Roles', cascade="all, delete-orphan", single_parent=True)
    extra_menu_fields = db.relationship("Menu_fields", cascade="all, delete-orphan", single_parent=True)

    assign = db.relationship('Tasks',
        primaryjoin=(Tasks.assigner_id == id),
        backref='assigner', lazy='dynamic')

    accept = db.relationship('Tasks',
        primaryjoin=(Tasks.acceptor_id == id),
        backref='acceptor', lazy='dynamic')
    
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def avatar(self):
        if self.avatar_path is not None:
            return url_for('static', filename="avatars/"+self.avatar_path)
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s=200'.format(
            digest)

    def __repr__(self):
        return '<User {}>'.format(self.email)


class Roles(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.Unicode(64))


profile_field_connection = db.Table("profile_field_connection",
    db.Column('profile_id', db.Integer, db.ForeignKey('profiles.id')),
    db.Column('field_id', db.Integer, db.ForeignKey('fields.id'))
 )
 
class Profiles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("Users", uselist=False, backref = db.backref("profile", uselist=False))

    fields = db.relationship("Fields", 
        secondary = profile_field_connection, 
        primaryjoin =(profile_field_connection.c.profile_id == id),
        secondaryjoin = (profile_field_connection.c.field_id == Fields.id),
        backref = "profile", order_by = "Fields.order")


profile_template_field_connection = db.Table("profile_template_field_connection",
    db.Column('profile_template_id', db.Integer, db.ForeignKey('profile_template.id')),
    db.Column('field_id', db.Integer, db.ForeignKey('fields.id'))
 )

class Profile_template(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    fields = db.relationship("Fields", 
        secondary = profile_template_field_connection, 
        primaryjoin =(profile_template_field_connection.c.profile_template_id == id),
        secondaryjoin = (profile_template_field_connection.c.field_id == Fields.id),
        backref = "profile_template", order_by = "Fields.order")

#Дополнительные ссылки пользователя
class Menu_fields(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.Unicode(64))
    link = db.Column(db.Unicode(255))



#---------------------------------------------------------------------
#                        Sections and pages
#---------------------------------------------------------------------
section_field_connection = db.Table("section_field_connection",
    db.Column('section_id', db.Integer, db.ForeignKey('sections.id')),
    db.Column('field_id', db.Integer, db.ForeignKey('fields.id'))
 )
 
class Sections(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), unique=True)
    display = db.Column(db.Boolean, unique=False, default=True)
    fields = db.relationship("Fields", 
        secondary = section_field_connection, 
        primaryjoin =(section_field_connection.c.section_id == id),
        secondaryjoin = (section_field_connection.c.field_id == Fields.id),
        backref = "section", order_by = "Fields.order")


page_field_connection = db.Table("page_field_connection",
    db.Column('page_id', db.Integer, db.ForeignKey('pages.id')),
    db.Column('field_id', db.Integer, db.ForeignKey('fields.id'))
 )
 
class Pages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'))
    section = db.relationship("Sections", backref = db.backref("pages", order_by="desc(Pages.id)"))
    fields = db.relationship("Fields", 
        secondary = page_field_connection, 
        primaryjoin =(page_field_connection.c.page_id == id),
        secondaryjoin = (page_field_connection.c.field_id == Fields.id),
        backref = "page", order_by = "Fields.order")




