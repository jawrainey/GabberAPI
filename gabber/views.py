from gabber import db
from gabber.projects.models import Interview,  Project, ProjectPrompt
from flask import Blueprint, redirect, render_template, url_for
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
                                if 'none' not in
                                [cons.type.lower() for cons in interview.consents.all()]]

        # Display limited interview information to the viewer.
        interviews_to_display = []
        for interview in consented_interviews:
            # TODO: how to determine the prompt for this interview?
            prompt = ProjectPrompt.query.filter_by(id=interview.prompt_id).first()
            # The interviews that have been consented to be made public.
            interviews_to_display.append({
                'file': url_for('consent.protected', filename=interview.audio),
                'thumb': prompt.image_path,
                'trackAlbum': 'default.png',
                'trackName': prompt.text_prompt})

        return render_template('views/project.html',
                               project_title=project.replace("-", " "),
                               interviews=json.dumps(interviews_to_display))
