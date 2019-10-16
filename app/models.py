from datetime import datetime
from app import db, login
from flask_login import UserMixin
from hashlib import md5
from werkzeug.security import generate_password_hash, check_password_hash
from flask import url_for


template_media_connection = db.Table("template_media_connection",
    db.Column('template_id', db.Integer, db.ForeignKey('task_templates.id')),
    db.Column('media_id', db.Integer, db.ForeignKey('task_media.id'))
 )

task_media_connection = db.Table("task_media_connection",
    db.Column('task_id', db.Integer, db.ForeignKey('task.id')),
    db.Column('media_id', db.Integer, db.ForeignKey('task_media.id'))
 )

class Task_media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255))
    textArea = db.Column(db.String(255))
    date = db.Column(db.DateTime())
    encrypted_filename = db.Column(db.String(255))
    filename = db.Column(db.String(255))
    link = db.Column(db.String(255))
    picture = db.Column(db.String(255))
    label = db.Column(db.String(64))

    def __repr__(self):
        return '<Task_media {}, {}, {}, {}, {}, {}, {}>'.format(self.text, self.textArea, 
                self.date, self.encrypted_filename, self.filename, self.link, self.picture)

class Task_templates(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    fields = db.relationship("Task_media", 
        secondary = template_media_connection, 
        primaryjoin =(template_media_connection.c.template_id == id),
        secondaryjoin = (template_media_connection.c.media_id == Task_media.id),
        cascade="all, delete-orphan",single_parent=True,
        backref = "template", order_by = "Task_media.id")


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    assigner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    acceptor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    media = db.relationship("Task_media", 
        secondary = task_media_connection, 
        primaryjoin =(task_media_connection.c.task_id == id),
        secondaryjoin = (task_media_connection.c.media_id == Task_media.id),
        cascade="all, delete, delete-orphan",single_parent=True,
        backref = "task", order_by = "Task_media.id")

    status = db.Column(db.String(32), default ="Issued")

    def __repr__(self):
        return '<Task {}>'.format(self.description)


class Menu_field(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(64))
    link = db.Column(db.String(255))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    #Обязательные поля
    email = db.Column(db.String(64), index=True, unique=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    password = db.Column(db.String(255))

    # Второстепенные
    # Здесь должно быть media
    registered = db.Column(db.Boolean, unique=False, default=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    avatar_path = db.Column(db.String(255), default = None)
    roles = db.relationship('Role', secondary='user_roles')
    extra_menu_fields = db.relationship("Menu_field")

    assign = db.relationship(
        'Task',
        primaryjoin=(Task.assigner_id == id),
        backref='assigner', lazy='dynamic')

    accept = db.relationship(
        'Task',
        primaryjoin=(Task.acceptor_id == id),
        backref='acceptor', lazy='dynamic')


    def __repr__(self):
        return '<User {}>'.format(self.username)

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


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))


class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))


# Хз почему это здесь, нужно разобраться что это вообще делает
@login.user_loader
def load_user(id):
    return User.query.get(int(id))



