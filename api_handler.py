
import http.client
import json

API_KEY = "9943fa8927msh9f5dd0b4afc6aa8p1166c3jsnd4ce488a3caf"
API_HOST = "exercisedb.p.rapidapi.com"

def fetch_exercises(limit=1000, offset=0):
    """Fetch exercises from the ExerciseDB API with pagination"""
    conn = http.client.HTTPSConnection(API_HOST)
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': API_HOST
    }
    
    endpoint = f"/exercises?limit={limit}&offset={offset}"
    conn.request("GET", endpoint, headers=headers)
    res = conn.getresponse()
    data = res.read()
    
    try:
        return json.loads(data.decode("utf-8"))
    except:
        return []

def get_all_exercises():
    """Fetch all available exercises"""
    all_exercises = []
    offset = 0
    limit = 50  # Fetch in batches
    
    while True:
        batch = fetch_exercises(limit=limit, offset=offset)
        if not batch:
            break
            
        all_exercises.extend(batch)
        if len(batch) < limit:  # Last batch
            break
            
        offset += limit
    
    return all_exercises

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
