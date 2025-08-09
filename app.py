from flask import Flask, request, jsonify, render_template
import calculation.distance as di
from flask_cors import CORS
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime
import uuid
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

# Initialize Firestore
credentials = service_account.Credentials.from_service_account_file('proxi-meter-83499c587f3e.json')
db = firestore.Client(credentials=credentials, project='proxi-meter')

# -------------------------------
# Authentication Endpoints
# -------------------------------

@app.route("/signup", methods=["POST"])

def signup():
    data = request.json
    base_name = data.get("displayName", "Anonymous")
    user_id = str(uuid.uuid4())
    
    # Create unique display name
    display_name = f"{base_name}#{user_id[:4]}"
    
    # Create user document
    user_ref = db.collection("USERS").document(user_id)
    user_ref.set({
        'id': user_id,  # Add ID field
        'displayName': display_name,
        'displayName_lower': display_name.lower(),  # For case-insensitive search
        'createdAt': datetime.now(),
        'lastActive': datetime.now()
    }, merge=True)
    
    return jsonify({
        "user_id": user_id,
        "displayName": display_name,
        "status": "created"
    }), 201
# -------------------------------
# Friend Management
# -------------------------------

@app.route("/add-friend", methods=["POST"])
def add_friend():
    data = request.json
    user_id = data.get("user_id")
    friend_id = data.get("friend_id")
    
    if not user_id or not friend_id:
        return jsonify({"error": "Missing user_id or friend_id"}), 400
    
    # Add to friend list
    friend_ref = db.collection("USERS").document(user_id).collection('friends').document(friend_id)
    friend_ref.set({
        'friend_id': friend_id,
        'addedAt': datetime.now()
    })
    
    return jsonify({"status": "friend_added"})

@app.route("/get-friends", methods=["GET"])
def get_friends():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    
    friends = []
    try:
        friends_ref = db.collection("USERS").document(user_id).collection('friends').stream()
        for friend in friends_ref:
            friend_id = friend.id
            friend_doc = db.collection("USERS").document(friend_id).get()
            
            if friend_doc.exists:
                friends.append({
                    "id": friend_id,
                    "display_name": friend_doc.get('displayName', friend_id)
                })
            else:  # Handle missing friend documents
                friends.append({
                    "id": friend_id,
                    "display_name": "Unknown User"
                })
    except Exception as e:
        app.logger.error(f"Error getting friends: {str(e)}")
    
    return jsonify(friends)
@app.route("/search-users", methods=["GET"])
def search_users():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])
    
    results = []
    try:
        users_ref = db.collection("USERS")
        
        # Search by document ID (user ID)
        docs = users_ref.where(firestore.FieldPath.document_id(), ">=", query
                          ).where(firestore.FieldPath.document_id(), "<=", query + '\uf8ff'
                          ).stream()
        
        for doc in docs:
            user = doc.to_dict()
            results.append({
                "id": doc.id,
                "display_name": user.get('displayName', '')
            })
        
        # Search by display name (case-insensitive)
        query_lower = query.lower()
        docs = users_ref.where("displayName_lower", ">=", query_lower
                          ).where("displayName_lower", "<=", query_lower + '\uf8ff'
                          ).stream()
        
        for doc in docs:
            if not any(r['id'] == doc.id for r in results):
                user = doc.to_dict()
                results.append({
                    "id": doc.id,
                    "display_name": user.get('displayName', '')
                })
    except Exception as e:
        app.logger.error(f"User search error: {str(e)}")
    
    return jsonify(results[:10])

# -------------------------------
# Location Handling
# -------------------------------

@app.route("/update-location", methods=["POST"])
def update_location():
    try:
        data = request.json
        user_id = data.get("user_id")
        lat = data.get("lat")
        lon = data.get("lon")
        
        if not all([user_id, lat, lon]):
            return jsonify({"error": "Missing parameters"}), 400
        
        # Store location with timestamp
        timestamp = datetime.now()
        # Use Firestore-safe document ID format
        doc_id = timestamp.strftime("%Y%m%d%H%M%S%f")
        location_ref = db.collection("USERS").document(user_id).collection('locations').document(doc_id)
        location_ref.set({
            'lat': float(lat),
            'lon': float(lon),
            'timestamp': timestamp
        })
        
        # Update last active time
        user_ref = db.collection("USERS").document(user_id)
        user_ref.set({'lastActive': timestamp}, merge=True)
        
        return jsonify({"status": "ok"})
    except Exception as e:
        app.logger.error(f"Location update error: {str(e)}")
        return jsonify({"error": "Failed to update location", "details": str(e)}), 500
def get_latest_location(user_id):
    """Get the most recent location for a user"""
    locs_ref = db.collection("USERS").document(user_id).collection('locations')
    locations = locs_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).stream()
    
    for loc in locations:
        return loc.to_dict()
    return None

# -------------------------------
# Proximity Calculation
# -------------------------------

@app.route("/proximity", methods=["GET"])
def proximity():
    user_id = request.args.get("user_id")
    unit = request.args.get("unit", "").strip().lower()
    
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    
    # Get user's latest location
    user_loc = get_latest_location(user_id)
    if not user_loc:
        return jsonify({"error": "User location not found"}), 404
    
    # Get user's friends
    friends = []
    friends_ref = db.collection("USERS").document(user_id).collection('friends').stream()
    for friend in friends_ref:
        friends.append(friend.id)
    
    # Get friends' latest locations
    friend_locations = {}
    for friend_id in friends:
        if loc := get_latest_location(friend_id):
            friend_locations[friend_id] = loc
    
    # Handle units
    if not unit:
        unit = di.get_random_unit()
    if unit not in di.UNITS:
        return jsonify({
            "error": f"Unit '{unit}' not found",
            "available_units": list(di.UNITS.keys())
        }), 400
    
    # Calculate distances
    result = []
    for friend_id, loc in friend_locations.items():
        dist_m = di.haversine(
            user_loc['lat'], user_loc['lon'],
            loc['lat'], loc['lon']
        )
        dist_in_units = di.meters_to_units(dist_m, unit)
        
        # Get friend's display name
        friend_doc = db.collection("USERS").document(friend_id).get()
        display_name = friend_doc.get('displayName') if friend_doc.exists else friend_id
        
        result.append({
            "friend_id": friend_id,
            "display_name": display_name,
            "distance": dist_in_units,
            "unit": unit
        })
    
    return jsonify(result)

# -------------------------------
# Additional Endpoints
# -------------------------------

@app.route("/user-profile/<user_id>", methods=["GET"])
def get_profile(user_id):
    user_ref = db.collection("USERS").document(user_id)
    user = user_ref.get()
    
    if not user.exists:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify(user.to_dict())

if __name__ == '__main__':
    app.run(debug=True)