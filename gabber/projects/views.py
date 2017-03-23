from gabber.projects.models import Response, Interview, Project, ProjectPrompt
from flask import Blueprint, render_template, url_for, redirect, request, flash, jsonify
from flask_login import current_user, login_required
from gabber import app, db
import os

project = Blueprint('project', __name__)


@project.route('<path:project>/', methods=['GET'])
def display(project=None):
    all_projects = db.session.query(Project).all()
    existing = [i.title.replace(" ", "-").lower() for i in all_projects]

    if project not in existing:
        return redirect(url_for('main.index'))
    else:
        # TODO: challenge -- can the below be encapsulated into one query?
        # Select all interviews that for this project (based on prompt_id) that
        # have been fully consented by all participants for the audio interview.
        selected_project = Project.query.filter_by(
            title=project.replace("-", " ").lower()).first()
        prompt_ids = [i.id for i in selected_project.prompts.all()]
        interviews = db.session.query(Interview) \
            .filter(Interview.prompt_id.in_(prompt_ids)).order_by(Interview.created_on.desc()).all()

        consented_interviews = [interview for interview in interviews
                                if 'none' not in
                                [cons.type.lower() for cons in interview.consents.all()]]

        # Display limited interview information to the viewer.
        interviews_to_display = []
        for interview in consented_interviews:
            # TODO: how to determine the prompt for this interview?
            prompt = ProjectPrompt.query.filter_by(id=interview.prompt_id).first()
            # The interviews that have been consented to be made public.
            interviews_to_display.append({
                'audio': url_for('consent.protected', filename=interview.audio),
                'prompt': prompt.text_prompt,
                'created': interview.created_on.strftime("%b %d %Y")
            })

        return render_template('views/projects/display.html',
                               project_title=project,
                               interviews=interviews_to_display)


@project.route('sessions/<path:project>/', methods=['GET', 'POST'])
def sessions(project=None):
    _title = project.replace("-", " ").lower()
    interviews = Interview.query.join(ProjectPrompt).join(Project).filter(Project.title == _title).all()

    from collections import defaultdict

    groups = defaultdict(list)

    for interview in interviews:
        groups[interview.session_id].append(interview)

    sessions = [{'creation_date': interviews[0].created_on.strftime("%b %d, %Y"),
                 'participants': interviews[0].participants.all(),
                 'interviews': interviews,
                 'id': sid}
                for sid, interviews in groups.items()]

    return render_template('views/projects/sessions.html', sessions=sessions, project_name=_title)


@project.route('interview/response/', methods=['POST'])
def interview_response():
    # TODO: currently storing annotation tags as a JSON string...
    response = Response(
        text=request.form.get('content', ""),
        start_interval=request.form.get('start', 0),
        end_interval=request.form.get('end', 0),
        type=request.form.get('type', ""),
        user_id=current_user.id,
        interview_id=request.form.get('iid', 0),
    )
    db.session.add(response)
    db.session.commit()
    return jsonify({'success': True}), 200


@project.route('session/<int:session_id>', methods=['GET', 'POST'])
@project.route('session/interview/<int:interview_id>', methods=['GET', 'POST'])
def session(session_id=None, interview_id=None):
    # TODO: for now we are assuming one interview to build front-end
    if interview_id not in [i[0] for i in db.session.query(Interview.id).all()]:
        flash('The interview you tried to view does not exist.')
        return redirect(url_for('main.projects'))

    interview = Interview.query.filter_by(id=interview_id).first()
    interview.audio = url_for('consent.protected', filename=interview.audio, _external=True)

    response_types = {0: [], 1: []}

    for response in [i.serialize() for i in interview.responses.all()]:
        response_types[response['type']].append(response)

    return render_template('views/projects/session.html',
                           interview=interview,
                           participants=interview.participants.all(),
                           comments=response_types[0],
                           annotations=response_types[1])


@project.route('edit/<path:project>/', methods=['GET', 'POST'])
@login_required
def edit(project=None):
    if current_user.get_role() != 'admin':
        flash('You do not have authorization to edit this project')
        return redirect(url_for('main.projects'))

    project = Project.query.filter_by(title=project.replace("-", " ").lower()).first()

    # TODO: use WTForms to process and validate form. Tricky with dynamic form.
    if request.method == 'POST':
        # Allows title removal to create a 'prompt only' dictionary for parsing
        _form = request.form.copy()
        project.title = _form.get('title', '').lower()
        _form.pop('title')

        prompts = project.prompts.all()

        for fieldname, prompt_text in _form.items():
            __update_prompt(prompts, fieldname.split("-")[-1], text=prompt_text)

        for fieldname, uploaded_file in request.files.items():
            if uploaded_file.filename:
                folder = os.path.join(app.config['IMG_FOLDER'] + str(project.id))
                if not os.path.exists(folder):
                    os.makedirs(folder)
                fname = fieldname.split("-")[-1] + '.jpg'
                uploaded_file.save(os.path.join(folder, fname))
                __update_prompt(prompts, fname.split('.')[0], image=fname)

        db.session.commit()
        flash('The prompts for your project have been updated if any changes were made.')
        return redirect(url_for('main.projects'))
    return render_template('views/projects/edit.html', project=project)


def __update_prompt(prompts, prompt_id, text=None, image=None):
    for prompt in prompts:
        if int(prompt_id) == prompt.id:
            if text:
                prompt.text_prompt = text
            if image:
                prompt.image_path = image
