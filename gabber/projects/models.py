from gabber import db


members = db.Table('members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id')))


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    banner = db.Column(db.String(64))

    creator = db.Column(db.Integer, db.ForeignKey('user.id'))

    prompts = db.relationship('ProjectPrompt', backref='prompts', lazy='dynamic')
    members = db.relationship('User', secondary=members, back_populates="projects")

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())


class ProjectPrompt(db.Model):
    __tablename__ = 'projectprompt'

    id = db.Column(db.Integer, primary_key=True)
    creator = db.Column(db.Integer, db.ForeignKey('user.username'))
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

    created_on = db.Column(db.DateTime, default=db.func.now())

    prompt_id = db.Column(db.Integer, db.ForeignKey('projectprompt.id'))
    participants = db.relationship('Participant', secondary=participants,
                                   backref=db.backref('participants', lazy='dynamic'),
                                   lazy='dynamic')
    # Each of which provide individual consent for the audio recording.
    consents = db.relationship('InterviewConsent', backref='consentid', lazy='dynamic')


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
