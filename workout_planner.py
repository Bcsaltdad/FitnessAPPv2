import sqlite3
import json
import datetime
import logging
from typing import Dict, List, Any, Tuple, Optional

class WorkoutPlanner:
    def __init__(self, db_connection=None, db_path='fitness.db'):
        """
        Initialize the workout planner with a database connection.
        
        Args:
            db_connection: Optional existing database connection
            db_path: Path to the database file if no connection is provided
        """
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        if db_connection:
            self.db = db_connection
        else:
            self.db = sqlite3.connect(db_path)
        
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()
                
    def create_workout_plan(self, user_id: int, plan_name: str, goal: str, 
                          duration_weeks: int, primary_sport: str = None,
                          training_phase: str = "General") -> int:
        """
        Create a new workout plan for a user.
        
        Args:
            user_id: User ID
            plan_name: Name of the plan
            goal: Primary fitness goal
            duration_weeks: Duration in weeks
            primary_sport: Optional sport focus
            training_phase: Training phase (Off-Season, In-Season, etc.)
            
        Returns:
            ID of the created plan
        """
        created_at = datetime.datetime.now()
        
        try:
            self.cursor.execute('''
            INSERT INTO fitness_plans 
            (user_id, name, goal, duration_weeks, created_at, primary_sport, training_phase)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, plan_name, goal, duration_weeks, created_at, primary_sport, training_phase))
            
            self.db.commit()
            plan_id = self.cursor.lastrowid
            return plan_id
        except sqlite3.Error as e:
            logging.error(f"Error creating workout plan: {e}")
            self.db.rollback()
            raise
    
    def add_workout_to_plan(self, plan_id: int, exercise_id: int, week: int, 
                           day: int, target_sets: int, target_reps: int) -> int:
        """
        Add an exercise to a workout plan.
        
        Args:
            plan_id: Plan ID
            exercise_id: Exercise ID
            week: Week number
            day: Day of the week (1-7)
            target_sets: Target number of sets
            target_reps: Target number of reps or duration
            
        Returns:
            ID of the created workout
        """
        try:
            self.cursor.execute('''
            INSERT INTO plan_workouts 
            (plan_id, exercise_id, week, day, target_sets, target_reps)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (plan_id, exercise_id, week, day, target_sets, target_reps))
            
            self.db.commit()
            workout_id = self.cursor.lastrowid
            return workout_id
        except sqlite3.Error as e:
            logging.error(f"Error adding workout to plan: {e}")
            self.db.rollback()
            raise
    
    def generate_intelligent_plan(self, user_profile: Dict, 
                               sports_profile: Dict = None,
                               duration_weeks: int = 8,
                               current_phase: str = "General") -> Dict:
        """
        Generate an intelligent workout plan based on user profile and sport requirements.
        
        Args:
            user_profile: User profile data
            sports_profile: Sports requirements data
            duration_weeks: Duration in weeks
            current_phase: Training phase
            
        Returns:
            Complete workout plan structure
        """
        # Extract user data
        user_id = user_profile['user_id']
        primary_sport = user_profile.get('primary_sport')
        experience_level = user_profile.get('experience_level', 'Intermediate')
        training_frequency = user_profile.get('training_frequency', 3)
        session_duration = user_profile.get('session_duration', 45)
        goals = user_profile.get('goals', [])
        
        # Create generic sports profile if not provided
        if not sports_profile and primary_sport:
            sports_profile = self._create_generic_profile(primary_sport)
        elif not sports_profile:
            # Create a balanced profile for general fitness
            sports_profile = {
                "required_movements": ["Squat", "Hinge", "Push", "Pull", "Carry"],
                "energy_systems": ["Aerobic", "Anaerobic"],
                "primary_muscle_groups": ["Quadriceps", "Hamstrings", "Chest", "Back", "Shoulders"],
                "injury_risk_areas": [],
                "training_phase_focus": {
                    "General": ["Strength", "Hypertrophy", "Conditioning"]
                }
            }
        
        # Determine the training split based on frequency
        training_split = self._determine_training_split(
            training_frequency, 
            sports_profile,
            experience_level
        )
        
        # Get the focus areas based on the current training phase
        phase_focus = sports_profile.get('training_phase_focus', {}).get(current_phase, [])
        if not phase_focus:
            phase_focus = ["General Strength", "Conditioning", "Core"]
            
        # Create the plan structure
        start_date = datetime.datetime.now()
        end_date = start_date + datetime.timedelta(weeks=duration_weeks)
        
        workout_plan = {
            "user_id": user_id,
            "primary_sport": primary_sport,
            "training_split": training_split,
            "focus_areas": phase_focus,
            "weeks": []
        }
        
        # Generate workout routines for each week
        for week in range(1, duration_weeks + 1):
            # Adjust intensity and volume based on week number (linear periodization)
            intensity_factor = min(0.7 + (week * 0.05), 0.95)  # Increases each week
            volume_factor = 1.0 - (week * 0.02) if week > 3 else 1.0  # Decreases after week 3
            
            week_plan = {
                "week_number": week,
                "intensity": round(intensity_factor * 100),  # As percentage
                "volume": round(volume_factor * 100),  # As percentage
                "workouts": []
            }
            
            # Generate individual workouts for each training day
            for day_config in training_split["days"]:
                day_number = day_config["day"]
                focus = day_config["focus"]
                
                # Get exercises for this workout
                workout_exercises = self._select_exercises_for_workout(
                    focus,
                    primary_sport,
                    experience_level,
                    intensity_factor,
                    volume_factor,
                    session_duration
                )
                
                week_plan["workouts"].append({
                    "day": day_number,
                    "focus": focus,
                    "exercises": workout_exercises
                })
                
            workout_plan["weeks"].append(week_plan)
            
        return workout_plan
        
    def _determine_training_split(self, frequency: int, sports_profile: Dict, 
                               experience_level: str) -> Dict:
        """
        Determine the optimal training split based on training frequency and sport.
        
        Args:
            frequency: Workouts per week
            sports_profile: Sports requirements data
            experience_level: User experience level
            
        Returns:
            Training split configuration
        """
        # Default fallback for any missing data
        if not sports_profile or not isinstance(sports_profile, dict):
            sports_profile = {
                "primary_muscle_groups": ["Full Body"]
            }
            
        if frequency <= 2:
            # For low frequency, use full-body workouts
            return {
                "type": "Full Body",
                "days": [{"day": i+1, "focus": "Full Body"} for i in range(frequency)]
            }
        elif frequency == 3:
            # 3-day split for most sports
            primary_muscles = sports_profile.get('primary_muscle_groups', [])
            if "Lower Body" in primary_muscles and len(primary_muscles) > 2:
                # Sport emphasizes lower body, like running or soccer
                return {
                    "type": "Push/Pull/Legs",
                    "days": [
                        {"day": 1, "focus": "Lower Body/Posterior Chain"},
                        {"day": 2, "focus": "Upper Body Push/Core"},
                        {"day": 3, "focus": "Lower Body/Upper Body Pull"}
                    ]
                }
            else:
                return {
                    "type": "Upper/Lower",
                    "days": [
                        {"day": 1, "focus": "Upper Body"},
                        {"day": 2, "focus": "Lower Body"},
                        {"day": 3, "focus": "Full Body/Functional"}
                    ]
                }
        elif frequency == 4:
            # 4-day split
            return {
                "type": "Upper/Lower",
                "days": [
                    {"day": 1, "focus": "Upper Body Push/Core"},
                    {"day": 2, "focus": "Lower Body/Posterior Chain"},
                    {"day": 3, "focus": "Upper Body Pull/Core"},
                    {"day": 4, "focus": "Lower Body/Functional"}
                ]
            }
        else:
            # 5+ day split
            if experience_level == "Advanced":
                # Body part split for advanced
                return {
                    "type": "Body Part Split",
                    "days": [
                        {"day": 1, "focus": "Chest/Triceps"},
                        {"day": 2, "focus": "Back/Biceps"}, 
                        {"day": 3, "focus": "Legs/Core"},
                        {"day": 4, "focus": "Shoulders/Arms"},
                        {"day": 5, "focus": "Sport-Specific/Conditioning"}
                    ] + ([{"day": 6, "focus": "Mobility/Recovery"}] if frequency >= 6 else [])
                }
            else:
                # Push/Pull/Legs for intermediate
                return {
                    "type": "Push/Pull/Legs",
                    "days": [
                        {"day": 1, "focus": "Push"},
                        {"day": 2, "focus": "Pull"}, 
                        {"day": 3, "focus": "Legs"},
                        {"day": 4, "focus": "Push + Sport-Specific"},
                        {"day": 5, "focus": "Pull + Sport-Specific"}
                    ] + ([{"day": 6, "focus": "Legs/Functional"}] if frequency >= 6 else [])
                }
    
    def _select_exercises_for_workout(self, focus: str, sport: str, experience_level: str,
                                   intensity_factor: float, volume_factor: float,
                                   session_duration: int) -> List[Dict]:
        """
        Select exercises for a workout based on focus and other factors.
        
        Args:
            focus: Workout focus (e.g., "Upper Body")
            sport: Primary sport
            experience_level: User experience level
            intensity_factor: Intensity adjustment factor
            volume_factor: Volume adjustment factor
            session_duration: Workout duration in minutes
            
        Returns:
            List of exercises with training parameters
        """
        # Calculate number of exercises based on session duration and experience
        exercise_count = self._calculate_exercise_counts(experience_level, session_duration, focus)
        
        # Focus keywords for query
        focus_keywords = focus.lower().split('/')
        
        # Select main/compound exercises
        main_exercises = self._select_main_exercises(
            focus_keywords, 
            sport,
            exercise_count["main"],
            experience_level,
            intensity_factor
        )
        
        # Select accessory/isolation exercises
        accessory_exercises = self._select_accessory_exercises(
            focus_keywords,
            sport,
            exercise_count["accessory"],
            volume_factor
        )
        
        # Select sport-specific exercises if applicable
        sport_specific_exercises = []
        if sport and exercise_count["sport_specific"] > 0:
            sport_specific_exercises = self._select_sport_specific_exercises(
                sport,
                exercise_count["sport_specific"]
            )
        
        # Combine all exercises
        all_exercises = main_exercises + accessory_exercises + sport_specific_exercises
        
        return all_exercises
    
    def _calculate_exercise_counts(self, experience_level: str, session_duration: int,
                               focus: str) -> Dict[str, int]:
        """Calculate optimal exercise counts based on user parameters."""
        # Base counts by experience level
        base_counts = {
            "Beginner": {"main": 2, "accessory": 3, "sport_specific": 1},
            "Intermediate": {"main": 3, "accessory": 4, "sport_specific": 2},
            "Advanced": {"main": 4, "accessory": 5, "sport_specific": 3}
        }.get(experience_level, {"main": 2, "accessory": 3, "sport_specific": 1})
        
        # Adjust for session duration (baseline is 60 minutes)
        duration_factor = session_duration / 60
        for key in base_counts:
            base_counts[key] = round(base_counts[key] * duration_factor)
            
        # Adjust for focus type
        if "Full Body" in focus:
            base_counts["main"] = max(2, base_counts["main"] - 1)
            base_counts["accessory"] = max(2, base_counts["accessory"] - 1)
            
        return base_counts
    
    def _select_main_exercises(self, focus_keywords: List[str], sport: str, 
                           count: int, experience_level: str, 
                           intensity_factor: float) -> List[Dict]:
        """Select main/compound exercises for the workout."""
        # Difficulty based on experience
        difficulty_map = {
            "Beginner": [1, 2, 3],
            "Intermediate": [2, 3, 4],
            "Advanced": [3, 4, 5]
        }
        difficulty_range = difficulty_map.get(experience_level, [1, 2, 3])
        
        # Build query for main exercises
        query_parts = []
        params = []
        
        # Add focus-based criteria
        focus_conditions = []
        for keyword in focus_keywords:
            focus_conditions.append("body_part LIKE ?")
            params.append(f"%{keyword}%")
        
        query_parts.append(f"({' OR '.join(focus_conditions)})")
        
        # Add exercise type criteria
        query_parts.append("exercise_type IN ('Strength', 'Compound', 'Power')")
        
        # Add sport-specific criteria if applicable
        if sport:
            query_parts.append("(sports_focus LIKE ? OR sports_focus IS NULL)")
            params.append(f"%{sport}%")
        
        # Add difficulty criteria
        difficulty_placeholders = ', '.join(['?' for _ in difficulty_range])
        query_parts.append(f"(difficulty IS NULL OR difficulty IN ({difficulty_placeholders}))")
        params.extend(difficulty_range)
        
        # Complete the query
        query = f"""
        SELECT * FROM exercises 
        WHERE {' AND '.join(query_parts)}
        ORDER BY RANDOM()
        LIMIT ?
        """
        params.append(count)
        
        # Execute query
        try:
            self.cursor.execute(query, params)
            exercises = [dict(row) for row in self.cursor.fetchall()]
            
            # Fill in missing slots if needed
            if len(exercises) < count:
                missing = count - len(exercises)
                # Use a more general query to find additional exercises
                self._add_fallback_exercises(exercises, "Compound", missing)
            
            # Calculate sets and reps based on experience level and intensity
            for exercise in exercises:
                # Parse JSON fields if needed
                if exercise.get('sports_focus') and isinstance(exercise['sports_focus'], str):
                    try:
                        exercise['sports_focus'] = json.loads(exercise['sports_focus'])
                    except:
                        exercise['sports_focus'] = []
                
                # Calculate sets and reps
                exercise_data = self._calculate_sets_reps(
                    exercise.get('exercise_type', 'Compound'),
                    experience_level,
                    intensity_factor,
                    sport and exercise.get('sports_focus') and sport in exercise.get('sports_focus', [])
                )
                
                exercise.update(exercise_data)
            
            return exercises
        except sqlite3.Error as e:
            logging.error(f"Error selecting main exercises: {e}")
            return []
    
    def _select_accessory_exercises(self, focus_keywords: List[str], sport: str, 
                                 count: int, volume_factor: float) -> List[Dict]:
        """Select accessory/isolation exercises for the workout."""
        # Build query for accessory exercises
        query_parts = []
        params = []
        
        # Add focus-based criteria
        focus_conditions = []
        for keyword in focus_keywords:
            focus_conditions.append("body_part LIKE ?")
            params.append(f"%{keyword}%")
        
        query_parts.append(f"({' OR '.join(focus_conditions)})")
        
        # Add exercise type criteria
        query_parts.append("exercise_type IN ('Isolation', 'Accessory', 'Mobility')")
        
        # Complete the query
        query = f"""
        SELECT * FROM exercises 
        WHERE {' AND '.join(query_parts)}
        ORDER BY RANDOM()
        LIMIT ?
        """
        params.append(count)
        
        # Execute query
        try:
            self.cursor.execute(query, params)
            exercises = [dict(row) for row in self.cursor.fetchall()]
            
            # Fill in missing slots if needed
            if len(exercises) < count:
                missing = count - len(exercises)
                # Use a more general query to find additional exercises
                self._add_fallback_exercises(exercises, "Isolation", missing)
            
            # Format accessory exercises
            for exercise in exercises:
                # Parse JSON fields if needed
                if exercise.get('sports_focus') and isinstance(exercise['sports_focus'], str):
                    try:
                        exercise['sports_focus'] = json.loads(exercise['sports_focus'])
                    except:
                        exercise['sports_focus'] = []
                
                # Default accessory exercise prescription
                exercise.update({
                    "target_sets": max(2, round(3 * volume_factor)),
                    "target_reps": "12-15",
                    "rest": "30-60 seconds",
                    "tempo": "2-0-2", # Concentric-pause-eccentric
                    "type": "Accessory"
                })
            
            return exercises
        except sqlite3.Error as e:
            logging.error(f"Error selecting accessory exercises: {e}")
            return []
    
    def _select_sport_specific_exercises(self, sport: str, count: int) -> List[Dict]:
        """Select sport-specific exercises."""
        if not sport or count == 0:
            return []
            
        # Query for sport-specific exercises
        try:
            query = """
            SELECT * FROM exercises 
            WHERE sports_focus LIKE ?
            ORDER BY RANDOM()
            LIMIT ?
            """
            
            params = [f"%{sport}%", count]
            
            self.cursor.execute(query, params)
            exercises = [dict(row) for row in self.cursor.fetchall()]
            
            # Format sport-specific exercises
            for exercise in exercises:
                # Parse JSON fields if needed
                if exercise.get('sports_focus') and isinstance(exercise['sports_focus'], str):
                    try:
                        exercise['sports_focus'] = json.loads(exercise['sports_focus'])
                    except:
                        exercise['sports_focus'] = []
                
                # Default sport-specific exercise prescription
                exercise.update({
                    "target_sets": 3,
                    "target_reps": "8-12",
                    "rest": "60-90 seconds",
                    "notes": f"Focus on sport-specific movement patterns for {sport}",
                    "type": "Sport-Specific"
                })
            
            return exercises
        except sqlite3.Error as e:
            logging.error(f"Error selecting sport-specific exercises: {e}")
            return []
    
    def _add_fallback_exercises(self, exercises: List[Dict], exercise_type: str, count: int):
        """Add general exercises of a given type to fill gaps."""
        if count <= 0:
            return
            
        # Get IDs of already selected exercises
        existing_ids = [ex['id'] for ex in exercises if 'id' in ex]
        id_exclusion = f"AND id NOT IN ({','.join(['?'] * len(existing_ids))})" if existing_ids else ""
        
        # Query for additional exercises
        try:
            query = f"""
            SELECT * FROM exercises 
            WHERE exercise_type LIKE ? 
            {id_exclusion}
            ORDER BY RANDOM()
            LIMIT ?
            """
            
            params = [f"%{exercise_type}%"]
            if existing_ids:
                params.extend(existing_ids)
            params.append(count)
            
            self.cursor.execute(query, params)
            fallback_exercises = [dict(row) for row in self.cursor.fetchall()]
            
            exercises.extend(fallback_exercises)
        except sqlite3.Error as e:
            logging.error(f"Error adding fallback exercises: {e}")
    
    def _calculate_sets_reps(self, exercise_type: str, experience_level: str, 
                         intensity_factor: float, is_sport_specific: bool) -> Dict:
        """
        Calculate appropriate sets and reps based on exercise type and user level.
        
        Args:
            exercise_type: Type of exercise
            experience_level: User experience level
            intensity_factor: Intensity adjustment (0.0-1.0)
            is_sport_specific: Whether exercise matches sport requirements
            
        Returns:
            Sets, reps, and other training parameters
        """
        base_sets = {
            "Beginner": 3,
            "Intermediate": 4,
            "Advanced": 5
        }.get(experience_level, 3)
        
        # Adjust sets based on intensity factor
        adjusted_sets = round(base_sets * (0.8 + (intensity_factor * 0.4)))
        
        # Set rep ranges based on exercise type
        if exercise_type == 'Power':
            reps = "3-5"
            rest = "2-3 minutes"
            tempo = "X-0-2"  # X = explosive
            intensity = f"{round(85 + (intensity_factor * 10))}%"
        elif exercise_type == 'Strength':
            reps = "5-8"
            rest = "1.5-2 minutes"
            tempo = "2-0-2"
            intensity = f"{round(80 + (intensity_factor * 15))}%"
        elif exercise_type == 'Compound':
            reps = "6-10"
            rest = "1-2 minutes"
            tempo = "2-0-2"
            intensity = f"{round(75 + (intensity_factor * 15))}%"
        else:  # Accessory or other types
            reps = "8-12"
            rest = "60-90 seconds"
            tempo = "2-1-2"
            intensity = f"{round(70 + (intensity_factor * 10))}%"
            
        # Add emphasis for sport-specific exercises
        notes = "Focus on explosive power and control" if is_sport_specific else ""
            
        return {
            "target_sets": adjusted_sets,
            "target_reps": reps,
            "rest": rest,
            "tempo": tempo,
            "intensity": intensity,
            "notes": notes,
            "type": "Main"
        }
    
    def _create_generic_profile(self, sport: str) -> Dict:
        """Create a generic sports profile if specific one doesn't exist."""
        # Set up default values based on sport category
        sport_lower = sport.lower()
        
        if any(x in sport_lower for x in ["running", "cycling", "swimming", "triathlon", "endurance"]):
            # Endurance sports
            profile = {
                "required_movements": ["Squat", "Lunge", "Hinge", "Core Stability"],
                "energy_systems": ["Aerobic", "Lactate Threshold", "VO2 Max"],
                "primary_muscle_groups": ["Quadriceps", "Hamstrings", "Calves", "Core", "Glutes"],
                "injury_risk_areas": ["Knees", "Achilles", "Plantar Fascia", "Hip Flexors"],
                "training_phase_focus": {
                    "Off-Season": ["Strength", "Mobility", "Work Capacity"],
                    "Pre-Season": ["Power Endurance", "Sport-Specific Endurance", "Technical"],
                    "In-Season": ["Maintenance", "Recovery", "Technical"],
                    "Post-Season": ["Recovery", "Mobility", "Imbalance Correction"]
                }
            }
        elif any(x in sport_lower for x in ["football", "basketball", "soccer", "hockey", "lacrosse", "rugby"]):
            # Team field/court sports
            profile = {
                "required_movements": ["Sprint", "Jump", "Deceleration", "Change of Direction", "Rotational Power"],
                "energy_systems": ["Anaerobic", "Aerobic Power", "Phosphagen"],
                "primary_muscle_groups": ["Quadriceps", "Hamstrings", "Glutes", "Core", "Shoulders"],
                "injury_risk_areas": ["ACL", "Ankles", "Shoulders", "Lower Back"],
                "training_phase_focus": {
                    "Off-Season": ["Strength", "Power", "Work Capacity"],
                    "Pre-Season": ["Power", "Speed", "Game-Specific Conditioning"],
                    "In-Season": ["Power Maintenance", "Recovery", "Injury Prevention"],
                    "Post-Season": ["Recovery", "Imbalance Correction", "Mobility"]
                }
            }
        elif any(x in sport_lower for x in ["tennis", "golf", "baseball", "cricket", "throwing"]):
            # Rotational/striking sports
            profile = {
                "required_movements": ["Rotation", "Anti-Rotation", "Hinge", "Single-Leg Stability", "Shoulder Stability"],
                "energy_systems": ["Phosphagen", "Anaerobic", "Aerobic"],
                "primary_muscle_groups": ["Core", "Obliques", "Shoulders", "Upper Back", "Forearms"],
                "injury_risk_areas": ["Shoulders", "Elbows", "Lower Back", "Obliques"],
                "training_phase_focus": {
                    "Off-Season": ["Strength", "Mobility", "Movement Pattern Correction"],
                    "Pre-Season": ["Power", "Rotational Power", "Sport-Specific Conditioning"],
                    "In-Season": ["Power Maintenance", "Recovery", "Injury Prevention"],
                    "Post-Season": ["Recovery", "Mobility", "Imbalance Correction"]
                }
            }
        elif any(x in sport_lower for x in ["weightlifting", "powerlifting", "bodybuilding", "strength"]):
            # Strength sports
            profile = {
                "required_movements": ["Squat", "Deadlift", "Bench Press", "Overhead Press"],
                "energy_systems": ["Phosphagen", "Anaerobic"],
                "primary_muscle_groups": ["Quadriceps", "Hamstrings", "Chest", "Back", "Shoulders"],
                "injury_risk_areas": ["Lower Back", "Shoulders", "Knees", "Elbows"],
                "training_phase_focus": {
                    "Off-Season": ["Hypertrophy", "Work Capacity", "Technique"],
                    "Pre-Season": ["Strength", "Power", "Competition-Specific"],
                    "In-Season": ["Peak Strength", "Technical", "Maintenance"],
                    "Post-Season": ["Recovery", "Hypertrophy", "Weakness Correction"]
                }
            }
        else:
            # General athletic profile
            profile = {
                "required_movements": ["Squat", "Hinge", "Push", "Pull", "Carry", "Rotation"],
                "energy_systems": ["Aerobic", "Anaerobic", "Phosphagen"],
                "primary_muscle_groups": ["Quadriceps", "Hamstrings", "Chest", "Back", "Shoulders", "Core"],
                "injury_risk_areas": ["Lower Back", "Shoulders", "Knees"],
                "training_phase_focus": {
                    "Off-Season": ["Strength", "Hypertrophy", "Work Capacity"],
                    "Pre-Season": ["Power", "Speed", "Sport-Specific"],
                    "In-Season": ["Maintenance", "Recovery", "Injury Prevention"],
                    "Post-Season": ["Recovery", "Mobility", "Weakness Correction"],
                    "General": ["Strength", "Hypertrophy", "Conditioning"]
                }
            }
            
        return profile
    
    def save_generated_plan(self, plan_data: Dict) -> int:
        """Save a generated workout plan to the database."""
        try:
            # Create the plan record
            user_id = plan_data["user_id"]
            plan_name = plan_data.get("plan_name", "Intelligent Workout Plan")
            goals = ", ".join(plan_data.get("focus_areas", ["General Fitness"]))
            duration_weeks = len(plan_data["weeks"])
            primary_sport = plan_data.get("primary_sport")
            
            # Create the plan
            plan_id = self.create_workout_plan(
                user_id,
                plan_name,
                goals,
                duration_weeks,
                primary_sport
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
