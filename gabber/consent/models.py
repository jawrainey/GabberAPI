from gabber import db

class InterviewConsent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interview.id'))
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))
    type = db.Column(db.String(50))

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
