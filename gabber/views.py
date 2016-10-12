from gabber import db, helper
from gabber.models import Experience
from flask import Blueprint, redirect, request, \
    render_template, send_from_directory, url_for
import json

main = Blueprint('main', __name__)


@main.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@main.route('projects/', methods=['GET'])
@main.route('projects/<path:project>', methods=['GET'])
def projects(project=None):
    all_projects = helper.commissioned_projects()
    existing = [i['theme'].replace(" ", "-").lower() for i in all_projects]

    if not project:
        return redirect(url_for('main.projects') + existing[0])
    elif project not in existing:
        return redirect(url_for('main.index'))
    else:
        # All experiences that have been consented for public display.
        experiences = Experience.query.filter(
            (Experience.theme == project.replace("-", " ")) &
            ((Experience.consentInterviewer == "ALL") | (Experience.consentInterviewer == "AUD")) &
            ((Experience.consentInterviewee == "ALL") | (Experience.consentInterviewee == "AUD"))).all()

        filtered = []

        for exp in experiences:
            audio = url_for('main.protected', filename=exp.experience)
            # Taking a picture of interviewee is optional. Only show if allowed.
            if (exp.authorImage and exp.consentInterviewer == 'ALL' and exp.consentInterviewee == 'ALL'):
                image = url_for('main.protected', filename=exp.authorImage)
            else:
                image = url_for('main.protected', filename='default.png')

            promptImage = [i['imageName'] for d in all_projects for i in d['prompts'] if i['prompt'] == exp.promptText]

            # The experiences that have been consented to be made public.
            filtered.append({'file': audio, 'thumb': promptImage,
                             'trackAlbum': image, 'trackName': exp.promptText})

        return render_template('explore.html',
                               project_title=project.replace("-", " "),
                               experiences=json.dumps(filtered))


@main.route('consent/<token>', methods=['POST'])
def validate_consent(token):
    # TODO: user can re-approve their experience until expiration time met.
    token = helper.confirm_consent(token)
    experience = Experience.query.filter_by(experience=token[1]).first()
    if token[0] == experience.interviewerEmail:
        experience.consentInterviewer = request.form['consent']
    else:
        experience.consentInterviewee = request.form['consent']
        helper.snowball(experience.intervieweeEmail)
    db.session.commit()
    return redirect(url_for('main.projects'))


@main.route('consent/<token>', methods=['GET'])
def display_consent(token):
    # Get the audio-experience (AX) associated with this consent.
    # The interviewees name and path to the recorded audio is encoded in URI.
    consent = helper.confirm_consent(token)
    # The consent URI exists for a period of time to prevent hacks.
    if not consent:
        return "Approval for this experience has expired."
    # The contents of the experience to display to the user.
    experience_to_approve = [{
        'file': url_for('main.protected', filename=consent[1]),
        'trackAlbum': (url_for('main.protected', filename=consent[2]) if consent[2]
                  else url_for('main.protected', filename='default.png'))
    }]
    # Display the experience that the user needs to approve.
    return render_template('consent.html',
                           experiences=json.dumps(experience_to_approve))


@main.route('protected/<filename>')
def protected(filename):
    # Store on root with nginx config to prevent anyone viewing audios
    # TODO: however, if the filename is known, then anyone can download.
    return send_from_directory('protected', filename)
