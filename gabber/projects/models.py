from gabber import db


members = db.Table(
    'members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id')))


participants = db.Table(
    'participants',
    db.Column('participant_id', db.Integer, db.ForeignKey('participant.id')),
    db.Column('interview_id', db.Integer, db.ForeignKey('interview.id')))


class Project(db.Model):
    """
    A project is the overarching theme for an interview session

    Backrefs:
        Can refer to associated prompts with 'prompts'
        Can refer to 'members' of a project with 'members'

    Relationships:
        one-to-many: a project can have many prompts
        many-to-many: a project can have many members
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    banner = db.Column(db.String(64))

    creator = db.Column(db.Integer, db.ForeignKey('user.id'))
    type = db.Column(db.SmallInteger, default=1)
    consent = db.Column(db.SmallInteger, default=0)

    prompts = db.relationship('ProjectPrompt', backref='project', lazy='dynamic')
    members = db.relationship('User', secondary=members, back_populates="projects")

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

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
                        for prompt in self.prompts]
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

    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    interviews = db.relationship('Interview', backref='interviews', lazy='dynamic')

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())


class Interview(db.Model):
    """
    An interview between participants for a given ProjectPrompt

    Relationships:
        one-to-many: an interview can have many responses (comments or themes)
        many-to-many: an interview can have many participants
        one-to-many: an interview must be consented by many participants
    """
    id = db.Column(db.Integer, primary_key=True)
    audio = db.Column(db.String(260))
    image = db.Column(db.String(260))
    location = db.Column(db.String(10))
    session_id = db.Column(db.String(260))
    creator = db.Column(db.Integer, db.ForeignKey('user.id'))
    prompt_id = db.Column(db.Integer, db.ForeignKey('projectprompt.id'))
    created_on = db.Column(db.DateTime, default=db.func.now())

    responses = db.relationship('Response', backref='interview', lazy='dynamic')
    participants = db.relationship('Participant', secondary=participants,
                                   backref=db.backref('interviews', lazy='dynamic'),
                                   lazy='dynamic')
    consents = db.relationship('InterviewConsent', backref='interview', lazy='dynamic')

    def prompt_text(self):
        """
        returns the text of the prompt used for this Interview
        """
        return ProjectPrompt.query.filter_by(id=self.prompt_id).first().text_prompt


class Response(db.Model):
    """
    A response to an interview, which is either a comment or annotation

    Although a separate table for annotations could be used, there are many
    shared properties between comments/annotations. However, one disadvantage is that
    annotation text is not stored in a separate table, thereby preventing text duplication.

    Backrefs:
        Can refer to its creator with 'user'
        Can refer to its parent interview with 'interview'
    """
    __tablename__ = 'responses'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(280), default=None)
    start_interval = db.Column(db.Integer)
    end_interval = db.Column(db.Integer, default=0)
    # The response type can either be a comment (0) or an annotation (1).
    type = db.Column(db.Integer)
    reactions = db.Column(db.Integer, default=1)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    interview_id = db.Column(db.Integer, db.ForeignKey('interview.id'))

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def serialize(self):
        """
        A serialized version of a response to use within views

        returns
            dict: a human-readable serialization of the Response object
        """
        from gabber.users.models import User
        import datetime
        return {
            'id': self.id,
            'content': str(self.text),
            'start': self.start_interval,
            'end': self.end_interval,
            'timestamp': self.created_on.strftime("%Y-%m-%d %H:%M:%S"),
            'days_since': abs((self.created_on - datetime.datetime.now()).days),
            'creator': str(User.query.filter_by(id=self.user_id).first().fullname),
            'type': self.type
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
