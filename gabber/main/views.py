from gabber.projects.models import Project, ProjectPrompt, Interview
from flask import Blueprint, redirect, render_template, flash, url_for
from flask_login import current_user

main = Blueprint('main', __name__)


@main.route('/', methods=['GET'])
def index():
    return render_template('views/main/index.html')


@main.route('about/', methods=['GET'])
def about():
    return render_template('views/main/about.html')


@main.route('projects/', methods=['GET'])
def projects():
    public_projects = Project.query.filter_by(type=1).all()
    user_projects = []
    if current_user.is_authenticated and (current_user.get_role() == 'admin' or current_user.get_role() == 'staff'):
        # Projects the user is a member of (whether private & public)
        user_projects = current_user.projects
        # Do not show the same projects in the public section if you are a member of that project
        public_projects = list(set(public_projects) - set(user_projects))
    return render_template('views/main/projects.html', user_projects=user_projects, public_projects=public_projects)


@main.route('idm/', methods=['GET'])
def idm():
    from sqlalchemy.sql import and_
    import datetime
    prompt_ids = [i.id for i in
                  Project.query.filter_by(id=1).first().prompts.all()]

    interviews = Interview.query.filter(
        and_(Interview.prompt_id.in_(prompt_ids),
             Interview.created_on >= datetime.datetime(2017, 2, 15, 15, 00, 00))
    ).order_by(Interview.created_on.desc()).all()

    filtered_interviews = []

    for i in interviews:
        for j in i.participants.all():
            if 'ncl' in j.email or 'newcastle' in j.email:
                filtered_interviews.append(i)
                break

    prompts = ProjectPrompt.query.filter(ProjectPrompt.id.in_(prompt_ids)).all()
    prompts = dict((p.id, p.text_prompt) for p in prompts)
    return render_template('views/main/idm.html',
                           interviews=filtered_interviews,
                           prompts=prompts)
