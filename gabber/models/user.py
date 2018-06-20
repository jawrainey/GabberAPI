from flask_bcrypt import Bcrypt
from .. import db
from uuid import uuid4

bcrypt = Bcrypt()


class ResetTokens(db.Model):
    """
    Used to determine if a token has been previously used to reset a users password.
    From a UX/SEC perspective, if it has, then we do not want the user to be able to reset it again.
    """
    token = db.Column(db.String(192), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_active = db.Column(db.Boolean, default=True)


class SessionConsent(db.Model):
    """
    Stores the type of consent provided by a participant for their Gabber,
    which is used to determine if a Gabber has been consented to be public.

    Type options include:
        public: anyone can view/listen to the recording
        members: only members of the project can view/listen to the recording
        private: only participants of the project can view/listen to the recording
    """
    id = db.Column(db.Integer, primary_key=True)
    # Options include: public, private, none.
    type = db.Column(db.String(50), default='none')
    token = db.Column(db.String(260), unique=True)
    session_id = db.Column(db.String(260), db.ForeignKey('interview_session.id'))
    participant_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())


class User(db.Model):
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
    verified = db.Column(db.Boolean, default=False)

    participant_of = db.relationship("InterviewParticipants", lazy='joined')
    member_of = db.relationship("Membership", back_populates="user", lazy='dynamic')
    connections = db.relationship('Connection', backref='user', lazy='dynamic')
    connection_comments = db.relationship('ConnectionComments', backref='user', lazy='dynamic')

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def __init__(self, fullname, email, password, registered=False):
        self.fullname = fullname
        self.email = email
        self.set_password(password)
        self.registered = registered

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

    def is_project_member(self, pid):
        """
        Determines whether or not this user is a member of a project.

        :param pid: the project id to search for
        :return: True if this user is a member, otherwise False.
        """
        match = [i.role_id for i in self.member_of if int(i.project_id) == int(pid) if not i.deactivated]
        return True if match else False

    def role_for_project(self, pid):
        """
        Obtains the role for a project based on its ID

        :param pid: the project id to search for
        :return: The type of role (such as admin, staff, or user), otherwise None
        """
        from ..models.projects import Roles
        match = [i.role_id for i in self.member_of if i.project_id == pid if i.confirmed and not i.deactivated]
        return Roles.query.get(match[0]).name if match else 'participant'
