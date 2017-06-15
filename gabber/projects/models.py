from gabber import db


members = db.Table(
    'members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id')))


participants = db.Table(
    'participants',
    db.Column('participant_id', db.Integer, db.ForeignKey('participant.id')),
    db.Column('interview_id', db.Integer, db.ForeignKey('interview.id')))


codes_for_connections = db.Table(
    'codes_for_connections',
    db.Column('connection_id', db.Integer, db.ForeignKey('connection.id')),
    db.Column('code_id', db.Integer, db.ForeignKey('code.id'))
)


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
    members = db.relationship('User', secondary=members, back_populates="projects")

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
        from flask import request
        from gabber import app
        # Only required as the server is behind a proxy @OpenLab
        uri = (request.url_root[0:(len(request.url_root)-1)] +
               app.static_url_path + '/img/' + str(self.id) + '/')

        return {
            'theme': self.title,
            'prompts': [{'imageName': uri + prompt.image_path, 'prompt': prompt.text_prompt}
                        for prompt in self.prompts if prompt.is_active]
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
            'content': str(self.justification),
            'start': self.start_interval,
            'end': self.end_interval,
            'timestamp': self.created_on.strftime("%Y-%m-%d %H:%M:%S"),
            'days_since': abs((self.created_on - datetime.datetime.now()).days),
            'creator': str(User.query.filter_by(id=self.user_id).first().fullname),
            'creator_id': User.query.filter_by(id=self.user_id).first().id,
            'codes': [{'code': str(i.text), 'id': i.id} for i in self.codes]
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
