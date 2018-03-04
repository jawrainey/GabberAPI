from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_migrate import Migrate
from flask_restful import Api
from flask_jwt_extended import JWTManager
import datetime
import os

# Share static path behind proxy across all blueprints
templates = os.path.join(os.pardir, 'frontend/templates')
static_path = os.path.join(os.pardir, 'frontend/static')
app = Flask(__name__, template_folder=templates, static_folder=static_path)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', '')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET', '')
app.config['SECRET_KEY'] = os.environ.get('SECRET', '')
app.config['SALT'] = os.environ.get('SALT', '')
app.config['ERROR_404_HELP'] = False
# This is a temporary as there is limited time to implement refresh tokens, etc
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(minutes=60*24*499)

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
jwt = JWTManager(app)
restful_api = Api(app)
db = SQLAlchemy(app)
ma = Marshmallow(app)
mail = Mail(app)
migrate = Migrate(app, db)

from gabber.api.projects import Projects
from gabber.api.project import Project
from gabber.api.membership import ProjectMembership
from gabber.api.sessions import ProjectSessions
from gabber.api.session import ProjectSession

restful_api.add_resource(Projects, '/api/projects/')
restful_api.add_resource(Project, '/api/projects/<int:pid>/')
restful_api.add_resource(ProjectMembership, '/api/projects/<int:pid>/membership/')
restful_api.add_resource(ProjectSessions, '/api/projects/<int:pid>/sessions/')
restful_api.add_resource(ProjectSession, '/api/projects/<int:pid>/sessions/<string:sid>/')

from gabber.api.auth import TokenRefresh, UserRegistration, UserLogin
restful_api.add_resource(TokenRefresh, '/api/auth/token/refresh/')
restful_api.add_resource(UserRegistration, '/api/auth/register/')
restful_api.add_resource(UserLogin, '/api/auth/login/')

# The existing API is confusing because methods are separate ...
from gabber.api.playlists import UserPlaylists, RegionsListForPlaylist, RegionsListByProject, RegionNote

restful_api.add_resource(
    RegionsListByProject,
    '/api/project/<int:project_id>/regions/',
    '/api/projects/<int:pid>/sessions/<string:sid>/annotation/'
)

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

from gabber.main.views import main
app.register_blueprint(main, url_prefix='/')
from gabber.api.views import api
app.register_blueprint(api, url_prefix='/api/')
from gabber.users.views import users
app.register_blueprint(users, url_prefix='/')
from gabber.projects.views import project
app.register_blueprint(project, url_prefix='/project/')
from gabber.consent.views import consent
app.register_blueprint(consent, url_prefix='/')

from gabber.utils import logging

# Model meta-data required to create db correctly
db.create_all()

from gabber.users.models import Anonymous
login_manager.anonymous_user = Anonymous


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
