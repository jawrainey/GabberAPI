# -*- coding: utf-8 -*-
"""
???
"""
from gabber import db
from flask_sqlalchemy import BaseQuery

codes_for_connections = db.Table(
    'codes_for_connections',
    db.Column('connection_id', db.Integer, db.ForeignKey('connection.id')),
    db.Column('code_id', db.Integer, db.ForeignKey('code.id'))
)


class QueryWithSoftDelete(BaseQuery):
    """
    Prepends is_active to the query object SQL statement.

    Note: this is modified version of Miguel Grinberg's SoftDelete: https://goo.gl/QFJK1c
    """
    _with_deleted = False

    def __new__(cls, *args, **kwargs):
        """
        The query object is created and modified here as in the init it is immutable.
        Being able to create a new instance of the query also enables overriding Object.query.get()
        """
        obj = super(QueryWithSoftDelete, cls).__new__(cls)
        # Optionally reset the query, e.g. to get all data including deleted.
        obj._with_deleted = kwargs.pop('_with_deleted', False)
        if len(args) > 0:
            super(QueryWithSoftDelete, obj).__init__(*args, **kwargs)
            return obj.filter_by(is_active=True) if not obj._with_deleted else obj
        return obj

    def __init__(self, *args, **kwargs):
        pass

    def with_deleted(self):
        """
        Lets QueryObject.query.with_deleted() be used to retrieve all the objects,
        including those that have been deleted.
        """
        return self.__class__(db.class_mapper(self._mapper_zero().class_),
                              session=db.session(), _with_deleted=True)

    def _get(self, *args, **kwargs):
        """
        This calls the original query.get function from the base class
        """
        return super(QueryWithSoftDelete, self).get(*args, **kwargs)

    def get(self, *args, **kwargs):
        """
        If QueryObject (say Project).query.get() is called it does not like the
        filter clause pre-loaded, so this workaround calls get without it.
        """
        obj = self.with_deleted()._get(*args, **kwargs)
        return obj if obj is None or self._with_deleted or obj.is_active else None


class Membership(db.Model):
    """
    Holds the user membership for projects and the users role in this project.

    Note: an association object is used to hold the role ontop of the many-to-many relationship(s).

    Relationships:
        many-to-many: a user can be a member of many projects
        many-to-many: a project can have many members
        one-to-one: each membership must have one role
    """
    id = db.Column(db.Integer, autoincrement=True, index=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    # Used to determine if a user has confirmed their membership
    confirmed = db.Column(db.Boolean, default=False)
    # Should someone leave a project, we make deactivate their membership for posterity.
    deactivated = db.Column(db.Boolean, default=False)
    # Determines (1) when membership was sent, and (2) for how long they were a member.
    date_sent = db.Column(db.DateTime, default=db.func.now())
    date_accepted = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    user = db.relationship("User", back_populates="member_of")
    project = db.relationship("Project", back_populates="members")
    role = db.relationship("Roles", backref=db.backref("member_of", uselist=False))

    def __init__(self, uid, pid, rid, confirmed=False):
        self.user_id = uid
        self.project_id = pid
        self.role_id = rid
        self.confirmed = confirmed

    @staticmethod
    def join_project(user_id, project_id):
        membership = Membership(uid=user_id, pid=project_id, rid=Roles.user_role(), confirmed=True)
        db.session.add(membership)
        db.session.commit()
        return membership

    @staticmethod
    def leave_project(user_id, project_id):
        # Given we store all the history of project joins/leaves,
        # when a user requests to leave only their most recent record is presented
        membership = Membership.query.filter_by(
            user_id=user_id,
            project_id=project_id,
            deactivated=False
        ).order_by(Membership.id.desc()).first()
        membership.deactivated = True
        db.session.commit()
        return membership


class Roles(db.Model):
    """
    The roles that can be assigned to a user, and are used to support access control on projects.

    Backrefs:
        one-to-many: a member of a project has one role, though a member can be part of many projects.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)

    @staticmethod
    def user_role():
        return Roles.query.filter_by(name='user').first().id


class Project(db.Model):
    """
    A project is the overarching theme for an interview session

    Backrefs:
        Can refer to associated prompts with 'prompts'
        Can refer to 'members' of a project with 'members'

    Relationships:
        one-to-many: a project can have many prompts
        one-to-many: a project can have many codebooks
        many-to-many: a project can have many members
    """

    query_class = QueryWithSoftDelete

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    # URL-friendly representation of the title
    slug = db.Column(db.String(256), unique=True, index=True)
    description = db.Column(db.String(256))
    # Used as a 'soft-delete' to preserve prompt-content for viewing
    is_active = db.Column(db.Boolean, default=True)

    creator = db.Column(db.Integer, db.ForeignKey('user.id'))
    # Is the project public or private? True (1) is public.
    has_consent = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean, default=True)

    codebook = db.relationship('Codebook', backref='project', lazy='dynamic')
    prompts = db.relationship('ProjectPrompt', backref='project', lazy='dynamic')

    members = db.relationship('Membership', back_populates='project',
                              primaryjoin='and_(Project.id==Membership.project_id, Membership.deactivated == False)')

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def __init__(self, title, description, creator, is_public):
        from slugify import slugify
        self.title = title
        self.slug = slugify(title)
        self.description = description
        self.creator = creator
        self.is_public = is_public


class ProjectPrompt(db.Model):
    """
    The discussion prompts used within the application for a project

    Backrefs:
        Can refer to its parent project with 'project'

    Relationships:
        one-to-many: a projectPrompt can be used by many interviews
    """
    id = db.Column(db.Integer, primary_key=True)
    creator = db.Column(db.Integer, db.ForeignKey('user.id'))
    # TODO: these should both be renamed
    text_prompt = db.Column(db.String(260))
    image_path = db.Column(db.String(260), default="default.jpg")
    is_active = db.Column(db.SmallInteger, default=1)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())


class InterviewSession(db.Model):
    """
    An interview session between participants for a set of prompts

    Relationships:
        one-to-many: an interview must be consented by many participants
        one-to-many: many participants can be involved in one interview
        one-to-many: an interview can have many connections
    """
    # The ID is also used as the RecordingFilename when storing the file;
    id = db.Column(db.String(260), primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    created_on = db.Column(db.DateTime, default=db.func.now())

    prompts = db.relationship('InterviewPrompts', backref='interview', lazy='joined')
    participants = db.relationship('InterviewParticipants', backref='interview', lazy='joined')
    connections = db.relationship(
        'Connection',
        backref='interview',
        lazy='joined',
        primaryjoin="and_(InterviewSession.id==Connection.session_id, Connection.is_active)"
    )

    def generate_signed_url_for_recording(self):
        """
        Generates a timed (two-hour) URL to access the recording of this interview session

        :return: signed URL for the audio recording of the interview
        """
        from gabber.utils import amazon
        return amazon.signed_url(self.project_id, self.id)


class InterviewPrompts(db.Model):
    """
    These are the annotations created during the capture of an interview, which differ
    from an annotation below as they are used for structural representation ontop of the recording.

    Backref:
        Can refer to associated interview with 'interview'
    """
    id = db.Column(db.Integer, primary_key=True)
    prompt_id = db.Column(db.Integer, db.ForeignKey('project_prompt.id'))
    interview_id = db.Column(db.String(260), db.ForeignKey('interview_session.id'))
    # Where in the structural annotation starts and ends
    start_interval = db.Column(db.Integer)
    end_interval = db.Column(db.Integer, default=0)

    topic = db.relationship("ProjectPrompt", lazy='joined')


class InterviewParticipants(db.Model):
    """
    The individual who was part of an interview

    Backref:
        Can refer to associated interview with 'interview'
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    interview_id = db.Column(db.String(260), db.ForeignKey('interview_session.id'))
    # 0: private, 1: public, 2: delete
    consent_type = db.Column(db.Integer, default=0)
    # 0: interviewee, 1: interviewer
    # Although this could be inferred through interview.creator, this simplifies queries
    role = db.Column(db.Boolean, default=False)

    user = db.relationship("User", back_populates="participant_of")

    def __init__(self, user_id, session_id, role):
        self.user_id = user_id
        self.interview_id = session_id
        self.role = role


class Connection(db.Model):
    """
    A connection (reflective perspective or opinion) from a user on a segment of an interview.

    Relationships:
        A connection can be associated with many codes.

    Backrefs:
        Can refer to its creator with 'user'
        Can refer to its parent interview with 'interview'
    """
    query_class = QueryWithSoftDelete

    # TODO: this should be renamed to UserAnnotation as connection is outdated
    id = db.Column(db.Integer, primary_key=True)
    # Although many are chosen, a general justification by the user must be provided.
    content = db.Column(db.String(1024))
    # Where in the interview this connection starts and ends
    start_interval = db.Column(db.Integer)
    end_interval = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    # A connection can be associated with many codes
    tags = db.relationship("Code", secondary=codes_for_connections, backref="connections")
    comments = db.relationship(
        'ConnectionComments',
        backref='connection',
        lazy='joined',
        primaryjoin='and_(Connection.id==ConnectionComments.connection_id, ConnectionComments.parent_id == None)'
    )

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    session_id = db.Column(db.String(260), db.ForeignKey('interview_session.id'))

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())


class ConnectionComments(db.Model):
    """
    Comments can be made on connections (where parent is 0) and on themselves.

    Backrefs:
        A comment can refer to its creator with 'user'
        A comment can refer to the connection its associated with via 'connection'
    """
    __tablename__ = 'connection_comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(1024), default=None)

    is_active = db.Column(db.Boolean, default=True)

    # If this is NULL, then it is a response to the root, e.g. the annotation itself.
    parent_id = db.Column(db.Integer, db.ForeignKey('connection_comments.id'), nullable=True)
    replies = db.relationship('ConnectionComments', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

    # Who created it and for what purpose?
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    connection_id = db.Column(db.Integer, db.ForeignKey('connection.id'))

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def __init__(self, content, pid, uid, aid):
        self.content = content
        self.parent_id = pid
        self.user_id = uid
        self.connection_id = aid


class Codebook(db.Model):
    """
    Holds a set of codes related to a project; acts as qualitative codebook.

    Backrefs:
        Can refer to its associated project with 'project'

    Relationships:
        one-to-many: a codebook can have many codes
    """
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    # Used to differentiate and support multiple codebooks for the same project
    tags = db.relationship('Code', backref="codebook", lazy='dynamic')
    name = db.Column(db.String(40))


class Code(db.Model):
    """
    Holds a textual "Code" for a specific Codebook.

    Note: this approach is not ideal as we would have duplicate codes across books.

    Backref:
        Can refer to associated codebook with 'codebook'
    """
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(64))
    codebook_id = db.Column(db.Integer, db.ForeignKey('codebook.id'))
