from datetime import datetime
from app import db, login
from flask_login import UserMixin
from hashlib import md5
from werkzeug.security import generate_password_hash, check_password_hash
from flask import url_for


class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Unicode(255))
    textArea = db.Column(db.Unicode(255))
    date = db.Column(db.DateTime())
    encrypted_filename = db.Column(db.Unicode(255))
    filename = db.Column(db.Unicode(255))
    link = db.Column(db.Unicode(255))
    picture = db.Column(db.Unicode(255))

    def __repr__(self):
        return '<Media {}, {}, {}, {}, {}, {}, {}>'.format(self.text, self.textArea, 
                self.date, self.encrypted_filename, self.filename, self.link, self.picture)

class Fields(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.Unicode(64))
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'))
    media = db.relationship("Media", backref=db.backref("field", uselist=False))
    display = db.Column(db.Boolean, unique=False, default=True)



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
        cascade="all, delete-orphan",single_parent=True,
        backref = "task_template", order_by = "Fields.id")


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
    media = db.relationship("Fields", 
        secondary = task_field_connection, 
        primaryjoin =(task_field_connection.c.task_id == id),
        secondaryjoin = (task_field_connection.c.field_id == Fields.id),
        cascade="all, delete, delete-orphan",single_parent=True,
        backref = "task", order_by = "Fields.id")





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
    roles = db.relationship('Roles', secondary='user_roles')
    extra_menu_fields = db.relationship("Menu_fields")

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


#Дополнительные ссылки пользователя
class Menu_fields(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.Unicode(64))
    link = db.Column(db.Unicode(255))


class Roles(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.Unicode(64))

role_connection = db.Table("user_roles",
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'))
 )


