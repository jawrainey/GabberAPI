from gabber import db, bcrypt
from flask_login import UserMixin, AnonymousUserMixin
from uuid import uuid4


class ResetTokens(db.Model):
    """
    Used to determine if a token has been previously used to reset a users password.
    From a UX/SEC perspective, if it has, then we do not want the user to be able to reset it again.
    """
    token = db.Column(db.String(192), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_active = db.Column(db.Boolean, default=True)


class User(UserMixin, db.Model):
    """
    A registered user of the system

    Relationships:
        many-to-many: a user can be a member of many projects
        many-to-many: a user be associated with (has created) many connections
        many-to-many: a user be associated with (has created) many comments
    """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True)
    password = db.Column(db.String(192))
    fullname = db.Column(db.String(64))
    # User accounts are created when participating in a session; once registered,
    # this is changed so that we can identify between registers/unregistered users.
    registered = db.Column(db.Boolean, default=False)

    member_of = db.relationship("Membership", back_populates="user", lazy='dynamic')
    connections = db.relationship('Connection', backref='user', lazy='dynamic')
    connection_comments = db.relationship('ConnectionComments', backref='user', lazy='dynamic')

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def __init__(self, fullname, email, password):
        self.fullname = fullname
        self.email = email
        self.set_password(password)

    @staticmethod
    def create_unregistered_user(fullname, email):
        user = User(fullname, email, uuid4().hex)
        db.session.add(user)
        db.session.commit()
        return user

    def set_password(self, plaintext):
        self.password = bcrypt.generate_password_hash(plaintext)

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
        match = [i.role_id for i in self.member_of if int(i.project_id) == int(pid)]
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
        The available projects for this user.

        :return: A list of public and private projects for this user
        """
        from gabber.projects.models import Project

        is_member = []
        not_member_and_public = []

        memberships = [i.project_id for i in self.member_of]

        for project in Project.query.order_by(Project.id.desc()).all():
            if project.id in memberships:
                is_member.append(project)
            if project.id not in memberships and project.is_public:
                not_member_and_public.append(project)

        return {
            'personal': is_member,
            'public': not_member_and_public
        }


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
