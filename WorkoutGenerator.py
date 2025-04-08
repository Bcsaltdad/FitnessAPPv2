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
    
    def _ensure_user_profile(self, user_id: int, experience_level: str, 
                           primary_sport: str, workouts_per_week: int,
                           time_per_workout: int, plan_goal: str,
                           specific_focus: List[str] = None) -> int:
        """
        Create or update user profile with sports preferences.
        
        Args:
            user_id: User ID
            experience_level: User experience level
            primary_sport: Primary sport
            workouts_per_week: Workouts per week
            time_per_workout: Minutes per workout
            plan_goal: Primary fitness goal
            specific_focus: Specific focus areas
            
        Returns:
            User profile ID
        """
        # Check if user profile exists
        existing_profile = self.db.get_user_profile(user_id)
        
        # Set fallback/default values
        name = ""
        age = 30
        secondary_sports = []
        goals = [plan_goal]
        
        # Extract secondary sports from specific focus
        if specific_focus and "None" not in specific_focus:
            for focus in specific_focus:
                if focus != primary_sport and focus not in ["None", "Core Strength", 
                                                           "Upper Body", "Lower Body"]:
                    secondary_sports.append(focus)
        
        # Create or update the profile
        profile_id = self.db.create_user_profile(
            user_id=user_id,
            name=name,
            age=age,
            experience_level=experience_level,
            primary_sport=primary_sport,
            secondary_sports=secondary_sports,
            goals=goals,
            training_frequency=workouts_per_week,
            session_duration=time_per_workout
        )
        
        return profile_id
    
    def _determine_primary_sport(self, specific_focus: List[str], 
                               plan_goal: str) -> Optional[str]:
        """
        Determine the primary sport from user input.
        
        Args:
            specific_focus: Specific focus areas selected by user
            plan_goal: Primary fitness goal
            
        Returns:
            Primary sport or None
        """
        # Common sports to detect
        sports = [
            "Running", "Golf", "Tennis", "Swimming", "Cycling", 
            "Football", "Soccer", "Basketball", "Baseball", "Hockey",
            "Volleyball", "Wrestling", "Weightlifting", "CrossFit",
            "Triathlon", "Skiing", "Snowboarding", "Climbing", "Boxing",
            "Martial Arts", "Olympic Lifting", "Powerlifting",
            "Rugby", "Cricket", "Gymnastics", "Dancing"
        ]
        
        # First check specific focus for sports
        if specific_focus and "None" not in specific_focus:
            for focus in specific_focus:
                if focus in sports:
                    return focus
        
        # If no sport found in specific focus, check plan goal
        if "Sports and Athletics" in plan_goal:
            return "Athletic Performance"
        elif "Body Building" in plan_goal:
            return "Bodybuilding"
        elif "Weight Loss" in plan_goal:
            return "General Fitness"
        
        # Default fallback
        return None
    
    def _determine_training_phase(self, plan_goal: str) -> str:
        """Determine the appropriate training phase based on goal."""
        phase_map = {
            "Sports and Athletics": "In-Season",  # Default to in-season for sports
            "Body Building": "Hypertrophy",      # Specific phase for bodybuilding
            "Body Weight Fitness": "General",     # General phase for bodyweight training
            "Weight Loss": "Fat Loss",           # Specific phase for weight loss
            "Mobility Exclusive": "Mobility"      # Specific phase for mobility
        }
        
        return phase_map.get(plan_goal, "General")
    
    def _get_sports_profile(self, sport: str) -> Dict:
        """
        Get or create a sports profile.
        
        Args:
            sport: Name of the sport
            
        Returns:
            Sports profile data
        """
        if not sport:
            # Return a general fitness profile
            return self.planner._create_generic_profile("General Fitness")
        
        # Try to get existing profile
        profile = self.db.get_sports_profile(sport)
        
        if profile:
            return profile
        
        # Create a new profile
        generic_profile = self.planner._create_generic_profile(sport)
        
        # Save the profile to the database
        self.db.create_sports_profile(
            sport=sport,
            required_movements=generic_profile["required_movements"],
            energy_systems=generic_profile["energy_systems"],
            primary_muscle_groups=generic_profile["primary_muscle_groups"],
            injury_risk_areas=generic_profile.get("injury_risk_areas", []),
            training_phase_focus=generic_profile["training_phase_focus"]
        )
        
        return generic_profile
    
    def _create_basic_plan(self, user_id: int, plan_name: str, plan_goal: str,
                          duration_weeks: int, workouts_per_week: int,
                          experience_level: str) -> Optional[int]:
        """
        Create a simplified workout plan as fallback.
        
        Args:
            user_id: User ID
            plan_name: Name of the plan
            plan_goal: Primary fitness goal
            duration_weeks: Duration in weeks
            workouts_per_week: Number of workouts per week
            experience_level: User experience level
            
        Returns:
            Plan ID or None if creation fails
        """
        try:
            # Create a basic plan
            plan_id = self.planner.create_workout_plan(
                user_id=user_id,
                plan_name=plan_name,
                goal=plan_goal,
                duration_weeks=duration_weeks
            )
            
            # Map workout focus based on frequency
            if workouts_per_week <= 2:
                workout_focus = [{"day": 1, "focus": "Full Body"}]
                if workouts_per_week == 2:
                    workout_focus.append({"day": 4, "focus": "Full Body"})
            elif workouts_per_week == 3:
                workout_focus = [
                    {"day": 1, "focus": "Push"},
                    {"day": 3, "focus": "Pull"},
                    {"day": 5, "focus": "Legs"}
                ]
            elif workouts_per_week == 4:
                workout_focus = [
                    {"day": 1, "focus": "Upper Body"},
                    {"day": 2, "focus": "Lower Body"},
                    {"day": 4, "focus": "Upper Body"},
                    {"day": 5, "focus": "Lower Body"}
                ]
            else:
                workout_focus = [
                    {"day": 1, "focus": "Chest"},
                    {"day": 2, "focus": "Back"},
                    {"day": 3, "focus": "Legs"},
                    {"day": 4, "focus": "Shoulders"},
                    {"day": 5, "focus": "Arms"}
                ]
                if workouts_per_week >= 6:
                    workout_focus.append({"day": 6, "focus": "Core"})
            
            # Exercise counts based on experience
            counts = {
                "Beginner": {"main": 2, "accessory": 2},
                "Intermediate": {"main": 3, "accessory": 3},
                "Advanced": {"main": 4, "accessory": 4}
            }.get(experience_level, {"main": 2, "accessory": 2})
            
            # Add exercises for each workout day, for each week
            for week in range(1, duration_weeks + 1):
                for focus in workout_focus:
                    day = focus["day"]
                    body_focus = focus["focus"]
                    
                    # Get main exercises
                    main_exercises = self._get_basic_exercises(
                        body_focus, "Compound", counts["main"]
                    )
                    
                    # Get accessory exercises
                    accessory_exercises = self._get_basic_exercises(
                        body_focus, "Isolation", counts["accessory"]
                    )
                    
                    # Add all exercises to the plan
                    for exercise in main_exercises + accessory_exercises:
                        self.planner.add_workout_to_plan(
                            plan_id=plan_id,
                            exercise_id=exercise["id"],
                            week=week,
                            day=day,
                            target_sets=exercise.get("target_sets", 3),
                            target_reps=exercise.get("target_reps", 10)
                        )
            
            return plan_id
        except Exception as e:
            logging.error(f"Error creating basic plan: {e}")
            return None
    
    def _get_basic_exercises(self, body_focus: str, exercise_type: str, count: int) -> List[Dict]:
        """Get basic exercises for fallback plan."""
        try:
            # Query for exercises
            self.db.cursor.execute(
                "SELECT * FROM exercises WHERE body_part LIKE ? AND exercise_type LIKE ? ORDER BY RANDOM() LIMIT ?",
                (f"%{body_focus}%", f"%{exercise_type}%", count)
            )
            
            exercises = [dict(row) for row in self.db.cursor.fetchall()]
            
            # If not enough exercises found, get some general ones
            if len(exercises) < count:
                self.db.cursor.execute(
                    "SELECT * FROM exercises WHERE exercise_type LIKE ? ORDER BY RANDOM() LIMIT ?",
                    (f"%{exercise_type}%", count - len(exercises))
                )
                exercises.extend([dict(row) for row in self.db.cursor.fetchall()])
            
            # Add default sets/reps
            for exercise in exercises:
                if exercise_type == "Compound":
                    exercise["target_sets"] = 4
                    exercise["target_reps"] = 8
                else:
                    exercise["target_sets"] = 3
                    exercise["target_reps"] = 12
            
            return exercises
        except Exception as e:
            logging.error(f"Error getting basic exercises: {e}")
            return []
