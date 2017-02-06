from gabber import db, helper
from gabber.models import Interview, Participant, InterviewConsent, Project, ProjectPrompt
from flask import Blueprint, redirect, request, \
    render_template, send_from_directory, session, url_for
import json

main = Blueprint('main', __name__)


@main.route('/', methods=['GET'])
def index():
    return render_template('views/index.html')


@main.route('about', methods=['GET'])
def about():
    return render_template('views/about.html')


@main.route('projects/', methods=['GET'])
@main.route('projects/<path:project>', methods=['GET'])
def projects(project=None):
    all_projects = db.session.query(Project).all()
    existing = [i.title.replace(" ", "-").lower() for i in all_projects]
    if not project:
        return render_template('views/projects.html', projects=all_projects)
    elif project not in existing:
        return redirect(url_for('main.index'))
    else:
        # TODO: challenge -- can the below be encapsulated into one query?
        # Select all interviews that for this project (based on prompt_id) that
        # have been fully consented by all participants for the audio interview.
        selected_project = Project.query.filter_by(title=project).first()
        prompt_ids = [i.id for i in selected_project.prompts.all()]
        interviews = db.session.query(Interview) \
            .filter(Interview.prompt_id.in_(prompt_ids)).all()

        consented_interviews = [interview for interview in interviews
                                if 'NONE' not in
                                [cons.type for cons in interview.consents.all()]]

        # Display limited interview information to the viewer.
        interviews_to_display = []
        for interview in consented_interviews:
            # TODO: how to determine the prompt for this interview?
            prompt = ProjectPrompt.query.filter_by(id=interview.prompt_id).first()
            # The interviews that have been consented to be made public.
            interviews_to_display.append({
                'file': url_for('main.protected', filename=interview.audio),
                'thumb': prompt.image_path,
                'trackAlbum': 'default.png',
                'trackName': prompt.text_prompt})

        return render_template('views/project.html',
                               project_title=project.replace("-", " "),
                               interviews=json.dumps(interviews_to_display))


@main.route('consent/<token>', methods=['POST'])
def validate_consent(token):
    # TODO: user can re-approve their interview until expiration time met.
    token = helper.confirm_consent(token)
    # The participant who is associated with this particular interview
    interviewConsent = InterviewConsent.query.join(Participant)\
        .filter(InterviewConsent.interview_id == \
                Interview.query.filter_by(audio = token['audio']).first().id,
                Participant.email == token['email']).first()
    interviewConsent.type = request.form['consent']
    db.session.commit()
    # TODO: snowball && inform user of change?
    return redirect(url_for('main.projects'))


@main.route('consent/<token>', methods=['GET'])
def display_consent(token):
    consent = helper.confirm_consent(token)

    if not consent:
        return "Approval for this interview has expired."

    # Used to provide temporary access to audio file, which may not be public.
    session['consenting'] = consent['audio']

    # The contents of the interview to display to the user.
    interview_to_approve = [{
        'file': url_for('main.protected', filename=consent['audio']),
        'trackAlbum': (url_for('main.protected', filename=consent['image']) if consent['image']
                  else url_for('main.protected', filename='default.png'))
    }]

    prompt_id = Interview.query.filter_by(
        audio=consent['audio']).first().prompt_id
    prompt = ProjectPrompt.query.filter_by(id=prompt_id).first()

    return render_template('views/consent.html',
                           interview=json.dumps(interview_to_approve),
                           prompt=prompt.text_prompt)


@main.route('protected/<filename>')
def protected(filename):
    # Allow only fully consented files to be made public,
    # or those consenting to view protected files temporary access
    if helper.consented(filename) or session.get('consenting', None) == filename:
        return send_from_directory('protected', filename)
    return redirect(url_for('main.index'))
