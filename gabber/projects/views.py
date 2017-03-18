from gabber.projects.models import Interview,  Project, ProjectPrompt
from flask import Blueprint, render_template, url_for, redirect, request, flash
from flask_login import current_user, login_required
from gabber import app, db
import json
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
            .filter(Interview.prompt_id.in_(prompt_ids)).all()

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
                'prompt': prompt.text_prompt})

        return render_template('views/projects/display.html',
                               project_title=project,
                               interviews=interviews_to_display)


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
