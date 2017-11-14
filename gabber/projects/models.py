from gabber import db


participants = db.Table(
    'participants',
    db.Column('participant_id', db.Integer, db.ForeignKey('participant.id')),
    db.Column('interview_id', db.Integer, db.ForeignKey('interview.id')))


codes_for_connections = db.Table(
    'codes_for_connections',
    db.Column('connection_id', db.Integer, db.ForeignKey('connection.id')),
    db.Column('code_id', db.Integer, db.ForeignKey('code.id'))
)


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

    user = db.relationship("User", back_populates="member_of")
    project = db.relationship("Project", back_populates="members")
    role = db.relationship("Roles", backref=db.backref("member_of", uselist=False))

    def __init__(self, uid, pid, rid):
        self.user_id = uid
        self.project_id = pid
        self.role_id = rid


class Roles(db.Model):
    """
    The roles that can be assigned to a user, and are used to support access control on projects.

    Backrefs:
        one-to-many: a member of a project has one role, though a member can be part of many projects.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)


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
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    # URL-friendly representation of the title
    slug = db.Column(db.String(256), unique=True, index=True)
    description = db.Column(db.String(256))

    creator = db.Column(db.Integer, db.ForeignKey('user.id'))
    # Is the project public or private? True (1) is public.
    type = db.Column(db.SmallInteger, default=1)
    # Should consent (via email) be enabled for this project?
    consent = db.Column(db.SmallInteger, default=0)

    codebook = db.relationship('Codebook', backref='project', lazy='dynamic')
    prompts = db.relationship('ProjectPrompt', backref='project', lazy='dynamic')
    members = db.relationship("Membership", back_populates="project")

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def __init__(self, title, description, creator, visibility):
        from slugify import slugify
        self.title = title
        self.slug = slugify(title)
        self.description = description
        self.creator = creator
        self.type = visibility

    def active_prompts(self):
        """
        Obtains the prompts for this project that are active

        :return: list of Prompt objects that are currently active for this project
        """
        return [prompt for prompt in self.prompts if prompt.is_active]

    def project_as_json(self):
        """
        Create a JSON containing the project title and project prompts (text and images) for use in API.

        Returns: dict of dicts containing the project title and associated prompts formatted for API consumption.
        """
        # TODO: do we really only want active prompts?
        return {
            'theme': self.title,
            'timestamp': self.created_on.strftime("%Y-%m-%d %H:%M:%S"),
            'prompts': [p.serialize() for p in self.prompts if p.is_active],
            'codebook': [c.text for c in self.codebook.first().codes.all()] if self.codebook.first() else []
        }


class ProjectPrompt(db.Model):
    """
    The discussion prompts used within the application for a project

    Backrefs:
        Can refer to its parent project with 'project'

    Relationships:
        one-to-many: a projectPrompt can be used by many interviews
    """
    __tablename__ = 'projectprompt'

    id = db.Column(db.Integer, primary_key=True)
    creator = db.Column(db.Integer, db.ForeignKey('user.id'))
    text_prompt = db.Column(db.String(64))
    image_path = db.Column(db.String(64))
    # Used as a 'soft-delete' to preserve prompt-content for viewing
    is_active = db.Column(db.SmallInteger, default=1)

    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    interviews = db.relationship('Interview', backref='interviews', lazy='dynamic')

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def serialize(self):
        """
        A serialized version of a prompt to use within views

        returns
            dict: a serialization of a prompt
        """
        from flask import request
        from gabber import app
        # Only required as the server is behind a proxy @OpenLab
        uri = (request.url_root[0:(len(request.url_root)-1)] +
               app.static_url_path + '/img/' + str(self.id) + '/')

        return {
            'imageName': uri + self.image_path,
            'prompt': self.text_prompt
        }

class Interview(db.Model):
    """
    An interview between participants for a given ProjectPrompt

    Relationships:
        one-to-many: an interview can have many connections
        one-to-many: an interview must be consented by many participants
        many-to-many: an interview can have many participants
    """
    id = db.Column(db.Integer, primary_key=True)
    audio = db.Column(db.String(260))
    image = db.Column(db.String(260))
    location = db.Column(db.String(10))
    session_id = db.Column(db.String(260))
    creator = db.Column(db.Integer, db.ForeignKey('user.id'))
    prompt_id = db.Column(db.Integer, db.ForeignKey('projectprompt.id'))
    created_on = db.Column(db.DateTime, default=db.func.now())

    connections = db.relationship('Connection', backref='interview', lazy='dynamic')
    participants = db.relationship('Participant', secondary=participants,
                                   backref=db.backref('interviews', lazy='dynamic'),
                                   lazy='dynamic')
    consents = db.relationship('InterviewConsent', backref='interview', lazy='dynamic')

    def project(self):
        """
        There's no relationship between Projects<->Interviews as there is through the ProjectPrompt.

        :returns The project associated with this interview.
        """
        return ProjectPrompt.query.filter_by(id=self.prompt_id).first().project

    def prompt_text(self):
        """
        returns the text of the prompt used for this Interview
        """
        return ProjectPrompt.query.filter_by(id=self.prompt_id).first().text_prompt

    def codebook(self):
        """
        returns all codes associated with this project
        """
        pid = ProjectPrompt.query.filter_by(id=self.prompt_id).first().project_id
        # A hack to support backwards compatibility with projects that don't have a codebook.
        cb = Project.query.filter_by(id=pid).first().codebook.first()
        return [{'text': str(i.text), 'id': i.id} for i in cb.codes.all()] if cb else []


class Connection(db.Model):
    """
    A connection (reflective perspective or opinion) from a user on a segment of an interview.

    Relationships:
        A connection can be associated with many codes.

    Backrefs:
        Can refer to its creator with 'user'
        Can refer to its parent interview with 'interview'
    """
    id = db.Column(db.Integer, primary_key=True)
    # Although many are chosen, a general justification by the user must be provided.
    justification = db.Column(db.String(1120))
    # Where in the interview this connection starts and ends
    start_interval = db.Column(db.Integer)
    end_interval = db.Column(db.Integer, default=0)

    # A connection can be associated with many codes
    codes = db.relationship("Code", secondary=codes_for_connections, backref="connections")
    comments = db.relationship('ConnectionComments', backref='connection', lazy='dynamic')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    interview_id = db.Column(db.Integer, db.ForeignKey('interview.id'))

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def serialize(self):
        """
        A serialized version of a connection to use within views

        returns
            dict: a serialization of a connection
        """
        from gabber.users.models import User
        import datetime
        return {
            'id': self.id,
            'content': u''.join(self.justification).encode('utf-8').strip(),
            'start': self.start_interval,
            'end': self.end_interval,
            'length': self.end_interval - self.start_interval,
            'timestamp': self.created_on.strftime("%Y-%m-%d %H:%M:%S"),
            'days_since': abs((self.created_on - datetime.datetime.now()).days),
            'creator': str(User.query.filter_by(id=self.user_id).first().fullname),
            'creator_id': User.query.filter_by(id=self.user_id).first().id,
            'tags': [str(i.text) for i in self.codes],
            'comments': [i.serialize() for i in self.comments],
            'interview': {
                'id': self.interview_id,
                'topic': ProjectPrompt.query.get(self.interview.prompt_id).text_prompt,
                # TODO: why is this hard-coded?
                'url': "http://gabber.audio" + "/protected/" + Interview.query.get(self.interview_id).audio,
                'uri': "http://gabber.audio/project/session/interview/" + str(self.interview_id) + "?r=" + str(self.id)
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
    text = db.Column(db.String(1120), default=None)

    # If this is zero, then it is a response to the root, e.g. the connection itself.
    parent_id = db.Column(db.Integer, db.ForeignKey('connection_comments.id'))
    children = db.relationship('ConnectionComments', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

    # Who created it and for what purpose?
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    connection_id = db.Column(db.Integer, db.ForeignKey('connection.id'))

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def serialize(self):
        from gabber.users.models import User
        import datetime
        return {
            'id': self.id,
            'pid': self.parent_id,
            'content': str(self.text),
            'timestamp': self.created_on.strftime("%Y-%m-%d %H:%M:%S"),
            'days_since': abs((self.created_on - datetime.datetime.now()).days),
            'creator': str(User.query.filter_by(id=self.user_id).first().fullname),
            'children': [i.serialize() for i in self.children.order_by(db.desc(ConnectionComments.created_on)).all()],
        }


class Participant(db.Model):
    """
    The individual who was part of an interview

    Relationships:
        one-to-many: a participant can have many complex needs.
        one-to-many: a participant can provide consent for many interviews

    Backref:
        Can refer to associated interviews with 'interviews'
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(64))
    age = db.Column(db.Integer)
    gender = db.Column(db.Integer)
    complexneeds = db.relationship('ComplexNeeds', backref="participant", lazy='dynamic')
    consent = db.relationship('InterviewConsent', backref='participant', lazy='dynamic')


class ComplexNeeds(db.Model):
    """
    This is specific to the FF deployment

    Backrefs:
        Can refer to its participant with 'participant'
        Can refer to its interview with 'interview'
    """
    __tablename__ = 'complexneeds'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String)
    timeline = db.Column(db.String)
    month = db.Column(db.String)
    year = db.Column(db.String)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))
    interview_id = db.Column(db.Integer, db.ForeignKey('interview.id'))


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
    name = db.Column(db.String)
    codes = db.relationship('Code', backref="codebook", lazy='dynamic')


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
    note = db.Column(db.String)
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
