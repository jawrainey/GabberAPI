from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask.ext.login import current_user, login_user, login_required, logout_user
from gabber.users.forms import LoginForm
from gabber.users.models import User
from gabber.projects.models import Project
from gabber import app, db, login_manager
import os

users = Blueprint('users', __name__)


@login_manager.user_loader
def load_user(email):
    return User.query.get(email)


@users.route('login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if current_user.is_authenticated:
        return redirect(url_for('users.dashboard'))

    if form.validate_on_submit():
        login_user(User.query.filter_by(username=form.email.data).first())
        return redirect(url_for('users.dashboard'))
    return render_template('views/login.html', form=form)


@users.route('logout/', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@users.route('dashboard/', methods=['GET', 'POST'])
@login_required
def dashboard():
    projects = Project.query.filter_by(creator=current_user.username).all()
    return render_template('views/users/dashboard.html', projects=projects)


@users.route('dashboard/edit/<project>/', methods=['GET', 'POST'])
@login_required
def edit_project(project=None):
    project = Project.query.filter_by(title=project).first()

    # TODO: use WTForms to process and validate form. Tricky with dynamic form.
    if request.method == 'POST':
        # Allows title removal to create a 'prompt only' dictionary for parsing
        _form = request.form.copy()
        project.title = _form.get('title', None)
        _form.pop('title')

        prompts = project.prompts.all()

        for fieldname, prompt_text in _form.iteritems():
            __update_prompt(prompts, fieldname.split("-")[-1], text=prompt_text)

        for fieldname, uploaded_file in request.files.iteritems():
            if uploaded_file.filename:
                folder = os.path.join(app.config['IMG_FOLDER'] + str(project.id))
                if not os.path.exists(folder):
                    os.makedirs(folder)
                fname = fieldname.split("-")[-1] + '.jpg'
                uploaded_file.save(os.path.join(folder, fname))
                __update_prompt(prompts, fname.split('.')[0], image=fname)

        db.session.commit()
        flash('The prompts for your project have been updated if any changes were made.')
        return redirect(url_for('users.dashboard'))
    return render_template('views/users/edit.html', project=project)


def __update_prompt(prompts, prompt_id, text=None, image=None):
    for prompt in prompts:
        if int(prompt_id) == prompt.id:
            if text:
                prompt.text_prompt = text
            if image:
                prompt.image_path = image
