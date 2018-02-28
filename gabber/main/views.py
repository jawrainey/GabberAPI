from gabber.projects.models import Project
from flask import Blueprint, render_template
from flask_login import current_user

main = Blueprint('main', __name__)


@main.route('/', methods=['GET'])
def index():
    return render_template('views/main/index.html')


@main.route('regions/#/<int:pid>', methods=['GET'])
@main.route('regions/#/me/playlist/<int:pid>', methods=['GET'])
@main.route('regions/', methods=['GET'])
def regions(pid=None):
    return render_template('views/playlist/index.html')


@main.route('privacy/', methods=['GET'])
def privacy():
    return render_template('views/main/privacy.html')


@main.route('terms/', methods=['GET'])
def terms():
    return render_template('views/main/terms.html')


@main.route('about/', methods=['GET'])
def about():
    return render_template('views/main/about.html')


@main.route('projects/', methods=['GET'])
def projects():
    public_projects = Project.query.filter_by(isProjectPublic=1).all()
    user_projects = []
    if current_user.is_authenticated:
        # Projects the user is a member of (whether private & public)
        user_projects = current_user.projects()
    return render_template('views/main/projects.html',
                           user_projects=user_projects['personal'],
                           public_projects=user_projects['public'])
