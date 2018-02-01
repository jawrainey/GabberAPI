from flask import Blueprint, render_template, request, redirect, url_for, send_from_directory, session
from gabber.projects.models import ProjectPrompt, InterviewSession
from gabber.users.models import User
from gabber.consent import helper
from gabber import db
import json

consent = Blueprint('consent', __name__)


@consent.route('consent/<token>', methods=['POST'])
def validate_consent(token):
    # TODO: user can re-approve their interview until expiration time met.
    token = helper.confirm_consent(token)
    # TODO: is the token-audio and token-email enough to identify a session?
    # The participant who is associated with this particular interview
    usr = User.query.filter_by(email=token['email']).first()
    # TODO: could simplify this via a join
    _session = InterviewSession.query.filter_by(recording_url=token['audio'])
    interview_consent = _session.participants.filter_by(user_id=usr.id).first()
    interview_consent.consent_type = request.form['consent']
    db.session.commit()
    # TODO: snowball && inform user of change?
    return redirect(url_for('main.projects'))


@consent.route('consent/<token>', methods=['GET'])
def display_consent(token):
    consent = helper.confirm_consent(token)

    if not consent:
        return "Approval for this interview has expired."

    # Used to provide temporary access to audio file, which may not be public.
    session['consenting'] = consent['audio']

    # The contents of the interview to display to the user.
    interview_to_approve = [{
        'file': url_for('consent.protected', filename=consent['audio']),
        'trackAlbum': (url_for('consent.protected', filename=consent['image']) if consent['image']
                  else url_for('consent.protected', filename='default.png'))
    }]

    prompt_id = InterviewSession.query.filter_by(
        audio=consent['audio']).first().prompt_id
    prompt = ProjectPrompt.query.filter_by(id=prompt_id).first()

    return render_template('views/consent/consent.html',
                           interview=json.dumps(interview_to_approve),
                           prompt=prompt.text_prompt)


@consent.route('protected/<filename>')
def protected(filename):
    # Allow only fully consented files to be made public,
    # or those consenting to view protected files temporary access
    if helper.consented(filename) or session.get('consenting', None) == filename:
        return send_from_directory('protected', filename)
    return redirect(url_for('main.index'))
