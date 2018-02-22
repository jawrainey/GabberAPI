from gabber.projects.models import InterviewSession, Membership, Project, ProjectPrompt, Roles, Codebook, Code
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

        if iid and iid in [i[0] for i in db.session.query(InterviewSession.id).all()]:
            _project = InterviewSession.query.get(iid).project()
        elif slug and slug in [str(i[0]) for i in db.session.query(Project.slug).all()]:
            _project = Project.query.filter_by(slug=slug).first()
        else:
            abort(404)

        _is_member = current_user.is_authenticated and current_user.member_of.filter_by(project_id=_project.id).first()

        if _project and _project.isProjectPublic or _is_member:
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

    _project = Project.query.filter_by(slug=slug).first()

    if _project.isProjectPublic:
        user_role = Roles.query.filter_by(name='user').first().id
        membership = Membership(uid=current_user.id, pid=_project.id, rid=user_role)
        _project.members.append(membership)
        db.session.add(_project)
        db.session.commit()
        message = "You are now part of the %s project!" % str(_project.title)
    flash(message)
    return redirect(url_for('main.projects'))


@project.route('sessions/<path:slug>/', methods=['GET', 'POST'])
@membership_required
def sessions(slug=None):
    pid = Project.query.filter_by(slug=slug).first().id
    interviews = InterviewSession.query.filter_by(project_id=pid).all()

    return render_template('views/projects/sessions.html', sessions=interviews,
                           project_name=Project.query.filter_by(slug=slug).first().title)


@project.route('session/interview/<string:interview_id>', methods=['GET', 'POST'])
@membership_required
def session(interview_id=None):
    if interview_id not in [i[0] for i in db.session.query(InterviewSession.id).all()]:
        flash('The interview you tried to view does not exist.')
        return redirect(url_for('main.projects'))

    interview = InterviewSession.query.get(interview_id)
    connections = [i.serialize() for i in interview.connections.all()]
    user_create_a_connection = len([i for i in connections if i['creator_id'] == current_user.get_id()])
    structural_annotation = [i.serialize() for i in interview.prompts.all()]

    return render_template('views/projects/session.html',
                           recording_url=interview.generate_signed_url_for_recording(),
                           interview=interview,
                           participants=interview.participants.all(),
                           conno=structural_annotation,    # These are the structural prompts
                           connections=connections,        # Whereas these are user annotations
                           user_create_a_connection=user_create_a_connection)


@project.route('create', methods=['GET'])
@login_required
def create():
    """
    Renders the create view and form to the user.
    """
    return render_template('views/projects/edit.html', codebook=[])


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

    # Add and flush now to gain access to the project id when creating prompts below
    db.session.add(nproject)
    db.session.flush()

    # Associate the current user as a member of the project.
    admin_role = Roles.query.filter_by(name='admin').first().id
    membership = Membership(uid=current_user.id, pid=nproject.id, rid=admin_role)
    nproject.members.append(membership)

    import json
    codebook = json.loads(_form.get('codebook', []))

    if codebook:
        db_codebook = Codebook(project_id=nproject.id)
        nproject.codebook.append(db_codebook)
        db.session.add(db_codebook)
        db.session.flush()

        for c in codebook:
            code = Code(text=c['tag'], codebook_id=db_codebook.id)
            db.session.add(code)
            db_codebook.codes.append(code)
            db.session.flush()

        _form.pop('codebook')

    for textfield, field_value in [i for i in _form.items() if i[0].split("-")[0] == 'promptText']:
        prompt = ProjectPrompt(creator=current_user.id, text_prompt=field_value, project_id=nproject.id)
        # Flushing again as we need to use the prompt-id to create the image.
        db.session.add(prompt)
        db.session.flush()
        # Associate related image with prompt
        for imagefield, uploaded_file in request.files.items():
            # Each prompt has a text and image with the same field ID
            if (textfield.split("-")[1] == imagefield.split("-")[1]) and uploaded_file:
                image_name = __upload_prompt_image(uploaded_file, nproject.id, prompt.id)
                prompt.image_path = image_name
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
        project.isProjectPublic = 1 if _form.get('ispublic') else 0
        from slugify import slugify
        project.slug = slugify(project.title)

        import json
        codebook = json.loads(_form.get('codebook', []))

        if codebook:
            pj_codebook = Codebook.query.filter_by(project_id=project.id).first()
            pj_codes = pj_codebook.codes.all()
            # Create newly added codes for the codebook
            for item in codebook:
                _id = item.get('id', None)
                if not _id:
                    code = Code(text=item.get('tag', None), codebook_id=pj_codebook.id)
                    db.session.add(code)
                    pj_codebook.codes.append(code)
                    db.session.commit()

            # Remove codes that were removes by the user:
            user_codes = set([c['id'] for c in codebook if c.get('id', None)])
            known_codes = set([c.id for c in pj_codes])
            removed_tags = known_codes - user_codes
            if removed_tags:
                for tag_id in removed_tags:
                    code = Code.query.filter_by(id=tag_id).first()
                    db.session.delete(code)
                    db.session.commit()

        _form.pop('title')
        _form.pop('description')
        _form.pop('ispublic', None)
        _form.pop('codebook')

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
                        image_name = __upload_prompt_image(uploaded_file, project.id, new_prompt.id)
                        # Upload and associated the new image (if there is one) with the new prompt.
                        new_prompt.image_path = image_name
                    else:
                        new_prompt.image_path = "default.jpg"
                    # Associate this newly created prompt with this specific project
                    project.prompts.append(new_prompt)
        db.session.commit()
        flash('The prompts for your project have been updated if any changes were made.')
        return redirect(url_for('main.projects'))

    _cb = Codebook.query.filter_by(project_id=project.id).first()

    if _cb:
        codebook = [{'id': c.id, 'tag': c.text} for c in Codebook.query.filter_by(project_id=project.id).first().codes.all()]
    else:
        codebook = []
    return render_template('views/projects/edit.html', project=project, codebook=codebook)


def __upload_prompt_image(filetosave, projectid, promptid):
    from uuid import uuid4
    from gabber.utils import amazon
    file_nom = str(uuid4().hex) + "-" + str(promptid) + ".jpg"
    s3_folder = str(projectid) + "/prompt-images/" + file_nom
    amazon.upload(filetosave, s3_folder)
    return file_nom
