from gabber import app, db
from gabber.consent import helper
from gabber.users.models import User
from gabber.projects.models import Interview, Project, ProjectPrompt, Participant
from gabber.consent.models import InterviewConsent
from flask import jsonify, request, Blueprint, url_for
import json, os

api = Blueprint('api', __name__)


@api.route('projects', methods=['GET'])
def projects():
    # TODO: filter based on user credentials.
    # TODO: use built-in __dict__ and filter to simplify accessing from models.
    res = []
    for project in Project.query.join(ProjectPrompt).all():
        uri = app.config['IMG_FOLDER'] + str(project.id) + '/'
        res.append({
            'theme': project.title,
            'prompts': [
                {'imageName': uri + p.image_path,
                 'prompt' : p.text_prompt}
                for p in project.prompts]})
    return jsonify(res), 200


@api.route('register', methods=['POST'])
def register():
    username = request.form.get('email', None)
    password = request.form.get('password', None)
    fullname = request.form.get('fullname', None)

    if not username or not password or not fullname:
        return jsonify({'error': 'All fields are required.'}), 400

    if username in [user.username for user in db.session.query(User.username)]:
        return jsonify({'error': 'An account with that email exists.'}), 400

    db.session.add(User(username, password, fullname))
    db.session.commit()
    return jsonify({'success': 'A user has been created successfully'}), 200


@api.route('auth', methods=['POST'])
def login():
    username = request.form.get('username', None)
    password = request.form.get('password', None)

    if not username or not password:
        return jsonify({'error': 'All fields are required.'}), 400

    known_users = [user.username for user in db.session.query(User.username)]
    if username and username in known_users:
        user = User.query.filter_by(username=username).first()
        if user and user.is_correct_password(password):
            return jsonify({'success': 'We did it!'}), 200
        return jsonify({'error': 'Incorrect password provided.'}), 400
    return jsonify({'error': 'Username and password do not match.'}), 400


@api.route('upload', methods=['POST'])
def upload():
    """
    Allows a client to upload an audio interview with associated meta-data,
    including details of participants in a JSON encoded file.
    """
    # TODO: return better errors for specific missing data.
    if not request.files or not request.form:
        return jsonify({'error': 'Required data has not been sent.'}), 400

    # TODO: validate fields
    interview = request.files['experience']

    if 'participants' in request.files:
        participants = request.files['participants']

        parts = [Participant(name=i['name'], email=i['email'],
                             consent=[InterviewConsent(type='NONE')])
                 for i in json.loads(participants.read())]

    else:
        email = request.form.get('interviewerEmail', None)
        fname = User.query.filter_by(username=email).first()
        participants = [
            {
                'name': request.form.get('intervieweeName', None),
                'email': request.form.get('intervieweeEmail', None)
            },
            {
                'name': fname.fullname if fname else None,
                'email': email
                }
        ]
        parts = [Participant(name=i['name'], email=i['email'],
                             consent=[InterviewConsent(type='NONE')])
                 for i in participants]

    location = request.form.get('location', None)
    prompt_text = request.form.get('promptText', None)

    # Save file to disk and capture path.
    # TODO: validate: check mime type, use magic_python.
    expPath = os.path.join(app.config['UPLOAD_FOLDER'], interview.filename)
    interview.save(expPath)


    interview = Interview(
        audio = interview.filename,
        image = None,
        location = location,
        prompt_id = ProjectPrompt.query.filter_by(text_prompt=prompt_text).first().id
    )

    # Populating relationship fields outside constructor due to extending lists.
    interview.consents.extend([i.consent.first() for i in parts])
    interview.participants.extend(parts)

    db.session.add(interview)
    db.session.commit()

    for participant in participants:
        if participant['email']:
            helper.email_consent(interview, participant['email'])

    return jsonify({'success': 'We did it!'}), 200
