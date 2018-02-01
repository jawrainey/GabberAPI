from gabber import app, db
from gabber.users.models import User
from gabber.projects.models import InterviewSession, Project, ProjectPrompt, Connection
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

    if username in [user.username for user in db.session.query(User.email)]:
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

    known_users = [user.username for user in db.session.query(User.email)]
    if username and username in known_users:
        user = User.query.filter_by(username=username).first()
        if user and user.is_correct_password(password):
            return jsonify({'success': 'We did it!'}), 200
        return jsonify({'error': 'Incorrect password provided.'}), 400
    return jsonify({'error': 'Username and password do not match.'}), 400


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


@api.route('connection/comment/create/', methods=['POST'])
def create_comment_on_connection():
    """
    Creates a new comment on a connection or a response to another comment.

    Args:
        json:
            comment (str): the writing response to a connection or another comment
            uid (int): the ID of the user creating the comment
            cid (int): the ID of the connection where this comment was made
            pid (int): the ID of the parent where the comment is being created.

    Returns:
        json: 'success' if the comment was created or 'error' and related message.
    """
    from gabber.projects.models import ConnectionComments
    from flask_login import current_user

    content = request.get_json()
    # TODO: validation
    response = content.get('comment', None)
    uid = content.get('uid', current_user.id)
    cid = content.get('cid', None)
    pid = content.get('pid', content['cid'])

    response = ConnectionComments(text=response, user_id=uid, connection_id=cid, parent_id=pid)

    db.session.add(response)
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


@api.route('member/add/', methods=['POST'])
def add_member():
    """
    Allows a user with an admin role to add a registered user to their project.

    Args:
        json:
            uid (int): the user id of the individual making this request
            pid (int): the project the admin wants to add a member to
            email (str): the email address of the registered user to add

    Returns:
        json: 'success' if the prompt was deleted or 'error' and related message.
    """
    from gabber.projects.models import Membership, Project, Roles

    req = request.get_json()

    uid = req.get('uid', None)
    pid = req.get('pid', None)
    email = req.get('email', None)

    # The user must exist before it can become a project member
    if email and email not in [user.username for user in db.session.query(User.email)]:
        return jsonify({'error': 'This email (%s) is not linked to a registered account.' % email}), 400

    # The user must be an admin of this particular project
    role_for_this_project = User.query.get(uid).member_of.filter_by(project_id=pid).first().role_id
    if role_for_this_project is not Roles.query.filter_by(name='admin').first().id:
        return jsonify({'error': 'You must be an admin of a project to add members to it.'}), 400

    # The project must exist before we try to get it
    project = Project.query.get(pid)
    if not project:
        return jsonify({'error': 'No project exists with that ID'}), 400

    id_of_member_to_add = User.query.filter_by(username=email).first().id

    # A user cannot be a member of the project more than once
    if id_of_member_to_add and id_of_member_to_add in [m.user_id for m in project.members]:
        return jsonify({'error': 'A user with that email is already a member of %s' % project.title}), 400

    # Make this registered user a member of this project
    user_role = Roles.query.filter_by(name='staff').first().id
    membership = Membership(uid=id_of_member_to_add, pid=pid, rid=user_role)
    project.members.append(membership)

    db.session.add(project)
    db.session.commit()

    return jsonify({'success': True}), 200


@api.route('log/event', methods=['POST'])
def log_event():
    """
    Logs a user event, such as a click, to the database to support interaction analytics.

    Args:
        json:
            type (int): Refers to the type of the event named within the database. For a full list, see: log/events
            content (json): Contains data that uniquely identifies the given event, such as region ID.

    Returns:
        json: 'success' if the event was logged to the database correctly or 'error' and related message.

    """
    from gabber.utils import logging
    req = request.get_json()
    # TODO: validation.
    logging.log_audio_interview_events(req.get('type', None), req.get('content', None), req.get('path', None))
    return jsonify({'success': True}), 200
