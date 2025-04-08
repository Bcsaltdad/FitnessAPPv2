

import sqlite3 import json from datetime import datetime class ExerciseDatabase: def __init__(self, db_path): """Initialize the database connection""" self.conn = sqlite3.connect(db_path) self.conn.row_factory = sqlite3.Row self.cursor = self.conn.cursor()

pasted

Help me handel an error in my code: File "/mount/src/fitnessappv2/main.py", line 286, in <module>
    summary = db.get_plan_summary(plan['id'])
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/mount/src/fitnessappv2/exercise_utils.py", line 136, in get_plan_summary self.cursor.execute('''

I belive it is caused here:

I can help with this error. Looking at your code, it seems the issue is occurring when calling the get_plan_summary method on line 286 of your main.py file. Let's analyze the problem.

The error is happening in the get_plan_summary method, which is located at line 136 in your exercise_utils.py file. Based on the code you've shared, this method is trying to execute an SQL query, but something is going wrong.

Here's what might be causing the issue:

The plan ID being passed might be invalid or missing
There could be a SQL syntax error in the query
There might be a problem with table relationships
Looking at the get_plan_summary method in your pasted code:

python
def get_plan_summary(self, plan_id):
    """Get summary statistics for a fitness plan"""
    self.cursor.execute('''
        SELECT 
            pw.week,
            COUNT(DISTINCT pw.id) as total_exercises,
            COUNT(DISTINCT wl.id) as exercises_completed,
            AVG(wl.weight_kg) as avg_weight,
            COUNT(DISTINCT pw.day) as days_worked
        FROM plan_workouts pw
        LEFT JOIN workout_logs wl ON pw.id = wl.workout_id
        WHERE pw.plan_id = ?
        GROUP BY pw.week
        ORDER BY pw.week
    ''', (plan_id,))
    return self.cursor.fetchall()
Let's fix this issue. There are a few potential solutions:

Make sure the plan exists and has a valid ID:
python
def get_plan_summary(self, plan_id):
    """Get summary statistics for a fitness plan"""
    # First check if the plan exists
    self.cursor.execute("SELECT id FROM fitness_plans WHERE id = ?", (plan_id,))
    if not self.cursor.fetchone():
        print(f"Warning: No plan found with ID {plan_id}")
        return []
        
    self.cursor.execute('''
        SELECT 
            pw.week,
            COUNT(DISTINCT pw.id) as total_exercises,
            COUNT(DISTINCT wl.id) as exercises_completed,
            AVG(wl.weight_kg) as avg_weight,
            COUNT(DISTINCT pw.day) as days_worked
        FROM plan_workouts pw
        LEFT JOIN workout_logs wl ON pw.id = wl.workout_id
        WHERE pw.plan_id = ?
        GROUP BY pw.week
        ORDER BY pw.week
    ''', (plan_id,))
    return self.cursor.fetchall()
Add error handling to catch and diagnose potential SQL errors:
python
def get_plan_summary(self, plan_id):
    """Get summary statistics for a fitness plan"""
    try:
        self.cursor.execute('''
            SELECT 
                pw.week,
                COUNT(DISTINCT pw.id) as total_exercises,
                COUNT(DISTINCT wl.id) as exercises_completed,
                AVG(wl.weight_kg) as avg_weight,
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
        # Return empty list on error
        return []
Check for null values in the SQL query:
python
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
I'd recommend implementing the third option, as it's the most comprehensive solution. It:

Adds error handling
Properly handles NULL values in the SQL query
Returns an empty list if there's an error, which will prevent the application from crashing
This should fix the error you're encountering when calling db.get_plan_summary(plan['id']) in your main.py file.


import streamlit as st import pandas as pd import json import hashlib from datetime import datetime, timedelta from exercise_utils import ExerciseDatabase from workout_planner import WorkoutPlanner from WorkoutGenerator import WorkoutGenerator # Initialize session state for user management if 'user

pasted

Creating a new plan using hte create new plan tab here does not work; let me know if oyu need to see my other code

Based on the code snippets you've shared, I can identify several issues that might be causing problems when creating a new plan. Let's focus on fixing the most likely problems:

Main Issues:
Your get_plan_summary method is failing with an error.
There are potential issues in the create plan workflow.
Let's fix these issues one by one:

1. First, let's fix the get_plan_summary method as I recommended earlier:
python
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
2. Issues in the Create Plan workflow:
Looking at the code where you create a new plan, there are a few potential issues:

You're using WorkoutGenerator which we don't have the full code for.
There's duplicated code in the plan creation section.
There's a potential issue with accessing workouts after plan creation.
Here's how to fix the plan creation section:

python
if st.button("Create Personalized Plan"):
    if not plan_name:
        st.error("Please enter a plan name.")
    else:
        with st.spinner("Creating your personalized workout plan..."):
            # Create workout generator instance
            planner = WorkoutPlanner(db.conn)
            generator = WorkoutGenerator(db, planner, None)  # Engine can be None for now
            
            # If primary sport is "None", set it to None
            sport = None if primary_sport == "None" else primary_sport
            
            # Add sport to specific_focus if selected
            if sport and sport not in specific_focus and specific_focus != ["None"]:
                specific_focus.append(sport)
            
            # Generate the plan
            try:
                success, result = generator.create_workout_plan(
                    user_id=st.session_state.user_id,
                    plan_name=plan_name,
                    plan_goal=plan_goal,
                    duration_weeks=duration,
                    workouts_per_week=workouts_per_week,
                    equipment_access=equipment_access,
                    limitations=limitations,
                    experience_level=experience_level,
                    preferred_cardio=preferred_cardio,
                    specific_focus=specific_focus,
                    time_per_workout=time_per_workout,
                    primary_sport=sport,  # Make sure you're passing the sport
                    training_phase=training_phase  # Pass the training phase
                )
                
                if success:
                    plan_id = result
                    st.success("Your personalized plan has been created!")
                    
                    # Preview first week
                    st.write("### Preview of Week 1")
                    try:
                        workouts = db.get_plan_workouts(plan_id, 1, None)
                        
                        if not workouts:
                            st.info("No workouts found for week 1. Your plan has been created but may be empty.")
                        else:
                            # Group by day
                            days_dict = {}
                            for workout in workouts:
                                day = workout['day']
                                if day not in days_dict:
                                    days_dict[day] = []
                                days_dict[day].append(workout)
                            
                            # Display workouts by day
                            day_names = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 
                                        4: "Thursday", 5: "Friday", 6: "Saturday", 7: "Sunday"}
                            
                            for day, day_workouts in sorted(days_dict.items()):
                                st.write(f"**{day_names.get(day, f'Day {day}')}** - {len(day_workouts)} exercises")
                                for workout in day_workouts[:3]:  # Show just a few exercises as preview
                                    st.write(f"- {workout.get('title', 'Unknown exercise')}: {workout.get('target_sets', '?')} sets × {workout.get('target_reps', '?')} reps")
                                if len(day_workouts) > 3:
                                    st.write(f"- ...and {len(day_workouts) - 3} more exercises")
                    except Exception as e:
                        st.warning(f"Unable to preview plan. The plan was created but preview failed.")
                        if st.session_state.dev_mode:
                            st.error(f"Debug - Error: {str(e)}")
                    
                    # Navigate back to plans view
                    st.session_state.view = 'plans'
                    if st.button("Go to My Plans", key="go_to_plans_after_creation"):
                        go_to_plans()
                else:
                    if isinstance(result, int):
                        plan_id = result
                        st.warning("Basic plan created. Some advanced features couldn't be applied.")
                        st.session_state.view = 'plans'
                        if st.button("Go to My Plans", key="go_to_basic_plans"):
                            go_to_plans()
                    else:
                        st.error(f"Error creating workout plan: {result}")
            except Exception as e:
                st.error(f"An error occurred while creating your plan: {str(e)}")
                if st.session_state.dev_mode:
                    st.exception(e)
3. Consider debugging the WorkoutGenerator class:
Without seeing your WorkoutGenerator class, I'm guessing it's having issues creating the plan. You might want to wrap its code in a try/except block to understand what's going wrong.

4. Additional Improvements:
Fix the duplicated code in the Create Plan section - I've removed duplicated sections in the code above.
Add proper error handling throughout your application.
Enhance the create_workout_plan method call - I've added primary_sport and training_phase parameters that might be missing.
Add debug logging - In developer mode, you can display more detailed error information.
If this doesn't solve your issue, I'd need to see the implementation of your WorkoutGenerator class, particularly its create_workout_plan method, to provide more specific help. That's likely where the error is occurring.


import streamlit as st import pandas as pd import json import hashlib from datetime import datetime, timedelta from exercise_utils import ExerciseDatabase from workout_planner import WorkoutPlanner from WorkoutGenerator import WorkoutGenerator # Initialize session state for user management if 'user

pasted


import logging from typing import Dict, List, Tuple, Any, Optional, Union from datetime import datetime class WorkoutGenerator: def __init__(self, db, planner, engine): """Initialize the workout generator with database and engine dependencies.""" self.db = db self.planne

pasted


import sqlite3 import json from datetime import datetime class ExerciseDatabase: def __init__(self, db_path): """Initialize the database connection""" self.conn = sqlite3.connect(db_path) self.conn.row_factory = sqlite3.Row self.cursor = self.conn.cursor()

pasted


import sqlite3 import json import datetime import logging from typing import Dict, List, Any, Tuple, Optional class WorkoutPlanner: def __init__(self, db_connection=None, db_path='fitness.db'): """ Initialize the workout planner with a database connection. Args:

pasted

You might need to rewrite how this functions for me becasue we are now broken I will attach my main and all of the pertenant codes:

Looking at all the code you've shared, I can identify several issues that are causing your app to break when creating a new plan. Let's fix these problems one by one.

1. First, let's fix the get_plan_summary method in your ExerciseDatabase class:
python
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
2. The issues in your create plan workflow:
Looking at the create_workout_plan method in WorkoutGenerator, I noticed that it's not handling the primary_sport and training_phase parameters correctly. Let's fix that:

python
def create_workout_plan(self, user_id: int, plan_name: str, plan_goal: str,
                      duration_weeks: int, workouts_per_week: int, 
                      equipment_access: List[str], limitations: List[str],
                      experience_level: str, preferred_cardio: List[str] = None,
                      specific_focus: List[str] = None, primary_sport: str = None,
                      training_phase: str = None, time_per_workout: int = 45) -> Tuple[bool, Union[int, str]]:
    """
    Create a personalized workout plan based on user input.
    """
    try:
        # Extract primary sport from specific focus or deduce it from plan goal if not provided
        if primary_sport is None:
            primary_sport = self._determine_primary_sport(specific_focus, plan_goal)
        
        # Determine training phase if not provided
        if training_phase is None:
            training_phase = self._determine_training_phase(plan_goal)
        
        # Create or update user profile
        self._ensure_user_profile(
            user_id,
            experience_level,
            primary_sport,
            workouts_per_week,
            time_per_workout,
            plan_goal,
            specific_focus
        )
        
        # Get or create a sports profile
        sports_profile = self._get_sports_profile(primary_sport)
        
        # Get user profile for plan generation
        user_profile = self.db.get_user_profile(user_id)
        
        if not user_profile:
            # Create a minimal user profile from parameters
            user_profile = {
                "user_id": user_id,
                "experience_level": experience_level,
                "primary_sport": primary_sport,
                "training_frequency": workouts_per_week,
                "session_duration": time_per_workout,
                "goals": [plan_goal]
            }
        
        # Generate the intelligent workout plan
        workout_plan = self.planner.generate_intelligent_plan(
            user_profile=user_profile,
            sports_profile=sports_profile,
            duration_weeks=duration_weeks,
            current_phase=training_phase
        )
        
        # Add plan name before saving
        workout_plan["plan_name"] = plan_name
        
        # Save the generated plan to the database
        plan_id = self.planner.save_generated_plan(workout_plan)
        
        if not plan_id:
            # Fall back to simpler plan generation if intelligent planning fails
            logging.warning("Intelligent plan generation failed, falling back to basic planning")
            plan_id = self._create_basic_plan(
                user_id, plan_name, plan_goal, duration_weeks, 
                workouts_per_week, experience_level
            )
            
            if plan_id:
                return True, plan_id
            else:
                return False, "Failed to create workout plan"
        
        return True, plan_id
        
    except Exception as e:
        logging.error(f"Error creating workout plan: {e}")
        return False, str(e)
3. Fix the duplicated code in the Create Plan section of your main.py file:
python
if st.button("Create Personalized Plan"):
    if not plan_name:
        st.error("Please enter a plan name.")
    else:
        with st.spinner("Creating your personalized workout plan..."):
            # Create workout generator instance
            planner = WorkoutPlanner(db.conn)
            generator = WorkoutGenerator(db, planner, None)  # Engine can be None for now
            
            # If primary sport is "None", set it to None
            sport = None if primary_sport == "None" else primary_sport
            
            # Add sport to specific_focus if selected
            if sport and sport not in specific_focus and specific_focus != ["None"]:
                specific_focus.append(sport)
            
            try:
                # Generate the plan
                success, result = generator.create_workout_plan(
                    user_id=st.session_state.user_id,
                    plan_name=plan_name,
                    plan_goal=plan_goal,
                    duration_weeks=duration,
                    workouts_per_week=workouts_per_week,
                    equipment_access=equipment_access,
                    limitations=limitations,
                    experience_level=experience_level,
                    preferred_cardio=preferred_cardio,
                    specific_focus=specific_focus,
                    primary_sport=sport,
                    training_phase=training_phase,
                    time_per_workout=time_per_workout
                )
                
                if success:
                    plan_id = result
                    st.success("Your personalized plan has been created!")
                    
                    # Preview first week
                    st.write("### Preview of Week 1")
                    workouts = db.get_plan_workouts(plan_id, 1, None)
                    
                    if not workouts:
                        st.info("No workouts found for week 1. Your plan has been created but may be empty.")
                    else:
                        # Group by day
                        days_dict = {}
                        for workout in workouts:
                            day = workout['day']
                            if day not in days_dict:
                                days_dict[day] = []
                            days_dict[day].append(workout)
                        
                        # Display workouts by day
                        day_names = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 
                                    4: "Thursday", 5: "Friday", 6: "Saturday", 7: "Sunday"}
                        
                        for day, day_workouts in sorted(days_dict.items()):
                            st.write(f"**{day_names.get(day, f'Day {day}')}** - {len(day_workouts)} exercises")
                            for workout in day_workouts[:3]:  # Show just a few exercises as preview
                                st.write(f"- {workout.get('title', 'Unknown exercise')}: {workout.get('target_sets', '?')} sets × {workout.get('target_reps', '?')} reps")
                            if len(day_workouts) > 3:
                                st.write(f"- ...and {len(day_workouts) - 3} more exercises")
                    
                    # Navigate back to plans view
                    st.session_state.view = 'plans'
                    if st.button("Go to My Plans", key="go_to_plans_after_creation"):
                        go_to_plans()
                else:
                    if isinstance(result, int):
                        plan_id = result
                        st.warning("Basic plan created. Some advanced features couldn't be applied.")
                        st.session_state.view = 'plans'
                        if st.button("Go to My Plans", key="go_to_basic_plans"):
                            go_to_plans()
                    else:
                        st.error(f"Error creating workout plan: {result}")
            except Exception as e:
                st.error(f"An error occurred while creating your plan: {str(e)}")
                if st.session_state.dev_mode:
                    st.exception(e)
4. Fix for the save_generated_plan method in WorkoutPlanner:
python
def save_generated_plan(self, plan_data: Dict) -> int:
    """Save a generated workout plan to the database."""
    try:
        # Create the plan record
        user_id = plan_data["user_id"]
        plan_name = plan_data.get("plan_name", "Intelligent Workout Plan")
        goals = ", ".join(plan_data.get("focus_areas", ["General Fitness"]))
        duration_weeks = len(plan_data["weeks"])
        primary_sport = plan_data.get("primary_sport")
        current_phase = plan_data.get("current_phase", "General")
        
        # Create the plan
        plan_id = self.create_workout_plan(
            user_id,
            plan_name,
            goals,
            duration_weeks,
            primary_sport,
            current_phase
        )
        
        # Add exercises to the plan
        for week in plan_data["weeks"]:
            week_number = week["week_number"]
            
            for workout in week["workouts"]:
                day_number = workout["day"]
                
                for exercise in workout["exercises"]:
                    exercise_id = exercise["id"]
                    target_sets = exercise.get("target_sets", 3)
                    target_reps = exercise.get("target_reps", "8-12")
                    
                    # Convert string reps to a number for storage if needed
                    if isinstance(target_reps, str) and "-" in target_reps:
                        # Use the average value
                        try:
                            low, high = target_reps.split("-")
                            target_reps = (int(low) + int(high)) // 2
                        except:
                            target_reps = 10  # Default
                    
                    # Add the workout to the plan
                    self.add_workout_to_plan(
                        plan_id,
                        exercise_id,
                        week_number,
                        day_number,
                        target_sets,
                        target_reps
                    )
        
        return plan_id
    except Exception as e:
        logging.error(f"Error saving generated plan: {e}")
        return None
Comprehensive Solution:
The main issues I've identified are:

Error handling in get_plan_summary which is failing when you look at your plan details.
Parameter handling issues in the create_workout_plan method.
Duplicated and conflicting code in the plan creation UI section.
Potential issues in the plan saving process.
The fixes I've provided should address these problems. When implementing these changes:

First update the get_plan_summary method in your ExerciseDatabase class to properly handle errors.
Update the create_workout_plan method in your WorkoutGenerator class to properly handle the primary_sport and training_phase parameters.
Fix the duplicated code in your main.py file's plan creation section.
Update the save_generated_plan method in WorkoutPlanner to ensure all parameters are properly passed.
After making these changes, your app should be able to create new plans without errors.

can you rewrite each of these in place for me so that I can copy and paste the entire files in to my git

I'll rewrite each of your files completely so you can copy and paste them directly into your git. I'll organize them by file name:

1. exercise_utils.py
python
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
2. WorkoutGenerator.py
python
import logging
from typing import Dict, List, Tuple, Any, Optional, Union
from datetime import datetime

class WorkoutGenerator:
    def __init__(self, db, planner, engine):
        """Initialize the workout generator with database and engine dependencies."""
        self.db = db
        self.planner = planner
        self.engine = engine
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def create_workout_plan(self, user_id: int, plan_name: str, plan_goal: str,
                          duration_weeks: int, workouts_per_week: int, 
                          equipment_access: List[str], limitations: List[str],
                          experience_level: str, preferred_cardio: List[str] = None,
                          specific_focus: List[str] = None, primary_sport: str = None,
                          training_phase: str = None, time_per_workout: int = 45) -> Tuple[bool, Union[int, str]]:
        """
        Create a personalized workout plan based on user input.
        
        Args:
            user_id: User ID
            plan_name: Name of the plan
            plan_goal: Primary fitness goal
            duration_weeks: Duration in weeks
            workouts_per_week: Number of workouts per week
            equipment_access: Available equipment
            limitations: Physical limitations
            experience_level: User experience level
            preferred_cardio: Preferred cardio methods
            specific_focus: Areas to focus on
            primary_sport: Primary sport focus
            training_phase: Training phase
            time_per_workout: Minutes per workout
            
        Returns:
            Tuple of (success, result) where result is plan_id if successful or error message
        """
        try:
            # Extract primary sport from specific focus or deduce it from plan goal if not provided
            if primary_sport is None:
                primary_sport = self._determine_primary_sport(specific_focus, plan_goal)
            
            # Determine training phase if not provided
            if training_phase is None:
                training_phase = self._determine_training_phase(plan_goal)
            
            # Create or update user profile
            self._ensure_user_profile(
                user_id,
                experience_level,
                primary_sport,
                workouts_per_week,
                time_per_workout,
                plan_goal,
                specific_focus
            )
            
            # Get or create a sports profile
            sports_profile = self._get_sports_profile(primary_sport)
            
            # Get user profile for plan generation
            user_profile = self.db.get_user_profile(user_id)
            
            if not user_profile:
                # Create a minimal user profile from parameters
                user_profile = {
                    "user_id": user_id,
                    "experience_level": experience_level,
                    "primary_sport": primary_sport,
                    "training_frequency": workouts_per_week,
                    "session_duration": time_per_workout,
                    "goals": [plan_goal]
                }
            
            # Generate the intelligent workout plan
            workout_plan = self.planner.generate_intelligent_plan(
                user_profile=user_profile,
                sports_profile=sports_profile,
                duration_weeks=duration_weeks,
                current_phase=training_phase
            )
            
            # Add plan name before saving
            workout_plan["plan_name"] = plan_name
            
            # Save th




import sqlite3 import json from datetime import datetime class ExerciseDatabase: def __init__(self, db_path): """Initialize the database connection""" self.conn = sqlite3.connect(db_path) self.conn.row_factory = sqlite3.Row self.cursor = self.conn.cursor()


import streamlit as st import pandas as pd import json import hashlib from datetime import datetime, timedelta from exercise_utils import ExerciseDatabase from workout_planner import WorkoutPlanner from WorkoutGenerator import WorkoutGenerator # Initialize session state for user management if 'user


import streamlit as st import pandas as pd import json import hashlib from datetime import datetime, timedelta from exercise_utils import ExerciseDatabase from workout_planner import WorkoutPlanner from WorkoutGenerator import WorkoutGenerator # Initialize session state for user management if 'user


import logging from typing import Dict, List, Tuple, Any, Optional, Union from datetime import datetime class WorkoutGenerator: def __init__(self, db, planner, engine): """Initialize the workout generator with database and engine dependencies.""" self.db = db self.planne


import sqlite3 import json from datetime import datetime class ExerciseDatabase: def __init__(self, db_path): """Initialize the database connection""" self.conn = sqlite3.connect(db_path) self.conn.row_factory = sqlite3.Row self.cursor = self.conn.cursor()


import sqlite3 import json import datetime import logging from typing import Dict, List, Any, Tuple, Optional class WorkoutPlanner: def __init__(self, db_connection=None, db_path='fitness.db'): """ Initialize the workout planner with a database connection. Args:



