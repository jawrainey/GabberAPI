from gabber import db


class InterviewConsent(db.Model):
    """
    Stores the type of consent provided by a participant for their interview,
    which is used to determine if an interview has been consented to be public.

    Backrefs:
        Can refer to its participant via 'participant'
        Can refer to its interview via 'interview'
    """
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interview.id'))
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))
    type = db.Column(db.String(50))

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
