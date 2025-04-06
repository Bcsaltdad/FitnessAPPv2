import sqlite3
from typing import Dict, List, Optional, Union
import logging

class WorkoutPlanner:
    def __init__(self, db_connection=None, db_path='fitness.db'):
        """
        Initialize the WorkoutPlanner with a database connection.
        
        Args:
            db_connection: Optional existing database connection
            db_path: Path to the database file if no connection is provided
        """
        try:
            if db_connection:
                self.db = db_connection
            else:
                self.db = sqlite3.connect(db_path)
            self.db.row_factory = sqlite3.Row
            self.cursor = self.db.cursor()
            
            # Ensure necessary tables exist
            self._initialize_database()
        except sqlite3.Error as e:
            logging.error(f"Database connection error: {e}")
            raise
    
    def _initialize_database(self):
        """Set up database tables if they don't exist."""
        try:
            # Check if exercises table exists
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='exercises'")
            if not self.cursor.fetchone():
                # Create exercises table
                self.cursor.execute('''
                CREATE TABLE exercises (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    body_part TEXT NOT NULL,
                    exercise_type TEXT NOT NULL,
                    equipment TEXT,
                    difficulty TEXT,
                    contraindications TEXT,
                    default_sets INTEGER,
                    default_reps TEXT
                )
                ''')
                
                # Create exercise_instructions table
                self.cursor.execute('''
                CREATE TABLE exercise_instructions (
                    id INTEGER PRIMARY KEY,
                    exercise_id INTEGER,
                    instruction TEXT NOT NULL,
                    FOREIGN KEY (exercise_id) REFERENCES exercises (id)
                )
                ''')
                
                self.db.commit()
        except sqlite3.Error as e:
            logging.error(f"Database initialization error: {e}")
            self.db.rollback()
            raise

    def create_workout_plan(self, days: int, focus: Dict[str, str], 
                           equipment: List[str], limitations: List[str], 
                           experience_level: str, goal: str) -> Dict[str, List[Dict]]:
        """
        Generates a workout plan based on user input.
        
        Args:
            days: Number of workout days
            focus: Dictionary mapping day numbers to body part focus
            equipment: List of available equipment
            limitations: List of physical limitations/injuries
            experience_level: User experience level (Beginner/Intermediate/Advanced)
            goal: Training goal (Body Building, Weight Loss, etc.)
            
        Returns:
            Dictionary mapping days to exercise lists
        """
        plan = {}
        for day in range(1, days + 1):
            day_key = f"Day {day}"
            day_focus = focus.get(day_key, "")  # Handle missing focus for a day
            if not day_focus:
                logging.warning(f"No focus specified for {day_key}, using general workout")
                day_focus = "Full Body"
                
            exercises = self._select_exercises_for_focus(
                day_focus, equipment, limitations, experience_level, goal
            )
            
            # Add set/rep recommendations based on goal and experience
            exercises = self._add_set_rep_recommendations(exercises, goal, experience_level)
            
            plan[day_key] = exercises
        return plan
    
    def _add_set_rep_recommendations(self, exercises: List[Dict], 
                                   goal: str, experience_level: str) -> List[Dict]:
        """Add appropriate set and rep recommendations based on goal and experience level."""
        for exercise in exercises:
            exercise_type = exercise.get('exercise_type', '')
            
            # Default recommendations
            sets = exercise.get('default_sets', 3)
            reps = exercise.get('default_reps', '8-12')
            
            # Adjust based on goal
            if "Body Building" in goal:
                if exercise_type == "Compound":
                    sets = max(3, sets)
                    reps = "8-12"
                elif exercise_type == "Isolation":
                    sets = max(3, sets)
                    reps = "10-15"
            elif "Strength" in goal:
                if exercise_type == "Compound":
                    sets = max(4, sets)
                    reps = "4-6"
                elif exercise_type == "Isolation":
                    sets = max(3, sets)
                    reps = "6-8"
            elif "Weight Loss" in goal:
                if exercise_type == "Cardio":
                    sets = 1
                    reps = "15-20 minutes"
                else:
                    sets = max(3, sets)
                    reps = "12-15"
                    
            # Adjust based on experience level
            if experience_level == "Beginner":
                sets = min(sets, 3)  # Cap sets for beginners
            elif experience_level == "Advanced":
                sets = max(sets, 4)  # Ensure advanced users get enough volume
                
            # Add to exercise dictionary
            exercise['recommended_sets'] = sets
            exercise['recommended_reps'] = reps
            
        return exercises

    def _select_exercises_for_focus(self, day_focus: str, equipment: List[str], 
                                  limitations: List[str], experience_level: str, 
                                  goal: str) -> List[Dict]:
        """
        Select appropriate exercises for a specific workout focus.
        
        Args:
            day_focus: Body part focus for the day (e.g., "Legs/Glutes")
            equipment: Available equipment
            limitations: User's physical limitations
            experience_level: User's experience level
            goal: Training goal
            
        Returns:
            List of exercise dictionaries
        """
        exercise_count = {
            "Beginner": {"Compound": 4, "Isolation": 4, "Cardio": 3, "Mobility": 2},
            "Intermediate": {"Compound": 5, "Isolation": 5, "Cardio": 3, "Mobility": 3},
            "Advanced": {"Compound": 6, "Isolation": 6, "Cardio": 4, "Mobility": 3}
        }.get(experience_level, {"Compound": 2, "Isolation": 2, "Cardio": 1, "Mobility": 1})
        
        # Adjust based on goal
        if "Body Building" in goal:
            exercise_count["Isolation"] += 1
        elif "Sports" in goal:
            exercise_count["Compound"] += 1
            exercise_count["Mobility"] += 2
            exercise_count["Compound"] += 1
            exercise_count["Isolation"] += 1
        elif "Weight Loss" in goal:
            exercise_count["Cardio"] += 1
        elif "Mobility" in goal:
            exercise_count["Mobility"] += 2
            exercise_count["Compound"] -= 1
            exercise_count["Isolation"] -= 1
        
        exercises = []
        focus_keywords = day_focus.lower().split('/')
        
        # Format equipment for SQL query
        equipment_str = "', '".join(equipment) if equipment else ""
        
        # Format limitations for SQL query to exclude contraindicated exercises
        limitations_conditions = []
        for limitation in limitations:
            limitations_conditions.append(f"e.contraindications NOT LIKE '%{limitation}%'")
        limitations_sql = " AND ".join(limitations_conditions) if limitations_conditions else "1=1"
        
        # Get exercises from database based on focus
        for exercise_type in ["Compound", "Isolation", "Cardio", "Mobility"]:
            count = exercise_count[exercise_type]
            if count <= 0:
                continue
            
            # Query exercises from database
            query = f'''
            SELECT e.*, GROUP_CONCAT(i.instruction) as instructions
            FROM exercises e
            LEFT JOIN exercise_instructions i ON e.id = i.exercise_id
            WHERE e.exercise_type = ?
            AND (
                e.body_part LIKE ? 
                OR e.body_part LIKE ?
                OR e.title LIKE ?
            )
            AND ({limitations_sql})
            '''
            
            # Add equipment filter if equipment is specified
            if equipment_str:
                query += f" AND (e.equipment IS NULL OR e.equipment IN ('{equipment_str}'))"
            
            query += '''
            GROUP BY e.id
            ORDER BY RANDOM()
            LIMIT ?
            '''
            
            # Use focus keywords to find relevant exercises
            params = [
                exercise_type,
                f"%{focus_keywords[0]}%",
                f"%{focus_keywords[-1] if len(focus_keywords) > 1 else focus_keywords[0]}%",
                f"%{focus_keywords[0]}%",
                count
            ]
            
            try:
                self.cursor.execute(query, params)
                rows = self.cursor.fetchall()
                
                for row in rows:
                    exercise = dict(row)
                    exercises.append(exercise)
                    
                # If we didn't get enough exercises, get some general ones for the exercise type
                if len(rows) < count:
                    remaining = count - len(rows)
                    self._add_general_exercises(exercises, exercise_type, remaining, equipment, limitations)
                    
            except sqlite3.Error as e:
                logging.error(f"Database query error: {e}")
                logging.error(f"Query: {query}")
                logging.error(f"Params: {params}")
        
        return exercises
    
    def _add_general_exercises(self, exercises: List[Dict], exercise_type: str, 
                             count: int, equipment: List[str], limitations: List[str]):
        """Add general exercises if specific ones for the focus area aren't enough."""
        if count <= 0:
            return
            
        # Format equipment for SQL query
        equipment_str = "', '".join(equipment) if equipment else ""
        
        # Format limitations for SQL query
        limitations_conditions = []
        for limitation in limitations:
            limitations_conditions.append(f"e.contraindications NOT LIKE '%{limitation}%'")
        limitations_sql = " AND ".join(limitations_conditions) if limitations_conditions else "1=1"
        
        # Get exercises not already in the list
        existing_ids = [e['id'] for e in exercises if 'id' in e]
        existing_ids_str = ', '.join(str(id) for id in existing_ids) if existing_ids else '0'
        
        query = f'''
        SELECT e.*, GROUP_CONCAT(i.instruction) as instructions
        FROM exercises e
        LEFT JOIN exercise_instructions i ON e.id = i.exercise_id
        WHERE e.exercise_type = ?
        AND e.id NOT IN ({existing_ids_str})
        AND ({limitations_sql})
        '''
        
        # Add equipment filter if equipment is specified
        if equipment_str:
            query += f" AND (e.equipment IS NULL OR e.equipment IN ('{equipment_str}'))"
        
        query += '''
        GROUP BY e.id
        ORDER BY RANDOM()
        LIMIT ?
        '''
        
        try:
            self.cursor.execute(query, [exercise_type, count])
            rows = self.cursor.fetchall()
            
            for row in rows:
                exercise = dict(row)
                exercises.append(exercise)
                
        except sqlite3.Error as e:
            logging.error(f"Database query error when adding general exercises: {e}")
    
    def add_exercise(self, title: str, body_part: str, exercise_type: str, 
                    equipment: str = None, difficulty: str = None, 
                    contraindications: str = None, default_sets: int = 3, 
                    default_reps: str = "8-12", instructions: List[str] = None):
        """
        Add a new exercise to the database.
        
        Args:
            title: Exercise name
            body_part: Target body part(s)
            exercise_type: Type of exercise (Compound, Isolation, Cardio, Mobility)
            equipment: Required equipment
            difficulty: Exercise difficulty level
            contraindications: Health conditions that should avoid this exercise
            default_sets: Default number of sets
            default_reps: Default rep range
            instructions: List of instruction steps
        
        Returns:
            ID of the newly created exercise
        """
        try:
            # Insert exercise
            self.cursor.execute('''
            INSERT INTO exercises (title, body_part, exercise_type, equipment, 
                                difficulty, contraindications, default_sets, default_reps)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, body_part, exercise_type, equipment, 
                difficulty, contraindications, default_sets, default_reps))
            
            exercise_id = self.cursor.lastrowid
            
            # Insert instructions if provided
            if instructions:
                for instruction in instructions:
                    self.cursor.execute('''
                    INSERT INTO exercise_instructions (exercise_id, instruction)
                    VALUES (?, ?)
                    ''', (exercise_id, instruction))
            
            self.db.commit()
            return exercise_id
            
        except sqlite3.Error as e:
            logging.error(f"Error adding exercise: {e}")
            self.db.rollback()
            return None
    
    def search_exercises(self, keyword: str, limit: int = 10) -> List[Dict]:
        """
        Search for exercises by keyword.
        
        Args:
            keyword: Search term
            limit: Maximum number of results
            
        Returns:
            List of matching exercise dictionaries
        """
        try:
            query = '''
            SELECT e.*, GROUP_CONCAT(i.instruction) as instructions
            FROM exercises e
            LEFT JOIN exercise_instructions i ON e.id = i.exercise_id
            WHERE e.title LIKE ? OR e.body_part LIKE ? OR e.exercise_type LIKE ?
            GROUP BY e.id
            LIMIT ?
            '''
            
            search_term = f"%{keyword}%"
            self.cursor.execute(query, (search_term, search_term, search_term, limit))
            
            return [dict(row) for row in self.cursor.fetchall()]
            
        except sqlite3.Error as e:
            logging.error(f"Error searching exercises: {e}")
            return []
            
    def close_connection(self):
        """Close the database connection."""
        if hasattr(self, 'db') and self.db:
            self.db.close()
            
    def __enter__(self):
        """Support for context manager protocol."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close connection when exiting context."""
        self.close_connection()


# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Use with context manager for automatic cleanup
    with WorkoutPlanner() as planner:
        # Add some sample exercises if database is empty
        planner.cursor.execute("SELECT COUNT(*) FROM exercises")
        count = planner.cursor.fetchone()[0]
        
        if count == 0:
            logging.info("Adding sample exercises to database...")
            planner.add_exercise(
                title="Back Squat",
                body_part="Legs/Glutes",
                exercise_type="Compound",
                equipment="Barbell",
                difficulty="Intermediate",
                contraindications="Knee Injury, Lower Back Injury",
                default_sets=4,
                default_reps="5-8",
                instructions=[
                    "Position the barbell on your upper back.",
                    "Feet shoulder-width apart, toes slightly turned out.",
                    "Brace core and squat down until thighs are parallel to floor.",
                    "Drive through heels to return to standing position."
                ]
            )
            # Add more sample exercises here...
        
        # Create a workout plan
        plan = planner.create_workout_plan(
            days=3,
            focus={"Day 1": "Legs/Glutes", "Day 2": "Chest/Shoulders", "Day 3": "Back/Arms"},
            equipment=["Barbell", "Dumbbells"],
            limitations=["Knee Injury"],
            experience_level="Intermediate",
            goal="Body Building"
        )
        
        # Print the plan
        for day, exercises in plan.items():
            print(f"\n{day} - {len(exercises)} exercises:")
            for i, exercise in enumerate(exercises, 1):
                print(f"  {i}. {exercise['title']} - {exercise['recommended_sets']} sets of {exercise['recommended_reps']}")
