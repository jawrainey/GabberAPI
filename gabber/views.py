# -*- coding: utf-8 -*-

from gabber import app, db
from gabber.models import Experience
from helper import confirm_consent
from flask import render_template, send_from_directory, \
    Markup, flash, url_for, request, redirect


@app.route('/', methods=['GET'])
def index():
    """
    Displays chronologically all experiences that have been made public.
    """
    # All of the experiences that have been consented for public display.
    experiences = Experience.query.filter(Experience.consent != "NONE").all()
    # Pass information we want to display to simplify view logic.
    filtered_experiences = []
    # TODO: transcriptions as "subtitles below audios" for non-natives?
    for experience in experiences:
        # An audio experience is required
        audio = url_for('protected', filename=experience.experience)
        # Taking a picture of interviewee is optional. Only show if allowed.
        if experience.authorImage and experience.consent == 'all':
            image = url_for('protected', filename=experience.authorImage)
        else:
            image = url_for('protected', filename='default.png')
        filtered_experiences.append({'audio': audio, 'image': image})
    return render_template('home.html', experiences=filtered_experiences)


@app.route('/consent/<token>', methods=['GET', 'POST'])
def consent(token):
    # Get the audio-experience (AX) associated with this consent.
    # The interviewees name and path to the recorded audio is encoded in URI.
    consent = confirm_consent(token)
    # The consent URI exists for a period of time to prevent hacks.
    if not consent:
        return "Approval for this experience has expired."

    experience_to_approve = {
        'name': consent[0],
        'audio': url_for('protected', filename=consent[1]),
        'image': consent[2]
    }

    # TODO: move this post operation to individual method.
    if request.method == "POST":
        # TODO: user can re-approve their experience until expiration time met.
        experience = Experience.query.filter_by(experience=consent[1]).first()
        # TODO: validate input -- those haxzors may modify the name property
        # for malicious intent, but for now. Let's make it work.
        experience.consent = request.form['consent']
        db.session.commit()
        # Display a message upon submitting their consent on the home page.
        # That way, if they do approve, they can see their experience too.
        flash(Markup('<h3>Thank you for approving your experience. If you \
                     would like to gather your friends experiences, consider \
                     downloading <a href="/download">gabber</a>.</h3>'))
        return redirect(url_for('index'))
    # Display the experience that the user needs to approve.
    return render_template('consent.html', data=experience_to_approve)


@app.route('/protected/<filename>')
def protected(filename):
    import os
    # Store on root with nginx config to prevent anyone viewing audios
    # TODO: however, if the filename is known, then anyone can download.
    path = os.path.join(app.root_path, 'protected')
    return send_from_directory(path, filename)
