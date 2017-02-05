from gabber import db, bcrypt


class User(db.Model):
    username = db.Column(db.String(64), unique=True, primary_key=True)
    password = db.Column(db.String(192))
    fullname = db.Column(db.String(64))

    def __init__(self, username, password, fullname):
        self.username = username
        self.set_password(password)
        self.fullname = fullname

    def set_password(self, plaintext):
        self.password = bcrypt.generate_password_hash(plaintext)

    def is_correct_password(self, plaintext):
        return bcrypt.check_password_hash(self.password, plaintext)


participants = db.Table('participants',
    db.Column('participant_id', db.Integer, db.ForeignKey('participant.id')),
    db.Column('interview_id', db.Integer, db.ForeignKey('interview.id')))


class Interview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    audio = db.Column(db.String(260))
    image = db.Column(db.String(260))
    location = db.Column(db.String(10))

    prompt_id = db.Column(db.Integer, db.ForeignKey('projectprompt.id'))
    participants = db.relationship('Participant', secondary=participants,
                                   backref=db.backref('participants', lazy='dynamic'))
    # Each of which provide individual consent for the audio recording.
    consents = db.relationship('InterviewConsent', backref='consentid', lazy='dynamic')


class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(64))
    consent = db.relationship('InterviewConsent', backref='consents', lazy='dynamic')


class InterviewConsent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interview.id'))
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))
    type = db.Column(db.String(50))


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    banner = db.Column(db.String(64))

    creator = db.Column(db.Integer, db.ForeignKey('user.username'))
    prompts = db.relationship('ProjectPrompt', backref='prompts', lazy='dynamic')


class ProjectPrompt(db.Model):
    __tablename__ = 'projectprompt'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    creator = db.Column(db.Integer, db.ForeignKey('user.username'))
    interviews = db.relationship('Interview', backref='interviews', lazy='dynamic')
    text_prompt = db.Column(db.String(64))
    image_path = db.Column(db.String(64))
    audio_path = db.Column(db.String(64))
