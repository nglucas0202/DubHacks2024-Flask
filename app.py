from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
from sqlalchemy.ext.mutable import MutableList
from flask_cors import CORS
from flask_socketio import SocketIO

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
socketio = SocketIO(app, cors_allowed_origins="*")  # allow frontend to connect
db = SQLAlchemy(app)

load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

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
    names = db.Column(MutableList.as_mutable(db.JSON), nullable=False)  # ← KEY LINE


@app.route('/create_user', methods=['POST'])
def create_user():
    print("create_user called")
    data = request.get_json()
    username = data.get('username')
    print("create_user: username=" + username)
    password = data.get('password')
    print("create_user: password=" + password)

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "User already exists!"}), 400

    print("create_user: creating user...")
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


# only support three cities for now
@app.route('/get_cities', methods=['GET'])
def get_cities():
    return jsonify([ "Seattle", "Bellevue", "Renton" ])


@app.route('/get_courts/<city>', methods=['GET'])
def get_courts(city):
    # Geocode city to get lat/lng
    geocode_url = f'https://maps.googleapis.com/maps/api/geocode/json?address={city}&key={GOOGLE_MAPS_API_KEY}'
    geocode_resp = requests.get(geocode_url)
    geocode_data = geocode_resp.json()
    if not geocode_data['results']:
        return jsonify({'error': 'City not found'}), 404
    location = geocode_data['results'][0]['geometry']['location']
    lat, lng = location['lat'], location['lng']

    # Search for basketball courts nearby
    places_url = (
        'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
        f'?location={lat},{lng}&radius=10000&keyword=basketball%20court&key={GOOGLE_MAPS_API_KEY}'
    )
    places_resp = requests.get(places_url)
    courts = places_resp.json().get('results', [])
    
    # google Place API will return generic "Basketball Court" if name is not available
    # we will just check and ignore duplicate for now
    seen = set()
    unique_courts = []
    for c in courts:
        if city.lower() in c.get('vicinity', '').lower():
            name = c['name']
            address = c.get('vicinity', '')
            key = name.lower()
            if key not in seen:
                seen.add(key)
                unique_courts.append({
                    'name': name,
                    'address': address,
                    'lat': c['geometry']['location']['lat'],
                    'lng': c['geometry']['location']['lng']
                })    
    
    # Return relevant info
    return jsonify(unique_courts)


#for testing without calling google API
@app.route('/get_courts_test/<city>', methods=['GET'])
def get_courts_test(city):
    if city == "Seattle":
        return jsonify([
            {
                "address": "7201 East Green Lake Dr N, Seattle",
                "lat": 47.6799933,
                "lng": -122.3282347,
                "name": "Basketball Courts"
            },
            {
                "address": "333 Pontius Ave N, Seattle",
                "lat": 47.62164139999999,
                "lng": -122.3326096,
                "name": "Cascade Playground"
            },
            {
                "address": "1661 Nagle Pl, Seattle",
                "lat": 47.61620509999999,
                "lng": -122.3199016,
                "name": "Cal Anderson Basketball Court"
            },
            {
                "address": "N 35th St &, Carr Pl N, Seattle",
                "lat": 47.6489767,
                "lng": -122.3392515,
                "name": "Basketball Court"
            },
            {
                "address": "7201 East Green Lake Dr N, Seattle",
                "lat": 47.6802143,
                "lng": -122.3284022,
                "name": "Green Lake Park"
            },
            {
                "address": "923 NW 54th St, Seattle",
                "lat": 47.6674414,
                "lng": -122.369546,
                "name": "Gilman Playground"
            },
            {
                "address": "7201 East Green Lake Dr N, Seattle",
                "lat": 47.68026039999999,
                "lng": -122.3285033,
                "name": "Green Lake Community Center"
            },
            {
                "address": "750 S Homer St, Seattle",
                "lat": 47.5514318,
                "lng": -122.3213014,
                "name": "Georgetown Playfield"
            },
            {
                "address": "MM5J+P8M, 817 NE 43rd St, Seattle",
                "lat": 47.6593534,
                "lng": -122.3189345,
                "name": "Christie Park"
            },
            {
                "address": "1635 11th Ave, Seattle",
                "lat": 47.6170185,
                "lng": -122.319127,
                "name": "Cal Anderson Park"
            },
            {
                "address": "9320 38th Ave. S, Seattle",
                "lat": 47.5190115,
                "lng": -122.2842073,
                "name": "Benefit Playground"
            },
            {
                "address": "1710 Broadway, Seattle",
                "lat": 47.616543,
                "lng": -122.320649,
                "name": "Seattle Central Basketball Stadium"
            },
            {
                "address": "201 19th Ave, Seattle",
                "lat": 47.60374849999999,
                "lng": -122.3078965,
                "name": "Rotary Style Basketball"
            },
            {
                "address": "1400-1402 NE 50th St, Seattle",
                "lat": 47.66506099999999,
                "lng": -122.3134908,
                "name": "Park with Basketball Hoop"
            },
            {
                "address": "5827 16th Ave NE, Seattle",
                "lat": 47.67261999999999,
                "lng": -122.3115411,
                "name": "Ravenna Park Basketball Courts"
            }
        ])
    elif city == "Bellevue":
        return jsonify([
            {
                "address": "16000 NE 10th St, Bellevue",
                "lat": 47.6198443,
                "lng": -122.1279789,
                "name": "Crossroads Park Basketball Courts"
            },
            {
                "address": "2277 158th Ct NE, Bellevue",
                "lat": 47.6299034,
                "lng": -122.1296303,
                "name": "Bel-Tech Basketball Court"
            },
            {
                "address": "2532 127th Ave NE, Bellevue",
                "lat": 47.6332591,
                "lng": -122.1702949,
                "name": "Cherry Crest Mini Park"
            },
            {
                "address": "12309 SE 23rd Pl, Bellevue",
                "lat": 47.58992019999999,
                "lng": -122.1732594,
                "name": "Norwood Village Park Basketball Courts"
            },
            {
                "address": "1933 104th Ave SE, Bellevue",
                "lat": 47.5943434,
                "lng": -122.2029626,
                "name": "Basketball court"
            },
            {
                "address": "16153 SE 33rd Cir, Bellevue",
                "lat": 47.5807655,
                "lng": -122.126881,
                "name": "Spiritridge Park Basketball Court"
            }
        ])
    else:
        return jsonify([
            {
                "address": "272 Thomas Ave SW, Renton",
                "lat": 47.48049,
                "lng": -122.227584,
                "name": "City of Renton: Earlington Park"
            },
            {
                "address": "1101 Bronson Way N, Renton",
                "lat": 47.4827958,
                "lng": -122.200118,
                "name": "Liberty Park. Renton"
            },
            {
                "address": "601 S 23rd St, Renton",
                "lat": 47.4584171,
                "lng": -122.2082134,
                "name": "Thomas Teasdale Park"
            },
            {
                "address": "14372 WA-169, Renton",
                "lat": 47.4673649,
                "lng": -122.1468433,
                "name": "Basketball Court"
            },
            {
                "address": "815 Union Ave NE, Renton",
                "lat": 47.4968672,
                "lng": -122.1658434,
                "name": "Kiwanis Park"
            }           
        ])


# return the names on the waitlist for the specific location
@app.route('/get_names/<location>', methods=['GET'])
def get_names(location):
    location_data = Location.query.filter_by(location_name=location).first()
    if location_data:
        return jsonify(location_data.names), 200

    return jsonify([]), 200  # Return empty list if no names found


@app.route('/waitlist_signup', methods=['POST'])
def waitlist_signup():
    data = request.get_json()
    location_name = data.get('location')
    name = data.get('name')

    # Find or create location
    location = Location.query.filter_by(location_name=location_name).first()
    if not location:
        location = Location(location_name=location_name, names=[name])
        db.session.add(location)
    else:
        location.names.append(name)
    db.session.commit()

    loc2 = Location.query.filter_by(location_name=location_name).first()

    # Emit the update to all connected clients
    socketio.emit('update_wait_list', {'location': location_name, 'names': location.names})    

    return jsonify({"message": "Names saved successfully!"}), 200    


@app.route('/waitlist_leave', methods=['POST'])
def waitlist_leave():
    data = request.get_json()
    location_name = data.get('location')
    name = data.get('name')

    # Find location
    location = Location.query.filter_by(location_name=location_name).first()
    if location and name in location.names:
        location.names.remove(name)
        db.session.commit()

    # Emit the update to all connected clients
    socketio.emit('update_wait_list', {'location': location_name, 'names': location.names})    

    return jsonify({"message": "Names saved successfully!"}), 200  


@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    user_list = [{"id": user.id, "username": user.username} for user in users]
    return jsonify(user_list), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, host='0.0.0.0', port=5000)
    #app.run(host='0.0.0.0', port=5000, debug=True)

