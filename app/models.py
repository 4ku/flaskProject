from datetime import datetime
from app import db, login
from flask_login import UserMixin
from hashlib import md5
from werkzeug.security import generate_password_hash, check_password_hash
from flask import url_for


class Media(db.Model):
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
        return '<Media {}, {}, {}, {}, {}, {}, {}>'.format(self.text, self.textArea, 
                self.date, self.encrypted_filename, self.filename, self.link, self.picture)



task_template_media_connection = db.Table("task_template_media_connection",
    db.Column('template_id', db.Integer, db.ForeignKey('task_templates.id')),
    db.Column('media_id', db.Integer, db.ForeignKey('media.id'))
 )

task_media_connection = db.Table("task_media_connection",
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id')),
    db.Column('media_id', db.Integer, db.ForeignKey('media.id'))
 )

class Task_templates(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    fields = db.relationship("Media", 
        secondary = task_template_media_connection, 
        primaryjoin =(task_template_media_connection.c.template_id == id),
        secondaryjoin = (task_template_media_connection.c.media_id == Media.id),
        cascade="all, delete-orphan",single_parent=True,
        backref = "template", order_by = "Media.id")


class Tasks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    assigner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    acceptor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(32), default ="Issued")
    media = db.relationship("Media", 
        secondary = task_media_connection, 
        primaryjoin =(task_media_connection.c.task_id == id),
        secondaryjoin = (task_media_connection.c.media_id == Media.id),
        cascade="all, delete, delete-orphan",single_parent=True,
        backref = "task", order_by = "Media.id")

    




post_template_media_connection = db.Table("post_template_media_connection",
    db.Column('post_template_id', db.Integer, db.ForeignKey('post_templates.id')),
    db.Column('media_id', db.Integer, db.ForeignKey('media.id'))
)

post_media_connection = db.Table("post_media_connection",
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id')),
    db.Column('media_id', db.Integer, db.ForeignKey('media.id'))
 )

class Post_templates(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    fields = db.relationship("Media", 
        secondary = post_template_media_connection, 
        primaryjoin =(post_template_media_connection.c.post_template_id == id),
        secondaryjoin = (post_template_media_connection.c.media_id == Media.id),
        cascade="all, delete-orphan",single_parent=True,
        backref = "post_template", order_by = "Media.id")

class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    media = db.relationship("Media", 
        secondary = post_media_connection, 
        primaryjoin =(post_media_connection.c.post_id == id),
        secondaryjoin = (post_media_connection.c.media_id == Media.id),
        cascade="all, delete, delete-orphan",single_parent=True,
        backref = "post", order_by = "Media.id")





class Users(UserMixin, db.Model):
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
    roles = db.relationship('Roles', secondary='user_roles')
    extra_menu_fields = db.relationship("Menu_fields")

    assign = db.relationship('Tasks',
        primaryjoin=(Tasks.assigner_id == id),
        backref='assigner', lazy='dynamic')

    accept = db.relationship('Tasks',
        primaryjoin=(Tasks.acceptor_id == id),
        backref='acceptor', lazy='dynamic')
    
    post = db.relationship('Posts',
        primaryjoin=(Posts.author_id == id),
        backref='author', lazy='dynamic')

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
    name = db.Column(db.String(64))
    link = db.Column(db.String(255))


class Roles(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))

role_connection = db.Table("user_roles",
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'))
 )


# Хз почему это здесь, нужно разобраться что это вообще делает
@login.user_loader
def load_user(id):
    return Users.query.get(int(id))



