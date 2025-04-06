
import http.client
import json

API_KEY = "9943fa8927msh9f5dd0b4afc6aa8p1166c3jsnd4ce488a3caf"
API_HOST = "exercisedb.p.rapidapi.com"

def fetch_exercises():
    """Fetch exercises from the ExerciseDB API"""
    conn = http.client.HTTPSConnection(API_HOST)
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': API_HOST
    }
    
    # Update to fetch all exercises endpoint
    conn.request("GET", "/exercises", headers=headers)
    res = conn.getresponse()
    data = res.read()
    
    try:
        return json.loads(data.decode("utf-8"))
    except:
        return []

def get_exercise_by_id(exercise_id):
    """Fetch a specific exercise by ID"""
    conn = http.client.HTTPSConnection(API_HOST)
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': API_HOST
    }
    
    conn.request("GET", f"/exercises/exercise/{exercise_id}", headers=headers)
    res = conn.getresponse()
    data = res.read()
    
    try:
        return json.loads(data.decode("utf-8"))
    except:
        return None
