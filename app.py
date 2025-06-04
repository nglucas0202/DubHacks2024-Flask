from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.mutable import MutableList
from flask_cors import CORS
from flask_socketio import SocketIO

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
socketio = SocketIO(app, cors_allowed_origins="*")  # allow frontend to connect
db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Define the Location model to store user names by location
class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100), nullable=False)
    #names = db.Column(db.JSON, nullable=False)  # Store names as a JSON array
    names = db.Column(MutableList.as_mutable(db.JSON), nullable=False)  # ← KEY LINE

@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "User already exists!"}), 400

    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully!"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user:
        print(user)
        print(user.password)

    if user and user.password == password:
        return jsonify({"message": "Login successful!"}), 200
    else:
        return jsonify({"message": "Invalid credentials!"}), 401

@app.route('/save_names', methods=['POST'])
def save_names():
    data = request.get_json()
    location_name = data.get('location')
    names = data.get('names')

    # Find or create location
    location = Location.query.filter_by(location_name=location_name).first()
    if not location:
        location = Location(location_name=location_name, names=names)
        db.session.add(location)
    else:
        location.names = names  # Update existing names
    db.session.commit()

    # Emit the update to all connected clients
    socketio.emit('update_wait_list', {'location': location_name, 'names': names})    

    return jsonify({"message": "Names saved successfully!"}), 200

@app.route('/waitlist_signup', methods=['POST'])
def waitlist_signup():
    data = request.get_json()
    location_name = data.get('location')
    print("Location: " + location_name)
    name = data.get('name')

    # Find or create location
    location = Location.query.filter_by(location_name=location_name).first()
    if not location:
        location = Location(location_name=location_name, names=[name])
        db.session.add(location)
    else:
        print("Here1: " + name)
        #location.names = []
        #location.names = [name]  # Update existing names
        location.names.append(name)
    db.session.commit()

    loc2 = Location.query.filter_by(location_name=location_name).first()
    print(loc2.names)

    # Emit the update to all connected clients
    socketio.emit('update_wait_list', {'location': location_name, 'names': location.names})    

    return jsonify({"message": "Names saved successfully!"}), 200    

@app.route('/waitlist_leave', methods=['POST'])
def waitlist_leave():
    data = request.get_json()
    location_name = data.get('location')
    print("Location: " + location_name)
    name = data.get('name')

    # Find location
    location = Location.query.filter_by(location_name=location_name).first()
    if location and name in location.names:
        location.names.remove(name)
        db.session.commit()

    # Emit the update to all connected clients
    socketio.emit('update_wait_list', {'location': location_name, 'names': location.names})    

    return jsonify({"message": "Names saved successfully!"}), 200  

@app.route('/get_names/<location>', methods=['GET'])
def get_names(location):
    print("Here 2")
    location_data = Location.query.filter_by(location_name=location).first()
    if location_data:
        print("Here3")
        print(location_data.names)
        return jsonify(location_data.names), 200
    print("Here4")
    return jsonify([]), 200  # Return empty list if no names found

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    user_list = [{"id": user.id, "username": user.username} for user in users]
    return jsonify(user_list), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)

