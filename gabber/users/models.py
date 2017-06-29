from gabber import db, bcrypt
from flask_login import UserMixin, AnonymousUserMixin


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

    def is_project_member(self, pid):
        """
        Determines whether or not this user is a member of a project.

        :param pid: the project id to search for
        :return: True if this user is a member, otherwise False.
        """
        from gabber.projects.models import Roles
        match = [i.role_id for i in self.member_of if i.project_id == pid]
        return True if match else False

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


class Anonymous(AnonymousUserMixin, User):
    """
    Required as we access user details via 'current_user', which do not exist for
    an anonymous user. By inheriting from both, and creating a fake user, we overcome that.

    Note: the order of inheritence is critical as we want to use the properties set by AnonymousUserMixin,
    e.g. is_authenticated and is_anonymous,and the methods defined above for a User.
    The way Python implements multiple inheritence is by assigning parent attributes from left-to-right.
    The potential problem is that User inherits from UserMixin where these properties are set to identify a user.
    """
    def __init__(self):
        self.username = 'Guest'
        self.password = 'none'
        self.fullname = 'Yaj Yeniar'