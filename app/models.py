from datetime import datetime
from app import db, login
from flask_user import UserMixin
from hashlib import md5
from werkzeug.security import generate_password_hash, check_password_hash
from flask import url_for

class Task_media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    label = db.Column(db.String())
    text = db.Column(db.String(140))
    date = db.Column(db.DateTime)
    encrypted_filename = db.Column(db.String())
    filename = db.Column(db.String())

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    assigner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    acceptor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    media = db.relationship("Task_media")
    status = db.Column(db.String(140), default ="Issued")

    def __repr__(self):
        return '<Task {}>'.format(self.description)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True)
    email_confirmed_at = db.Column(db.DateTime())
    password = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    avatar_path = db.Column(db.String(), default = None)
    roles = db.relationship('Role', secondary='user_roles')
    
    assign = db.relationship(
        'Task',
        primaryjoin=(Task.assigner_id == id),
        # secondaryjoin=(giveTask.c.task_id == Task.id),
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
            return url_for('static', filename=self.avatar_path)
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s=200'.format(
            digest)
    

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50))

class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))


@login.user_loader
def load_user(id):
    return User.query.get(int(id))




