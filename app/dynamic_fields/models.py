from app import db

class Text_field(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Unicode(255))
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'))
    media = db.relationship("Media", single_parent=True, uselist=False,
        backref=db.backref("text", uselist=False,cascade="all, delete, delete-orphan"))

class TextArea_field(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Unicode(255))
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'))
    media = db.relationship("Media", single_parent=True, uselist=False,
        backref=db.backref("textArea", uselist=False,cascade="all, delete, delete-orphan"))

class Date_field(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.DateTime())
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'))
    media = db.relationship("Media", single_parent=True, uselist=False,
        backref=db.backref("date", uselist=False,cascade="all, delete, delete-orphan"))

class Link_field(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Unicode(255))
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'))
    media = db.relationship("Media", single_parent=True, uselist=False,
        backref=db.backref("link", uselist=False,cascade="all, delete, delete-orphan"))

class Picture_field(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Unicode(255))
    encrypted_filename = db.Column(db.Unicode(255))
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'))
    media = db.relationship("Media", single_parent=True, uselist=False,
        backref=db.backref("picture", uselist=False,cascade="all, delete, delete-orphan"))

class File_field(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Unicode(255))
    encrypted_filename = db.Column(db.Unicode(255))
    file_type = db.Column(db.Unicode(30))
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'))
    media = db.relationship("Media", single_parent=True, uselist=False,
        backref=db.backref("file", uselist=False,cascade="all, delete, delete-orphan"))

class Number_field(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Float)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'))
    media = db.relationship("Media", single_parent=True, uselist=False,
        backref=db.backref("number", uselist=False,cascade="all, delete, delete-orphan"))

class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)


def default_order_value():
    return Fields.query.count()

class Fields(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.Unicode(64))
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'))
    media = db.relationship("Media", backref=db.backref("field", uselist=False, order_by="Fields.order"))
    display = db.Column(db.Boolean, unique=False, default=True)
    order = db.Column(db.Integer, default = default_order_value, nullable = False)