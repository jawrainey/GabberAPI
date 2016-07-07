from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.debug = True
# This is where all the audio experiences will be stored -- root directory.
xp = os.path.abspath(os.path.join("experiences"))
if not os.path.exists(xp):
    os.makedirs(xp)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + 'dati.db'
app.config['SECRET_KEY'] = 'supersecretpasswordfromtheotherside'
app.config['UPLOAD_FOLDER'] = xp

db = SQLAlchemy(app)

from gabber import views, models, api
