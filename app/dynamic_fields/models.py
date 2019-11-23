from app import db

class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Unicode(255))
    textArea = db.Column(db.Unicode(255))
    date = db.Column(db.DateTime())
    link = db.Column(db.Unicode(255))
    picture = db.Column(db.Unicode(255))
    number = db.Column(db.Float)

    encrypted_filename = db.Column(db.Unicode(255))
    filename = db.Column(db.Unicode(255))
    file_type = db.Column(db.Unicode(30))

def default_order_value():
    return Fields.query.count()

class Fields(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.Unicode(64))
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'))
    media = db.relationship("Media", backref=db.backref("field", uselist=False, order_by="Fields.order"))
    display = db.Column(db.Boolean, unique=False, default=True)
    order = db.Column(db.Integer, default = default_order_value, nullable = False)