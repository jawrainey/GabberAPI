from gabber.projects.models import Interview, Membership, Project, ProjectPrompt, Roles
from gabber.users.models import User
from flask import Blueprint, current_app, render_template, url_for, redirect, request, flash, abort
from flask_login import current_user, login_required
from functools import wraps
from gabber import app, db
import os

project = Blueprint('project', __name__)


def membership_required(func):
    """
    This ensures that the current user can only view public projects or projects they are a member in.
    Currently, kwargs are used (interview id and project slug) from the wrapped function to determine this.
    Arguably this is not perfect as decorators should not depend upon what they are wrapped.

    :param func: The view function to decorate.
    :type func: function
    :returns The view function to decorate with project membership.
    """
    @wraps(func)
    def verified_membership(*args, **kwargs):
        iid = kwargs.get('interview_id', None)
        slug = kwargs.get('slug', None)
        _project = None

        if iid and iid in [i[0] for i in db.session.query(Interview.id).all()]:
            _project = Interview.query.get(iid).project()
        elif slug and slug in [str(i[0]) for i in db.session.query(Project.slug).all()]:
            _project = Project.query.filter_by(slug=slug).first()
        else:
            abort(404)

        _is_member = current_user.is_authenticated and current_user.member_of.filter_by(project_id=_project.id).first()

        if _project and _project.type or _is_member:
            return func(*args, **kwargs)
        return current_app.login_manager.unauthorized()
    return verified_membership


@project.route('join/<path:slug>/', methods=['GET', 'POST'])
def join(slug=None):
    """
    Allow members to join public projects, and in the future,
    users to request access to private projects.

    :param slug: the human-readable URL for a project
    :return: a message to inform the user of the action that took place.
    """
    if not current_user.is_authenticated:
        flash("To join a project you must first register.")
        return redirect(url_for('users.signup'))

    project = Project.query.filter_by(slug=slug).first()
    cid = current_user.get_id()

    if project.type:
        user_role = Roles.query.filter_by(name='user').first().id
        membership = Membership(uid=current_user.id, pid=project.id, rid=user_role)
        project.members.append(membership)
        db.session.add(project)
        db.session.commit()
        message = "You are now part of the %s project!" % str(project.title)
    flash(message)
    return redirect(url_for('main.projects'))


@project.route('sessions/<path:slug>/', methods=['GET', 'POST'])
@membership_required
def sessions(slug=None):
    interviews = Interview.query.join(ProjectPrompt).join(Project).filter(Project.slug == slug).all()

    from collections import defaultdict

    groups = defaultdict(list)

    for interview in interviews:
        if interview.session_id:
            groups[interview.session_id].append(interview)

    sessions = [{'creator': User.query.filter_by(id=interviews[0].creator).first().fullname if User.query.filter_by(id=interviews[0].creator).first() else 'Unknown',
                 'creation_date': interviews[0].created_on,
                 'participants': interviews[0].participants.all(),
                 'participants_names': [i.name for i in interviews[0].participants.all() if i],
                 'interviews': interviews,
                 'first_interview_id': interviews[0].id}
                for sid, interviews in groups.items()]

    sessions.sort(key=lambda item: item['creation_date'], reverse=True)

    return render_template('views/projects/sessions.html', sessions=sessions,
                           project_name=Project.query.filter_by(slug=slug).first().title)


@project.route('session/interview/<int:interview_id>', methods=['GET', 'POST'])
@membership_required
def session(interview_id=None):
    if interview_id not in [i[0] for i in db.session.query(Interview.id).all()]:
        flash('The interview you tried to view does not exist.')
        return redirect(url_for('main.projects'))

    interview = Interview.query.filter_by(id=interview_id).first()
    connections = [i.serialize() for i in interview.connections.all()]
    user_create_a_connection = len([i for i in connections if i['creator_id'] == current_user.get_id()])

    return render_template('views/projects/session.html',
                           interview=interview,
                           interviews=Interview.query.filter_by(
                               session_id=Interview.query.filter_by(id=interview_id).first().session_id).all(),
                           participants=interview.participants.all(),
                           connections=connections,
                           user_create_a_connection=user_create_a_connection)


@project.route('create', methods=['GET'])
@login_required
def create():
    """
    Renders the create view and form to the user.
    """
    return render_template('views/projects/edit.html')


@project.route('create', methods=['POST'])
@login_required
def create_post():
    """
    Allow a user to CREATE a project

    Args:
        title (str): The name of the project
        description (str): A brief (tweet-length) description of the project.
        ispublic (bool): is the project for public viewing?
    """
    # We want to pop items from the dict and its an immutableDict by default
    _form = request.form.copy()

    nproject = Project(
        creator=current_user.id,
        title=_form.get('title', ''),
        description=_form.get('description', ''),
        visibility=1 if _form.get('ispublic') else 0)

    # This simplifies access to other form elements (only the prompts should remain)
    _form.pop('title')
    _form.pop('description')
    _form.pop('ispublic', None)

    # Associate the current user as a member of the project.
    admin_role = Roles.query.filter_by(name='admin').first().id
    membership = Membership(uid=current_user.id, pid=nproject.id, rid=admin_role)
    nproject.members.append(membership)

    # Add and flush now to gain access to the project id when creating prompts below
    db.session.add(nproject)
    db.session.flush()

    for textfield, field_value in _form.items():
        prompt = ProjectPrompt(creator=current_user.id, text_prompt=field_value, project_id=nproject.id)
        # Flushing again as we need to use the prompt-id to create the image.
        db.session.add(prompt)
        db.session.flush()
        # Associate related image with prompt
        for imagefield, uploaded_file in request.files.items():
            # Each prompt has a text and image with the same field ID
            if (textfield.split("-")[1] == imagefield.split("-")[1]) and uploaded_file:
                __upload_prompt_image(uploaded_file, nproject.id, prompt.id)
                prompt.image_path = str(prompt.id) + '.jpg'
                nproject.prompts.append(prompt)
    db.session.commit()
    flash('The project was created successfully!')
    return redirect(url_for('main.projects'))


@project.route('edit/<path:slug>/', methods=['GET', 'POST'])
@login_required
def edit(slug=None):
    project = Project.query.filter_by(slug=slug).first()

    if not project:
        flash('That project you tried to <edit> does not exist.')
        return redirect(url_for('main.projects'))

    if current_user.role_for_project(project.id) != 'admin':
        flash('You do not have authorization to edit this project')
        return redirect(url_for('main.projects'))

    # TODO: use WTForms to process and validate form. Tricky with dynamic form.
    if request.method == 'POST':
        # Simplify field removal to create a 'prompt only' dictionary for parsing
        _form = request.form.copy()

        project.title = _form.get('title', '')
        project.description = _form.get('description', '')
        project.type = 1 if _form.get('ispublic') else 0

        _form.pop('title')
        _form.pop('description')
        _form.pop('ispublic', None)

        for fieldname, prompt_text in _form.items():
            for file_id, uploaded_file in request.files.items():
                # Match the prompt-text to the associated prompt-image
                if fieldname.split("-")[1] == file_id.split("-")[1]:
                    # The promptID of the text field sent from the user
                    pid = int(fieldname.split("-")[-1])
                    # A new prompt is always created whether the user modifies or updates a prompt
                    new_prompt = ProjectPrompt(creator=current_user.id, text_prompt=prompt_text, project_id=project.id)
                    # When the user modifies an exist prompt we must soft-delete it
                    if pid in [p.id for p in project.prompts.all()]:
                        modified_prompt = ProjectPrompt.query.filter_by(id=pid).first()
                        # Soft delete the prompt as it has been modified
                        modified_prompt.is_active = 0
                        # An image may not have been updated, so we want to keep the older one.
                        new_prompt.image_path = modified_prompt.image_path
                    # Need to know the new prompt ID to associate with the uploaded image.
                    db.session.add(new_prompt)
                    db.session.flush()
                    # Only update the prompt image if the file has changed
                    if uploaded_file.filename:
                        # Upload and associated the new image (if there is one) with the new prompt.
                        new_prompt.image_path = str(new_prompt.id) + '.jpg'
                        __upload_prompt_image(uploaded_file, project.id, new_prompt.id)
                    # Associate this newly created prompt with this specific project
                    project.prompts.append(new_prompt)
        db.session.commit()
        flash('The prompts for your project have been updated if any changes were made.')
        return redirect(url_for('main.projects'))
    return render_template('views/projects/edit.html', project=project)


def __upload_prompt_image(filetosave, projectid, promptid):
    # Each project has a unique folder that must exist
    folder = os.path.join(app.config['IMG_FOLDER'] + str(projectid))
    if not os.path.exists(folder):
        os.makedirs(folder)
    filetosave.save(os.path.join(folder, str(promptid) + '.jpg'))
