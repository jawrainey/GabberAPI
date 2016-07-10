from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_mail import Mail
import os

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.debug = True
# This is where all the audio experiences will be stored -- root directory.
xp = os.path.abspath(os.path.join(os.pardir, "experiences"))
if not os.path.exists(xp):
    os.makedirs(xp)

dbp = os.path.join(xp, 'dati.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + dbp
app.config['SECRET_KEY'] = 'supersecretpasswordfromtheotherside'
app.config['UPLOAD_FOLDER'] = xp
app.config['SALT'] = 'supersecretsaltfromtheotherside'

# Gmail for simplicity of initial deployment.
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

db = SQLAlchemy(app)
mail = Mail(app)

from gabber import models, api, views

# Create the database afterwards as models meta-data required to populate it.
if not os.path.exists(dbp):
    db.create_all()
