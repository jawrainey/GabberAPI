# -*- coding: utf-8 -*-

from gabber import db, helper
from gabber.models import Experience
from flask import Blueprint, redirect, request, \
    render_template, send_from_directory, url_for
import json

main = Blueprint('main', __name__)


@main.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@main.route('listen', methods=['GET'])
def listen():
    """
    Displays chronologically all experiences that have been made public.
    """
    # All of the experiences that have been consented for public display.
    from sqlalchemy import or_
    C = ["NONE", "ANON"]
    experiences = Experience.query.filter(or_(
        ~Experience.consentInterviewer.in_(C),
        ~Experience.consentInterviewee.in_(C))).all()
    # Pass information we want to display to simplify view logic.
    filtered_experiences = []
    # TODO: transcriptions as "subtitles below audios" for non-natives?
    for experience in experiences:
        # An audio experience is required
        audio = url_for('main.protected', filename=experience.experience)
        # Taking a picture of interviewee is optional. Only show if allowed.
        if (experience.authorImage and
            experience.consentInterviewer == 'ALL' and
            experience.consentInterviewee == 'ALL'):
            # TODO: returns a 404... it would be better if a request was not
            # made, e.g. we can ask the database if there is an authorImage,
            # if there is, then no worries...
            image = url_for('main.protected', filename=experience.authorImage)
        else:
            image = url_for('main.protected', filename='default.png')
        # TODO: need to re-write jaudio such that the correct names are relevant
        # to my own use. Used it for speed, but now it's blah...
        mapPrompts = {"Getting involved in volunteering": p(1),
                      "Benefits of volunteering": p(2),
                      "Bad things about volunteering": p(3),
                      "Are volunteers appreciated enough?": p(4),
                      "Do volunteers have much freedom and flexibility?": p(5),
                      "Is it always clear what is expected of volunteers?": p(6),
                      "Do volunteers have much say in what they do?": p(7)}

        promptImage = mapPrompts.get(experience.promptText, None)
        filtered_experiences.append({'file': audio,
                                     'thumb': promptImage,
                                     'trackAlbum': image,
                                     'trackName': experience.promptText})
    return render_template('explore.html',
                           experiences=json.dumps(filtered_experiences))


def p(f):
    # Returns the URL to the prompt by filename...
    return url_for('static', filename='img/prompts/' + str(f) + '.jpg')


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
    return redirect(url_for('main.listen'))


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
