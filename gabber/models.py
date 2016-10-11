from gabber import db, bcrypt


class User(db.Model):
    __tablename__ = 'users'

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


class Experience(db.Model):
    __tablename__ = 'experiences'

    experience = db.Column(db.String(260), unique=True, primary_key=True)
    authorImage = db.Column(db.String(260))
    interviewerEmail = db.Column(db.String(64))
    intervieweeEmail = db.Column(db.String(64))
    intervieweeName = db.Column(db.String(64))
    location = db.Column(db.String(10))
    promptText = db.Column(db.String(64))
    consentInterviewer = db.Column(db.String(4))
    consentInterviewee = db.Column(db.String(4))
    theme = db.Column(db.String(240))
