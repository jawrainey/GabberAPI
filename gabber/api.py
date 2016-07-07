from gabber import app, db
from gabber.models import User
from flask import jsonify, request


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
