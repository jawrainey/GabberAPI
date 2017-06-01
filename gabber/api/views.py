from gabber import app, db
from gabber.users.models import User
from gabber.projects.models import Interview, Project, ProjectPrompt, Participant, ComplexNeeds
from gabber.consent.models import InterviewConsent
from flask import jsonify, request, Blueprint
import json
import os
from flask_login import login_required


api = Blueprint('api', __name__)


@api.route('projects', methods=['GET'])
def projects():
    # TODO: filter based on user credentials.
    return jsonify([p.project_as_json() for p in Project.query.all()]), 200


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

    #TODO: this is a string that we expect to be in JSON serialised.
    participants = request.form.get('participants', None)
    # All participants involved in this Gabber as Participant objects
    _participants = []

    if participants:
        # Note scope: as an error will be thrown otherwise, we use this below.
        participants = json.loads(participants)

        for p in participants:
            # Has this registered user been previously involved in a Gabber conversation?
            known_participant = Participant.query.filter_by(email=p['Email']).first()
            if known_participant and p["Email"]:
                known_participant.consent.extend([InterviewConsent(type='ALL')])
                _participants.append(known_participant)
            else:
                participant = Participant(name=p['Name'], email=p['Email'], gender=p['Gender'], age=p['Age'])
                # A registered user was involved in this uploaded conversation, but they have not
                if p['Email'] in [i[0] for i in db.session.query(User.username).all()]:
                    participant.name = User.query.filter_by(username=p['Email']).first().fullname
                participant.consent.extend([InterviewConsent(type='ALL')])
                _participants.append(participant)
    else:
        return jsonify({'error': 'No participants were interviewed.'}), 400

    # Only allow those who have been made members of projects (i.e. by admins
    # of those projects) to upload datafiles to that project.
    # Current approach is to lookup prompt based on text rather than ID ... oh my.
    interviewer_id = User.query.filter_by(username=participants[0]['Email']).first().id
    interview_prompt = ProjectPrompt.query.filter(
        ProjectPrompt.text_prompt.like(request.form.get('promptText', None))).first()
    members = Project.query.filter_by(id=interview_prompt.project_id).first().members

    if interviewer_id not in [m.id for m in members]:
        return jsonify({'error': 'You do not have authorization to upload to this project'}), 401

    #TODO: validate: check mime type, use magic_python.
    interviewFile = request.files['experience']
    filename = interviewFile.filename.split(".")[0] + ".mp4"
    interviewFile.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    interview = Interview(
        audio=filename,
        location=request.form.get('location', None),
        creator=interviewer_id,
        session_id=request.form.get('sessionID'),
        prompt_id=interview_prompt.id
    )

    # TODO: how to abstract this per project basis? Currently only for FF deployment.
    # Only attempt to add a participant the needs exist.
    # Checking for string as an empty dict as we have not yet converted this to JSON.
    if [i for i in participants if i['Needs'] and i['Needs'] != '{}']:
        iid = db.session.query(Interview).order_by(Interview.id.desc()).first().id + 1
        # First item is excluded as we want to keep in sync with parts above.
        for index, participant in enumerate(participants[1:]):
            # Do not update as we want to track how the participants needs
            # have changed between interview sessions
            cn = [ComplexNeeds(type=key, timeline=value['timeline'],
                               month=value['month'], year=value['year'],
                               interview_id=iid,
                               participant_id=_participants[index+1].id)
                  for key, value in json.loads(participant['Needs']).items()]
            _participants[index+1].complexneeds.extend(cn)

    # Populating relationship fields outside constructor due to extending lists.
    interview.consents.extend([i.consent.first() for i in _participants])
    interview.participants.extend(_participants)

    db.session.add(interview)
    db.session.commit()

    return jsonify({'success': 'We did it!'}), 200


@api.route('prompt/delete/', methods=['POST'])
@login_required
def delete_prompt():
    """
    Soft-deletes a prompt by flagging it as inactive. This allows prompts to be
    restored (by the admin) and remains associated with interviews for viewing.

    Args:
        prompt-id (int): the ID of the prompt to delete.

    Returns:
        json: 'success' if the prompt was deleted or 'error' and related message.
    """
    pid = int(request.form.get('prompt-id', -1))

    if pid == -1:
        return jsonify({'error': 'A prompt id must be provided.'}), 400
    elif pid not in [prompt.id for prompt in db.session.query(ProjectPrompt.id)]:
        return jsonify({'error': 'The prompt you provided is not known.'}), 400

    prompt = ProjectPrompt.query.filter_by(id=pid).first()
    prompt.is_active = 0
    db.session.commit()

    return jsonify({'success': True}), 200


@api.route('connection/create/', methods=['POST'])
def create_connection():
    """
    Creates a new connection for a user on a segment of an audio.

    Args:
        json:
            content (str): the message
            codes (list): a list of IDs of the codes to associate with this connection
            start (int): the start of a segment on an audio interview
            end (int): the end of a segment on an audio interview
            iid (int): the interview where this connection should be made

    Returns:
        json: 'success' if the prompt was deleted or 'error' and related message.
    """
    from gabber.projects.models import Connection, Code
    from flask_login import current_user

    content = request.get_json()

    # TODO: validation via Flask-RESTful

    connection = Connection(
        justification=content['content'],
        start_interval=content['start'],
        end_interval=content['end'],
        user_id=current_user.id,
        interview_id=content['iid'],
    )

    connection.codes.extend([Code.query.filter_by(id=cid).first() for cid in content['codes']])

    db.session.add(connection)
    db.session.commit()

    return jsonify({'success': True}), 200
