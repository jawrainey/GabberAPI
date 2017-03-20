from gabber import db


members = db.Table('members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id')))


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    banner = db.Column(db.String(64))

    creator = db.Column(db.Integer, db.ForeignKey('user.id'))
    type = db.Column(db.SmallInteger, default=1)
    consent = db.Column(db.SmallInteger, default=0)

    prompts = db.relationship('ProjectPrompt', backref='prompts', lazy='dynamic')
    members = db.relationship('User', secondary=members, back_populates="projects")

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())


class ProjectPrompt(db.Model):
    __tablename__ = 'projectprompt'

    id = db.Column(db.Integer, primary_key=True)
    creator = db.Column(db.Integer, db.ForeignKey('user.id'))
    text_prompt = db.Column(db.String(64))
    image_path = db.Column(db.String(64))

    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    interviews = db.relationship('Interview', backref='interviews', lazy='dynamic')

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())


participants = db.Table('participants',
    db.Column('participant_id', db.Integer, db.ForeignKey('participant.id')),
    db.Column('interview_id', db.Integer, db.ForeignKey('interview.id')))


class Interview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    audio = db.Column(db.String(260))
    image = db.Column(db.String(260))
    location = db.Column(db.String(10))
    session_id = db.Column(db.String(260))
    creator = db.Column(db.Integer, db.ForeignKey('user.id'))

    created_on = db.Column(db.DateTime, default=db.func.now())

    prompt_id = db.Column(db.Integer, db.ForeignKey('projectprompt.id'))
    comments = db.relationship('Comment', backref='interview', lazy='dynamic')
    participants = db.relationship('Participant', secondary=participants,
                                   backref=db.backref('participants', lazy='dynamic'),
                                   lazy='dynamic')
    # Each of which provide individual consent for the audio recording.
    consents = db.relationship('InterviewConsent', backref='consentid', lazy='dynamic')


class Comment(db.Model):
    """
    Comments are linear for now (do not have parents/children) for simplicity.

    Backrefs:
        A comment can refer to its creator with 'user'
        A comment can refer to its parent interview with 'interview'
    """
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(280), default=None)
    start_interval = db.Column(db.Integer)
    end_interval = db.Column(db.Integer, default=0)
    reactions = db.Column(db.Integer, default=1)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    interview_id = db.Column(db.Integer, db.ForeignKey('interview.id'))

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def serialize(self):
        from gabber.users.models import User
        return {
            'id': self.id,
            'content': str(self.text),
            'start': self.start_interval,
            'end': self.end_interval,
            'creator': str(User.query.filter_by(id=self.user_id).first().fullname)
        }


class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(64))
    age = db.Column(db.Integer)
    gender = db.Column(db.Integer)
    complexneeds = db.relationship('ComplexNeeds', backref="participant")
    consent = db.relationship('InterviewConsent', backref='consents', lazy='dynamic')


class ComplexNeeds(db.Model):
    """
    This is specific to the FF deployment.
    """
    __tablename__ = 'complexneeds'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String)
    timeline = db.Column(db.String)
    month = db.Column(db.String)
    year = db.Column(db.String)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))
    interview_id = db.Column(db.Integer, db.ForeignKey('interview.id'))
