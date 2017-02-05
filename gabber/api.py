from gabber import app, db, helper
from gabber.models import User, Interview, Project, ProjectPrompt, Participant, InterviewConsent
from flask import jsonify, request, Blueprint
import json, os

api = Blueprint('api', __name__)


@api.route('projects', methods=['GET'])
def projects():
    # TODO: filter based on user credentials.
    # TODO: use built-in __dict__ and filter to simplify accessing from models.
    res = []
    for project in Project.query.join(ProjectPrompt).all():
        res.append({
            'theme': project.title,
            'prompts': [
                {'image_name': p.image_path,'prompt' : p.text_prompt}
                for p in project.prompts]})
    return jsonify(res), 200


# requests.post('http://0.0.0.0:8080/api/register',
# data = {'email': 'jawrainey@gmail.com',
# 'password': 'apassword', 'fullname': 'Jay Rainey'})
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


# requests.post('http://0.0.0.0:8080/api/auth',
# data = {'username': 'jawrainey@gmail.com', 'password' : 'apassword'})
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


# requests.post("http://0.0.0.0:8080/api/upload",
# files={'experience': open('audio.mp3', 'rb'),
#        'authorImage': open('gnome.svg', 'rb')},
# data={'interviewerEmail':'jawrainey@gmail.com'})
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
    interview = request.files['interview']
    participants = request.files['participants']
    location = request.form.get('location', None)
    prompt_text = request.form.get('promptText', None)

    # Save file to disk and capture path.
    # TODO: validate: check mime type, use magic_python.
    expPath = os.path.join(app.config['UPLOAD_FOLDER'], interview.filename)
    interview.save(expPath)

    parts = [Participant(name=i['name'], email=i['email'],
                         consent=[InterviewConsent(type='None')])
             for i in json.loads(participants.read())]

    interview = Interview(
        audio = interview.filename,
        image = None,
        location = location,
        project_id = ProjectPrompt.query.filter_by(text_prompt=prompt_text).first().project_id
    )

    # Populating relationship fields outside constructor due to extending lists.
    interview.consents.extend([i.consent.first() for i in parts])
    interview.participants.extend(parts)

    db.session.add(interview)
    db.session.commit()

    # TODO: email all participants for consent
    return jsonify({'success': 'We did it!'}), 200
