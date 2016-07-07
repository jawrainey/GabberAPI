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
