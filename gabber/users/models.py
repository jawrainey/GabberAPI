from gabber import db, bcrypt
from flask_login import UserMixin


class User(UserMixin, db.Model):
    """
    A registered user of the system

    Relationships:
        many-to-many: a user can be a member of many projects
        many-to-many: a user be associated with (has created) many connections
        many-to-many: a user be associated with (has created) many comments
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    password = db.Column(db.String(192))
    fullname = db.Column(db.String(64))

    member_of = db.relationship("Membership", back_populates="user")
    connections = db.relationship('Connection', backref='user', lazy='dynamic')
    connection_comments = db.relationship('ConnectionComments', backref='user', lazy='dynamic')

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
        return self.id

    def role_for_project(self, pid):
        """
        Obtains the role for a project based on its ID

        :param pid: the project id to search for
        :return: The type of role (such as admin, staff, or user), otherwise None
        """
        from gabber.projects.models import Roles
        match = [i.role_id for i in self.member_of if i.project_id == pid]
        return Roles.query.get(match[0]).name if match else None

    def projects(self):
        """
        Determines the projects this user is a member of.

        :return: A list of projects THIS USER is a member of
        """
        from gabber.projects.models import Project
        return [Project.query.get(pid) for pid in [i.project_id for i in self.member_of]]