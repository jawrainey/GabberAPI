from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_migrate import Migrate
from flask_restful import Api
from flask_jwt_extended import JWTManager
import os

# Required when deploying to dokku @OpenLab
PROXY_PATH = os.getenv('PROXY_PATH', '/')
# Share static path behind proxy across all blueprints

templates = os.path.join(os.pardir, 'frontend/templates')
static_path = os.path.join(os.pardir, 'frontend/static')
static_url_path = os.path.join(PROXY_PATH, 'static')
app = Flask(__name__, template_folder=templates, static_url_path=static_url_path, static_folder=static_path)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

root = os.path.dirname(os.path.abspath(__file__))
xp = os.path.join(root, 'protected')
if not os.path.exists(xp):
    os.makedirs(xp)

dbp = os.path.join(xp, 'dati.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + dbp
app.config['SECRET_KEY'] = 'supersecretpasswordfromtheotherside'
app.config['UPLOAD_FOLDER'] = xp
app.config['SALT'] = 'supersecretsaltfromtheotherside'
app.config['PROXY_PATH'] = PROXY_PATH

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
# Prevents suggestions for URLs by Flask being produced
app.config['ERROR_404_HELP'] = False

app.config['JWT_SECRET_KEY'] = 'super-super-secret'
jwt = JWTManager(app)

restful_api = Api(app)
db = SQLAlchemy(app)
mail = Mail(app)
migrate = Migrate(app, db)

# The existing API is confusing because methods are separate ...
from gabber.api.playlists import Projects, UserPlaylists, \
    RegionsListForPlaylist, RegionsListByProject, RegionNote

restful_api.add_resource(Projects,             '/api/project/<int:pid>')
restful_api.add_resource(RegionsListByProject, '/api/project/<int:project_id>/regions/')

restful_api.add_resource(
    UserPlaylists,
    '/api/users/<int:user_id>/playlists/<int:playlist_id>',
    '/api/users/<int:user_id>/playlists'  # POST [create a new playlist]
)

restful_api.add_resource(
    RegionsListForPlaylist,
    '/api/users/<int:uid>/playlists/<int:pid>/regions'
)

restful_api.add_resource(
    RegionNote,
    '/api/users/<int:uid>/playlists/<int:pid>/region/<int:rid>/note'
)

from gabber.api.interview import InterviewSessions

restful_api.add_resource(InterviewSessions,
                         '/api/interview/',
                         '/api/interview/<string:uid>/')

from gabber.api.projects import AllProjects
restful_api.add_resource(AllProjects, '/api/projects/')

from gabber.api.auth import UserRegistration, UserLogin
restful_api.add_resource(UserRegistration, '/api/register')
restful_api.add_resource(UserLogin, '/api/login')

from gabber.main.views import main
app.register_blueprint(main, url_prefix=PROXY_PATH)
from gabber.api.views import api
app.register_blueprint(api, url_prefix=os.path.join(PROXY_PATH, 'api/'))
from gabber.users.views import users
app.register_blueprint(users, url_prefix=PROXY_PATH)
from gabber.projects.views import project
app.register_blueprint(project, url_prefix=os.path.join(PROXY_PATH, 'project/'))
from gabber.consent.views import consent
app.register_blueprint(consent, url_prefix=PROXY_PATH)

# Model meta-data required to create db correctly
if not os.path.exists(dbp):
    db.create_all()

from gabber.users.models import Anonymous
login_manager.anonymous_user = Anonymous

from gabber.utils import logging

@app.errorhandler(Exception)
def exceptions(error):
    """
    We must log here as `after_request` may not be executed.
    """
    logging.log_request()
    return error


@app.after_request
def after_request(response):
    """
    Log every request that has been made to the server.
    """
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    logging.log_request()
    return response
