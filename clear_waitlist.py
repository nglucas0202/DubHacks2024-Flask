# clear_location_names.py

from app import app, db, Location

with app.app_context():
    loc = Location.query.filter_by(location_name="Park1").first()

    if loc:
        loc.names = []
        db.session.commit()
        print(f"Cleared names for location '{loc.location_name}'")
    else:
        print("Location not found.")