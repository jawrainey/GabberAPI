from gabber.projects.models import Project
from flask import Blueprint, render_template
from flask_login import current_user

main = Blueprint('main', __name__)


@main.route('/', methods=['GET'])
def index():
    return render_template('views/main/index.html')


@main.route('regions/', methods=['GET'])
def regions():
    return render_template('views/playlist/index.html')


@main.route('tos/', methods=['GET'])
def tos():
    return render_template('views/main/tos.html')


@main.route('privacy/', methods=['GET'])
def privacy():
    return render_template('views/main/privacy.html')


@main.route('about/', methods=['GET'])
def about():
    return render_template('views/main/about.html')


@main.route('projects/', methods=['GET'])
def projects():
    public_projects = Project.query.filter_by(type=1).all()
    user_projects = []
    if current_user.is_authenticated:
        # Projects the user is a member of (whether private & public)
        user_projects = current_user.projects()
        # Do not show the same projects in the public section if you are a member of that project
        public_projects = list(set(public_projects) - set(user_projects))
    return render_template('views/main/projects.html', user_projects=user_projects, public_projects=public_projects)