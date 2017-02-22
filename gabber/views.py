from gabber.projects.models import Project, ProjectPrompt, Interview
from flask import Blueprint, redirect, render_template, flash, url_for

main = Blueprint('main', __name__)


@main.route('/', methods=['GET'])
def index():
    return render_template('views/main/index.html')


@main.route('about/', methods=['GET'])
def about():
    return render_template('views/main/about.html')


@main.route('projects/', methods=['GET'])
def projects():
    flash('No projects are currently public for you to listen to or curate.')
    return redirect(url_for('main.about'))


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

    print len(interviews)
    filtered_interviews = []

    for i in interviews:
        print i.participants.all()
        for j in i.participants.all():
            if 'ncl' in j.email or 'newcastle' in j.email:
                filtered_interviews.append(i)
                break

    prompts = ProjectPrompt.query.filter(ProjectPrompt.id.in_(prompt_ids)).all()
    prompts = dict((p.id, p.text_prompt) for p in prompts)
    return render_template('views/main/idm.html',
                           interviews=filtered_interviews,
                           prompts=prompts)
