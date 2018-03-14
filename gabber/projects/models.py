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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), primary_key=True)
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
        membership = Membership(uid=user_id, pid=project_id, rid=Roles.user_role())
        db.session.add(membership)
        db.session.commit()

    @staticmethod
    def leave_project(user_id, project_id):
        membership = Membership.query.filter_by(user_id=user_id, project_id=project_id).first()
        membership.deactivated = True
        db.session.commit()


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
    # When retrieving prompts, only show the active ones.
    prompts = db.relationship(
        'ProjectPrompt',
        backref='project',
        lazy='dynamic',
        primaryjoin="and_(Project.id==ProjectPrompt.project_id, ProjectPrompt.is_active)"
    )
    members = db.relationship("Membership", back_populates="project")

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def __init__(self, title, description, creator, visibility):
        from slugify import slugify
        self.title = title
        self.slug = slugify(title)
        self.description = description
        self.creator = creator
        self.is_public = visibility

    @staticmethod
    def __flatten(_):
        import itertools
        return list(itertools.chain.from_iterable(_))

    @staticmethod
    def all_public_projects():
        return {
            'public': [project for project in Project.query.filter(Project.is_public).all()],
            'personal': []
        }

    def members_json(self):
        """
        Used on the frontend to determine if a given user can view actions for a given project.

        :return:
        """
        return [
            {
                'id': m.user_id,
                'name': m.user.fullname,
                'role': Roles.query.get(m.role_id).name
            }
            for m in self.members
        ]

    def creator_name(self):
        from gabber.users.models import User
        _creator = User.query.get(self.creator)
        return {'name': _creator.fullname, 'id': _creator.id}

    def interview_sessions(self):
        return InterviewSession.query.filter_by(project_id=self.id).all()

    def user_regions_for_interview_sessions(self):
        # All the User Generated Regions for all interview sessions in this project
        uga_per_session = [i.connections.all() for i in self.interview_sessions()]
        return [i.serialize() for i in self.__flatten(uga_per_session)]

    def structural_regions_for_interview_sessions(self):
        # All the Regions for Structural Prompts for all interview sessions in this project
        prompts_per_session = [i.prompts.all() for i in self.interview_sessions()]
        return [i.serialize() for i in self.__flatten(prompts_per_session)]

    def active_prompts(self):
        """
        Obtains the prompts for this project that are active

        :return: list of Prompt objects that are currently active for this project
        """
        return [prompt for prompt in self.prompts if prompt.is_active]

    def serialize(self):
        """
        Create a JSON containing the project title and project prompts (text and images) for use in API.

        Returns: dict of dicts containing the project title and associated prompts formatted for API consumption.
        """
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'description': self.description,
            'creator': self.creator_name(),
            'members': self.members_json(),
            'has_consent': self.has_consent,
            'is_public': self.is_public,
            'timestamp': self.created_on.strftime("%Y-%m-%d %H:%M:%S"),
            'prompts': [p.serialize() for p in self.prompts if p.is_active],
            'topics': [p.serialize() for p in self.prompts if p.is_active]
        }


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
    # Used as a 'soft-delete' to preserve prompt-content for viewing
    is_active = db.Column(db.SmallInteger, default=1)

    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def prompt_image_url(self):
        """
        Generates a timed (two-hour) URL to access the recording of this interview session

        :return: signed URL for the audio recording of the interview
        """
        # TODO: this could be simplified as images for projects could be public?
        # Arguably not, as topics may be sensitive so revealing that information is not good.
        from gabber.utils import amazon
        if 'default' in self.image_path:
            return 'https://gabber.audio/static/default.jpg'
        else:
            return amazon.signed_url(str(self.project_id) + "/prompt-images/" + self.image_path)

    def serialize(self):
        """
        A serialized version of a prompt to use within views

        returns
            dict: a serialization of a prompt
        """
        return {
            'id': self.id,
            'text': self.text_prompt,
            'imageURL': self.prompt_image_url(),
            'creatorID': self.creator,
            'projectID': self.project_id
        }


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

    prompts = db.relationship('InterviewPrompts', backref='interview', lazy='dynamic')
    participants = db.relationship('InterviewParticipants', backref='interview', lazy='dynamic')
    connections = db.relationship(
        'Connection',
        backref='interview',
        lazy='dynamic',
        primaryjoin="and_(InterviewSession.id==Connection.session_id, Connection.is_active)"
    )

    def generate_signed_url_for_recording(self):
        """
        Generates a timed (two-hour) URL to access the recording of this interview session

        :return: signed URL for the audio recording of the interview
        """
        from gabber.utils import amazon
        # TODO: generate URL based on project type and consent process,
        # e.g. something similar to consent.helper.consented
        return amazon.signed_url(str(self.project_id) + "/" + str(self.id))

    def creator(self):
        """
        ??

        :returns ??
        """
        from gabber.users.models import User
        return User.query.get(self.creator_id)

    def project(self):
        """
        The project associated with this interview

        :returns The project associated with this interview.
        """
        return Project.query.get(self.project_id)

    def codebook(self):
        """
        returns all codes associated with this project
        """
        cb = self.project().codebook.first()
        return [{'text': str(i.text), 'id': i.id} for i in cb.codes.all()] if cb else []

    def serialize(self):
        """
        A serialized version of an InterviewSession to use within API

        returns
            dict: a serialization of an InterviewSession
        """
        import datetime
        return {
            'id': self.id,
            'creator': self.creator().fullname,
            'topics': [i.topic() for i in self.prompts.all()],
            'participants': [i.fullname() for i in self.participants.all()],
            'date': self.created_on.strftime("%d-%b-%Y"),
            'location': "TODO: update once GPS added",
            'meta': {
                "numAnnotations": len(self.connections.all()),
                'recordingLength': str(datetime.timedelta(seconds=self.prompts.all()[-1].end_interval))
            }
        }


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

    def topic(self):
        return ProjectPrompt.query.get(self.prompt_id).text_prompt.encode('utf-8')

    def serialize(self):
        """
        A serialized version of a connection to use within views

        returns
            dict: a serialization of a connection
        """
        from flask import url_for
        creator = InterviewSession.query.get(self.interview_id).creator()
        return {
            'id': str(self.id).encode('utf-8'),
            'start': self.start_interval,
            'end': self.end_interval,
            'length': self.end_interval - self.start_interval,
            'creator': str(creator.fullname),
            'creator_id': creator.id,
            'tags': [],
            'interview': {
                'id': str(self.interview_id),
                'topic': ProjectPrompt.query.get(self.prompt_id).text_prompt.encode('utf-8'),
                'url': str(InterviewSession.query.get(self.interview_id).generate_signed_url_for_recording()),
                'uri': url_for('project.session', interview_id=str(self.interview_id), _external=True) + "?r=" + str(self.id)
            }
        }


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

    def fullname(self):
        """
        The project associated with this interview

        :returns The project associated with this interview.
        """
        from gabber.users.models import User
        return User.query.get(self.user_id).fullname


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
    comments = db.relationship('ConnectionComments', backref='connection', lazy='dynamic')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    session_id = db.Column(db.String(260), db.ForeignKey('interview_session.id'))

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def structural_prompt_if_overlapped(self):
        """
        User Annotations are applied on-top of the audio, and each part of the audio
        is associated with a topic being discussed.

        :return: the topic being discussed where this annotation was created.
        """
        for topic in InterviewPrompts.query.filter_by(interview_id=self.session_id).all():
            if topic.start_interval <= self.start_interval <= topic.end_interval:
                return ProjectPrompt.query.get(topic.prompt_id).text_prompt

    def serialize(self):
        """
        A serialized version of a connection to use within views

        returns
            dict: a serialization of a connection
        """
        from gabber.users.models import User
        from flask import url_for
        import datetime
        return {
            'id': self.id,
            'content': u''.join(self.content).encode('utf-8').strip(),
            'start': self.start_interval,
            'end': self.end_interval,
            'length': self.end_interval - self.start_interval,
            'timestamp': self.created_on.strftime("%Y-%m-%d %H:%M:%S"),
            'days_since': abs((self.created_on - datetime.datetime.now()).days),
            'creator': u''.join(User.query.filter_by(id=self.user_id).first().fullname).encode('utf-8').strip(),
            'creator_id': User.query.filter_by(id=self.user_id).first().id,
            'tags': [str(i.text) for i in self.codes],
            'comments': [i.serialize() for i in self.comments],
            'interview': {
                'id': str(self.session_id),
                'topic': str(self.structural_prompt_if_overlapped()),
                'url': str(InterviewSession.query.get(self.session_id).generate_signed_url_for_recording()),
                'uri': url_for('project.session', interview_id=str(self.session_id), _external=True) + "?r=" + str(self.id)
            }
        }


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


    def serialize(self):
        from gabber.users.models import User
        import datetime
        return {
            'id': self.id,
            'pid': self.parent_id,
            'content': str(self.content),
            'timestamp': self.created_on.strftime("%Y-%m-%d %H:%M:%S"),
            'days_since': abs((self.created_on - datetime.datetime.now()).days),
            'creator': str(User.query.filter_by(id=self.user_id).first().fullname),
            'children': [i.serialize() for i in self.replies.order_by(db.desc(ConnectionComments.created_on)).all()],
        }


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


class Playlists(db.Model):
    """
    The name and creator of a playlist.
    TODO: for simplicity this does not consider a collaborative playlist
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    regions = db.relationship('PlaylistRegions', cascade="all,delete", backref="playlist", lazy='dynamic')

    def serialize(self):
        """
        A serialized version of a playlist, including all associated regions

        :return: a serialization (dict) of the playlist region
        """
        return {
            'id': self.id,
            'title': self.name,
            'uid': self.user_id,
            'regions': [r.serialize() for r in self.regions]
        }


class PlaylistRegions(db.Model):
    """
    The regions chosen by a user for a specific playlist
    """
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String(560))
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id'))
    # TODO: previously named regions connections
    region_id = db.Column(db.Integer, db.ForeignKey('connection.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, uid, pid, rid):
        self.user_id = uid
        self.playlist_id = pid
        self.region_id = rid

    def serialize(self):
        """
        A serialized version of a region for a playlist

        :return: a serialization (dict) of the playlist region
        """
        region = Connection.query.get(self.region_id).serialize()
        # Assign the true region ID rather than the ID of this model object
        region['id'] = self.region_id
        region['note'] = self.note
        region['region_id'] = self.region_id
        region['playlist_region_id'] = self.id
        region['playlist_id'] = self.playlist_id
        region['user_id'] = self.user_id
        return region
