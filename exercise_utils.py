import sqlite3
import json
from datetime import datetime

class ExerciseDatabase:
    def __init__(self, db_path):
        """Initialize the database connection"""
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._initialize_tables()
        
    def _initialize_tables(self):
        """Initialize all required database tables if they don't exist"""
        # Original tables
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS exercises 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             title TEXT,
                             description TEXT,
                             body_part TEXT,
                             exercise_type TEXT,
                             equipment TEXT,
                             level TEXT,
                             instructions TEXT)''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS fitness_plans 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             user_id INTEGER,
                             name TEXT,
                             goal TEXT,
                             duration_weeks INTEGER,
                             created_at TIMESTAMP,
                             is_active INTEGER DEFAULT 1,
                             FOREIGN KEY(user_id) REFERENCES users(id))''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS plan_workouts 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             plan_id INTEGER,
                             exercise_id INTEGER,
                             week INTEGER,
                             day INTEGER,
                             target_sets INTEGER,
                             target_reps INTEGER,
                             FOREIGN KEY(plan_id) REFERENCES fitness_plans(id),
                             FOREIGN KEY(exercise_id) REFERENCES exercises(id))''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS workout_logs 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             workout_id INTEGER,
                             completed_at TIMESTAMP,
                             sets_completed INTEGER,
                             reps_completed INTEGER,
                             weight_kg REAL,
                             FOREIGN KEY(workout_id) REFERENCES plan_workouts(id))''')
        
        # New tables for sports-specific workout planning
        
        # Sports profiles table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS sports_profiles 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             sport TEXT UNIQUE NOT NULL,
                             required_movements TEXT NOT NULL,
                             energy_systems TEXT NOT NULL,
                             primary_muscle_groups TEXT NOT NULL,
                             injury_risk_areas TEXT,
                             training_phase_focus TEXT)''')
        
        # User profiles with sports focus
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS user_profiles 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             user_id INTEGER UNIQUE NOT NULL,
                             name TEXT,
                             age INTEGER,
                             experience_level TEXT,
                             primary_sport TEXT,
                             secondary_sports TEXT,
                             goals TEXT,
                             training_frequency INTEGER,
                             session_duration INTEGER,
                             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                             FOREIGN KEY(user_id) REFERENCES users(id))''')
        
        # Progress tracking table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS progress_tracking 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             user_id INTEGER NOT NULL,
                             workout_date TIMESTAMP NOT NULL,
                             workout_id INTEGER,
                             exercises_completed TEXT NOT NULL,
                             performance_metrics TEXT NOT NULL,
                             notes TEXT,
                             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                             FOREIGN KEY(workout_id) REFERENCES plan_workouts(id),
                             FOREIGN KEY(user_id) REFERENCES users(id))''')
        
        # Enhanced exercise attributes - safely add columns that might not exist
        self._safe_add_column("exercises", "sports_focus", "TEXT")
        self._safe_add_column("exercises", "primary_movement_pattern", "TEXT")
        self._safe_add_column("exercises", "energy_system", "TEXT")
        self._safe_add_column("exercises", "primary_benefit", "TEXT")
        self._safe_add_column("exercises", "difficulty", "INTEGER")
        
        # Enhanced fitness plans
        self._safe_add_column("fitness_plans", "primary_sport", "TEXT")
        self._safe_add_column("fitness_plans", "training_phase", "TEXT")
        
        self.conn.commit()
    
    def _safe_add_column(self, table, column, column_type):
        """Safely add a column to a table if it doesn't exist"""
        try:
            # Check if column exists
            self.cursor.execute(f"PRAGMA table_info({table})")
            columns = [info[1] for info in self.cursor.fetchall()]
            
            # Add column if it doesn't exist
            if column not in columns:
                self.cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        except sqlite3.Error as e:
            print(f"Error adding column {column} to {table}: {e}")
    
    def get_exercises_by_goal(self, goal):
        """Get exercises filtered by goal"""
        self.cursor.execute('''SELECT * FROM exercises 
                             WHERE exercise_type LIKE ?''', (f'%{goal}%',))
        return self.cursor.fetchall()
    
    def get_active_plans(self, user_id):
        """Get all active fitness plans for a user"""
        self.cursor.execute('''SELECT * FROM fitness_plans 
                             WHERE user_id = ? AND is_active = 1''', (user_id,))
        return self.cursor.fetchall()
    
    def get_plan_summary(self, plan_id):
    """Get summary statistics for a fitness plan"""
        try:
            self.cursor.execute('''
                SELECT 
                    pw.week,
                    COUNT(DISTINCT pw.id) as total_exercises,
                    COUNT(DISTINCT CASE WHEN wl.id IS NOT NULL THEN wl.id END) as exercises_completed,
                    IFNULL(AVG(wl.weight_kg), 0) as avg_weight,
                    COUNT(DISTINCT pw.day) as days_worked
                FROM plan_workouts pw
                LEFT JOIN workout_logs wl ON pw.id = wl.workout_id
                WHERE pw.plan_id = ?
                GROUP BY pw.week
                ORDER BY pw.week
            ''', (plan_id,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error in get_plan_summary for plan_id {plan_id}: {e}")
            return []
    
    def get_plan_workouts(self, plan_id, week, day):
        """Get workouts for a specific plan, week, and day"""
        try:
            if day is not None:  # Explicit check for None
                self.cursor.execute('''
                    SELECT pw.*, e.*
                    FROM plan_workouts pw
                    JOIN exercises e ON pw.exercise_id = e.id
                    WHERE pw.plan_id = ? AND pw.week = ? AND pw.day = ?
                ''', (plan_id, week, day))
            else:
                self.cursor.execute('''
                    SELECT pw.*, e.*
                    FROM plan_workouts pw
                    JOIN exercises e ON pw.exercise_id = e.id
                    WHERE pw.plan_id = ? AND pw.week = ?
                ''', (plan_id, week))
            
            results = self.cursor.fetchall()
            # Return empty list if no workouts found
            return [dict(row) for row in results] if results else []
        except sqlite3.Error as e:
            print(f"Error fetching workouts for plan {plan_id}, week {week}, day {day}: {e}")
            # Return empty list on error
            return []
    
    def update_plan_goal(self, plan_id, new_goal):
        """Update the goal of a fitness plan"""
        self.cursor.execute('''UPDATE fitness_plans SET goal = ? WHERE id = ?''',
                         (new_goal, plan_id))
        self.conn.commit()
    
    def make_plan_inactive(self, plan_id):
        """Mark a fitness plan as inactive"""
        self.cursor.execute('''UPDATE fitness_plans SET is_active = 0 WHERE id = ?''',
                         (plan_id,))
        self.conn.commit()
    
    def log_workout(self, workout_id, sets, reps, weight_kg):
        """Log a completed workout"""
        self.cursor.execute(
            '''INSERT INTO workout_logs 
            (workout_id, completed_at, sets_completed, reps_completed, weight_kg)
            VALUES (?, ?, ?, ?, ?)''',
            (workout_id, datetime.now(), sets, reps, weight_kg))
        self.conn.commit()
    
    # New methods for sports-specific functionality
    
    def get_sports_list(self):
        """Get list of all available sports"""
        self.cursor.execute("SELECT sport FROM sports_profiles ORDER BY sport")
        return [row['sport'] for row in self.cursor.fetchall()]
    
    def get_sports_profile(self, sport):
        """Get a sport profile by name"""
        self.cursor.execute("SELECT * FROM sports_profiles WHERE sport = ?", (sport,))
        profile = self.cursor.fetchone()
        
        if profile:
            result = dict(profile)
            # Parse JSON fields
            result['required_movements'] = json.loads(result['required_movements'])
            result['energy_systems'] = json.loads(result['energy_systems'])
            result['primary_muscle_groups'] = json.loads(result['primary_muscle_groups'])
            result['injury_risk_areas'] = json.loads(result['injury_risk_areas'])
            result['training_phase_focus'] = json.loads(result['training_phase_focus'])
            return result
        return None
    
    def create_sports_profile(self, sport, required_movements, energy_systems, 
                             primary_muscle_groups, injury_risk_areas, training_phase_focus):
        """Create a new sports profile"""
        try:
            self.cursor.execute("""
            INSERT INTO sports_profiles 
            (sport, required_movements, energy_systems, primary_muscle_groups, 
            injury_risk_areas, training_phase_focus)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                sport,
                json.dumps(required_movements),
                json.dumps(energy_systems),
                json.dumps(primary_muscle_groups),
                json.dumps(injury_risk_areas),
                json.dumps(training_phase_focus)
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error creating sports profile: {e}")
            return None
    
    def get_user_profile(self, user_id):
        """Get a user's sports profile"""
        self.cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
        profile = self.cursor.fetchone()
        
        if profile:
            result = dict(profile)
            # Parse JSON fields
            result['secondary_sports'] = json.loads(result['secondary_sports'])
            result['goals'] = json.loads(result['goals'])
            return result
        return None
    
    def create_user_profile(self, user_id, name, age, experience_level, primary_sport,
                           secondary_sports, goals, training_frequency, session_duration):
        """Create a user profile with sports preferences"""
        try:
            self.cursor.execute("""
            INSERT INTO user_profiles 
            (user_id, name, age, experience_level, primary_sport, secondary_sports, goals, 
            training_frequency, session_duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, name, age, experience_level, primary_sport, 
                json.dumps(secondary_sports), json.dumps(goals),
                training_frequency, session_duration
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error creating user profile: {e}")
            # If duplicate, update instead
            try:
                self.cursor.execute("""
                UPDATE user_profiles SET
                name = ?, age = ?, experience_level = ?, primary_sport = ?,
                secondary_sports = ?, goals = ?, training_frequency = ?, session_duration = ?
                WHERE user_id = ?
                """, (
                    name, age, experience_level, primary_sport,
                    json.dumps(secondary_sports), json.dumps(goals),
                    training_frequency, session_duration, user_id
                ))
                self.conn.commit()
                return user_id
            except sqlite3.Error as e2:
                print(f"Error updating user profile: {e2}")
                return None
    
    def log_workout_progress(self, user_id, workout_id, exercises_completed, 
                            performance_metrics, notes=None):
        """Log detailed workout progress"""
        try:
            workout_date = datetime.now()
            
            self.cursor.execute("""
            INSERT INTO progress_tracking 
            (user_id, workout_date, workout_id, exercises_completed, performance_metrics, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                workout_date.isoformat(),
                workout_id,
                json.dumps(exercises_completed),
                json.dumps(performance_metrics),
                notes
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error logging workout progress: {e}")
            return None
    
    def get_progress_history(self, user_id, start_date=None, end_date=None):
        """Get workout progress history for a user"""
        query = "SELECT * FROM progress_tracking WHERE user_id = ?"
        params = [user_id]
        
        if start_date:
            query += " AND workout_date >= ?"
            params.append(start_date.isoformat())
            
        if end_date:
            query += " AND workout_date <= ?"
            params.append(end_date.isoformat())
            
        query += " ORDER BY workout_date DESC"
        
        self.cursor.execute(query, params)
        history = []
        
        for row in self.cursor.fetchall():
            entry = dict(row)
            entry['exercises_completed'] = json.loads(entry['exercises_completed'])
            entry['performance_metrics'] = json.loads(entry['performance_metrics'])
            history.append(entry)
            
        return history

    def add_exercise(self, title, body_part, exercise_type, description, equipment, level, 
                    instructions, sports_focus=None, primary_movement_pattern=None,
                    energy_system=None, difficulty=3, primary_benefit=None):
        """Add a new exercise with sports-specific attributes"""
        try:
            sports_focus_json = json.dumps(sports_focus) if sports_focus else None
            
            self.cursor.execute("""
            INSERT INTO exercises 
            (title, body_part, exercise_type, description, equipment, level, instructions,
             sports_focus, primary_movement_pattern, energy_system, difficulty, primary_benefit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                title, body_part, exercise_type, description, equipment, level, instructions,
                sports_focus_json, primary_movement_pattern, energy_system, difficulty, primary_benefit
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error adding exercise: {e}")
            return None
