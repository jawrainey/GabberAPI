from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
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

db = SQLAlchemy(app)

from gabber import models, api

# Create the database afterwards as models meta-data required to populate it.
if not os.path.exists(dbp):
    db.create_all()
