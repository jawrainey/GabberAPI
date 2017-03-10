from gabber import db, bcrypt
from flask_login import UserMixin
from gabber.projects.models import members


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    password = db.Column(db.String(192))
    fullname = db.Column(db.String(64))
    role = db.Column(db.SmallInteger, default=2)

    projects = db.relationship("Project", secondary=members, back_populates="members")

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def __init__(self, username, password, fullname):
        self.username = username
        self.password = bcrypt.generate_password_hash(password)
        self.fullname = fullname

    def is_correct_password(self, plaintext):
        return bcrypt.check_password_hash(self.password, plaintext)

    def get_id(self):
        """
        Overriding method from UserMixin
        """
        return unicode(self.id)

    def get_role(self):
        """
        returns string form of role to improve readability in views
        """
        roles = {0: 'admin', 1: 'staff', 2: 'user'}
        return roles[self.role]
