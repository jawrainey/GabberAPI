from gabber import app, db, helper
from gabber.models import User, Experience
from flask import jsonify, request
import os


# requests.post('http://0.0.0.0:8080/api/register',
# data = {'email': 'jawrainey@gmail.com',
# 'password': 'apassword', 'fullname': 'Jay Rainey'})
@app.route('/api/register', methods=['POST'])
def register():
    username = request.form.get('email', None)
    password = request.form.get('password', None)
    fullname = request.form.get('fullname', None)

    if not username or not password or not fullname:
        return jsonify({'error': 'All fields are required.'}), 400

    if username in [user.username for user in db.session.query(User.username)]:
        return jsonify({'error': 'An account with that email exists.'}), 400

    db.session.add(User(username, password, fullname))
    db.session.commit()
    return jsonify({'success': 'We did it!'}), 200


# requests.post('http://0.0.0.0:8080/api/auth',
# data = {'username': 'jawrainey@gmail.com', 'password' : 'apassword'})
@app.route('/api/auth', methods=['POST'])
def login():
    username = request.form.get('username', None)
    password = request.form.get('password', None)

    if not username or not password:
        return jsonify({'error': 'All fields are required.'}), 400

    known_users = [user.username for user in db.session.query(User.username)]
    if username and username in known_users:
        user = User.query.filter_by(username=username).first()
        if user and user.is_correct_password(password):
            return jsonify({'success': 'We did it!'}), 200
        return jsonify({'error': 'Incorrect password provided.'}), 400
    return jsonify({'error': 'Username and password do not match.'}), 400


# requests.post("http://0.0.0.0:8080/api/upload",
# files={'experience': open('audio.mp3', 'rb'),
#        'authorImage': open('gnome.svg', 'rb')},
# data={'interviewerEmail':'jawrainey@gmail.com'})
@app.route('/api/upload', methods=['POST'])
def upload():
    # TODO: return better errors for specific missing data.
    if not request.files or not request.form:
        return jsonify({'error': 'Required data has not been sent.'}), 400

    # 1. Validate fields
    experience = request.files['experience']
    interviewerEmail = request.form.get('interviewerEmail', None)
    intervieweeEmail = request.form.get('intervieweeEmail', None)
    intervieweeName = request.form.get('intervieweeName', None)
    location = request.form.get('location', None)
    promptText = request.form.get('promptText', None)

    # 2. Save file to disk and capture path. Required.
    expPath = os.path.join(app.config['UPLOAD_FOLDER'], experience.filename)
    experience.save(expPath)

    # 3. Save image to disk and capture path
    # Image of interviewee is optional. If not provided, use default silhouette.
    authorPath = None
    if 'authorImage' in request.files:
        authorImage = request.files['authorImage']
        authorPath = os.path.join(app.config['UPLOAD_FOLDER'],
                                  authorImage.filename)
        authorImage.save(authorPath)

    # 4. Save all data to database.
    experienceDB = Experience(experience=experience.filename,
                              authorImage=authorImage.filename,
                              interviewerEmail=interviewerEmail,
                              intervieweeEmail=intervieweeEmail,
                              intervieweeName=intervieweeName,
                              location=location,
                              promptText=promptText)
    db.session.add(experienceDB)
    db.session.commit()
    # Now we have saved it, ask the interviewee for permission to share it.
    helper.email_consent(experienceDB)
    return jsonify({'success': 'We did it!'}), 200
