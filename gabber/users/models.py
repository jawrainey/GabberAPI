from gabber import db, bcrypt
from flask_login import UserMixin


class User(UserMixin, db.Model):
    username = db.Column(db.String(64), unique=True, primary_key=True)
    password = db.Column(db.String(192))
    fullname = db.Column(db.String(64))

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def __init__(self, username, password, fullname):
        self.username = username
        self.password = bcrypt.generate_password_hash(password)
        self.fullname = fullname

    def is_correct_password(self, plaintext):
        return bcrypt.check_password_hash(self.password, plaintext)

    def get_id(self):
        return self.username
