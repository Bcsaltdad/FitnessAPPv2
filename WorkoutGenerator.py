import json
import random
from datetime import datetime

class WorkoutGenerator:
    """
    WorkoutGenerator handles the creation of customized workout plans 
    based on user preferences and goals.
    """

    def __init__(self, db_connection, workout_planner, workout_engine=None):
        """
        Initialize the WorkoutGenerator with required connections and components

        Args:
            db_connection: Database connection object
            workout_planner: Instance of WorkoutPlanner
            workout_engine: Optional instance of WorkoutEngine
        """
        self.db = db_connection
        self.planner = workout_planner
        self.engine = workout_engine

    def create_workout_plan(self, user_id, plan_name, plan_goal, duration_weeks, 
                           workouts_per_week, equipment_access, limitations,
                           experience_level, preferred_cardio=None, specific_focus=None, 
                           time_per_workout=45):
        """
        Creates a comprehensive workout plan based on user preferences.

        Returns:
            tuple: (success, plan_id or error message)
        """
        # Create plan details dictionary
        plan_details = {
            "workouts_per_week": workouts_per_week,
            "equipment_access": equipment_access,
            "limitations": limitations,
            "preferred_cardio": preferred_cardio or ["HIIT"],
            "specific_focus": specific_focus or ["None"],
            "time_per_workout": time_per_workout,
            "experience_level": experience_level
        }

        try:
            # Create distribution of days based on goal and workouts_per_week
            focus_distribution = self._create_focus_distribution(
                workouts_per_week, 
                plan_goal, 
                specific_focus, 
                preferred_cardio
            )

            # Adapt focus distribution based on equipment
            focus_distribution = self._adapt_for_equipment(focus_distribution, equipment_access)

            # Ensure the focus distribution accounts for exactly the number of days per week
            focus_distribution = self._normalize_focus_distribution(focus_distribution, workouts_per_week)

            # Create the actual workout plan using the planner
            workout_plan = self.planner.create_workout_plan(
                days=workouts_per_week,
                focus=focus_distribution,
                equipment=equipment_access,
                limitations=limitations,
                experience_level=experience_level,
                goal=plan_goal
            )

            # Validate and fix the plan if needed
            is_valid, validation_message = self._validate_workout_plan(workout_plan, plan_goal, experience_level)

            if not is_valid:
                print(f"Plan validation warning: {validation_message}")
                workout_plan = self._fix_workout_plan(workout_plan, plan_goal, experience_level)

            # Create plan in database
            plan_id = self.db.create_fitness_plan(
                name=plan_name,
                goal=plan_goal,
                duration_weeks=duration_weeks,
                plan_details=json.dumps(plan_details),
                user_id=user_id
            )

            # Add workouts to the database for each week and day
            self._add_workouts_to_database(plan_id, workout_plan, duration_weeks, plan_goal, experience_level)

            return True, plan_id

        except Exception as e:
            print(f"Error creating workout plan: {str(e)}")
            # Create a basic plan as fallback
            try:
                plan_id = self.db.create_fitness_plan(
                    name=plan_name,
                    goal=plan_goal,
                    duration_weeks=duration_weeks,
                    plan_details=json.dumps(plan_details),
                    user_id=user_id
                )
                # Add some basic exercises
                self._add_basic_exercises(plan_id, workouts_per_week, duration_weeks, plan_goal, experience_level)
                return False, plan_id
            except Exception as fallback_error:
                return False, str(fallback_error)

    def _create_focus_distribution(self, workouts_per_week, goal, specific_focus, preferred_cardio):
        """
        Creates workout focus distribution based on goal and preferences
        """
        # Base distributions by number of workouts per week
        if workouts_per_week <= 3:
            # Simplified approach for fewer workouts
            base_distributions = {
                "Body Building": {
                    1: {"Day 1": "Full Body"},
                    2: {"Day 1": "Upper Body", "Day 2": "Lower Body"},
                    3: {"Day 1": "Push/Chest/Shoulders", "Day 2": "Pull/Back/Arms", "Day 3": "Legs/Glutes"}
                },
                "Weight Loss": {
                    1: {"Day 1": "Full Body/HIIT"},
                    2: {"Day 1": "Cardio/HIIT", "Day 2": "Strength/Full Body"},
                    3: {"Day 1": "Upper Body/HIIT", "Day 2": "Lower Body/HIIT", "Day 3": "Full Body/Cardio"}
                },
                "Body Weight Fitness": {
                    1: {"Day 1": "Full Body/Calisthenics"},
                    2: {"Day 1": "Upper Body/Core", "Day 2": "Lower Body/Mobility"},
                    3: {"Day 1": "Push/Core", "Day 2": "Pull/Flexibility", "Day 3": "Legs/Cardio"}
                },
                "Mobility Exclusive": {
                    1: {"Day 1": "Full Body/Mobility"},
                    2: {"Day 1": "Upper Body/Mobility", "Day 2": "Lower Body/Mobility"},
                    3: {"Day 1": "Dynamic/Flow", "Day 2": "Strength/Stability", "Day 3": "Deep Stretch/Recovery"}
                },
                "Sports and Athletics": {
                    1: {"Day 1": "Full Body/Athletic"},
                    2: {"Day 1": "Power/Strength", "Day 2": "Speed/Agility"},
                    3: {"Day 1": "Upper Body/Power", "Day 2": "Lower Body/Speed", "Day 3": "Core/Agility"}
                }
            }

            # Get the distribution for the specific goal or default to Sports/Athletics
            goal_distro = base_distributions.get(goal, base_distributions["Sports and Athletics"])
            return goal_distro.get(workouts_per_week, {"Day 1": "Full Body"})

        elif workouts_per_week <= 5:
            # Intermediate approach (4-5 days)
            base_distributions = {
                "Body Building": {
                    "Day 1": "Chest/Triceps",
                    "Day 2": "Back/Biceps",
                    "Day 3": "Legs/Glutes",
                    "Day 4": "Shoulders/Arms",
                    "Day 5": "Lagging Areas/Core"
                },
                "Weight Loss": {
                    "Day 1": "Upper Body/HIIT",
                    "Day 2": "Lower Body/HIIT",
                    "Day 3": "Cardio/HIIT",
                    "Day 4": "Full Body Circuit",
                    "Day 5": "Active Recovery/Mobility"
                },
                "Body Weight Fitness": {
                    "Day 1": "Push/Core",
                    "Day 2": "Pull/Arms",
                    "Day 3": "Legs/Plyometrics",
                    "Day 4": "Upper Body/Skill",
                    "Day 5": "Core/Mobility"
                },
                "Mobility Exclusive": {
                    "Day 1": "Upper Body/Mobility",
                    "Day 2": "Lower Body/Mobility",
                    "Day 3": "Dynamic Flow/Balance",
                    "Day 4": "Yoga/Stretch",
                    "Day 5": "Corrective/Stability"
                },
                "Sports and Athletics": {
                    "Day 1": "Upper Body/Power",
                    "Day 2": "Lower Body/Strength",
                    "Day 3": "Core/Rotational",
                    "Day 4": "Power/Plyometrics",
                    "Day 5": "Speed/Agility/Conditioning"
                }
            }

            # Get distribution for specific goal
            return base_distributions.get(goal, base_distributions["Sports and Athletics"])

        else:
            # Advanced approach (6-7 days)
            base_distributions = {
                "Body Building": {
                    "Day 1": "Chest/Triceps",
                    "Day 2": "Back/Biceps",
                    "Day 3": "Legs/Calves",
                    "Day 4": "Shoulders/Arms",
                    "Day 5": "Chest/Back",
                    "Day 6": "Legs/Core",
                    "Day 7": "Active Recovery"
                },
                "Weight Loss": {
                    "Day 1": "Upper Push/HIIT",
                    "Day 2": "Upper Pull/HIIT",
                    "Day 3": "Lower Body/HIIT",
                    "Day 4": "Cardio/Intervals",
                    "Day 5": "Full Body Circuit",
                    "Day 6": "Cardio/Fat Burn",
                    "Day 7": "Active Recovery/Mobility"
                },
                "Body Weight Fitness": {
                    "Day 1": "Push/Core",
                    "Day 2": "Pull/Arms",
                    "Day 3": "Legs/Lower",
                    "Day 4": "Push Variation/Skill",
                    "Day 5": "Pull Variation/Core",
                    "Day 6": "Skills/Technique",
                    "Day 7": "Mobility/Recovery"
                },
                "Mobility Exclusive": {
                    "Day 1": "Upper Body/Mobility",
                    "Day 2": "Lower Body/Mobility",
                    "Day 3": "Dynamic Flow/Balance",
                    "Day 4": "Deep Stretch/Flexibility",
                    "Day 5": "Yoga/Integration",
                    "Day 6": "Corrective/Prehab",
                    "Day 7": "Gentle Recovery/Restoration"
                },
                "Sports and Athletics": {
                    "Day 1": "Upper Body/Power",
                    "Day 2": "Lower Body/Strength",
                    "Day 3": "Core/Stability",
                    "Day 4": "Power/Explosiveness",
                    "Day 5": "Speed/Agility",
                    "Day 6": "Conditioning/Endurance",
                    "Day 7": "Recovery/Mobility"
                }
            }

            return base_distributions.get(goal, base_distributions["Sports and Athletics"])

    def _adapt_for_equipment(self, focus_distribution, equipment_access):
        """
        Adapts focus distribution based on available equipment
        """
        # If no equipment or limited equipment, emphasize bodyweight exercises
        if "No Equipment" in equipment_access or len(equipment_access) <= 1:
            new_distribution = {}
            for day, focus in focus_distribution.items():
                # Add bodyweight qualifier to focus areas
                if "Bodyweight" not in focus:
                    if "Mobility" in focus or "Recovery" in focus:
                        # These are already bodyweight-friendly
                        new_distribution[day] = focus
                    else:
                        new_distribution[day] = focus + "/Bodyweight"
                else:
                    new_distribution[day] = focus
            return new_distribution

        return focus_distribution

    def _normalize_focus_distribution(self, focus_distribution, workouts_per_week):
        """
        Ensures the focus distribution has exactly the required number of days
        """
        # If we have too few days
        if len(focus_distribution) < workouts_per_week:
            # Add additional full body or recovery days
            for day in range(len(focus_distribution) + 1, workouts_per_week + 1):
                if day % 3 == 0:
                    focus_distribution[f"Day {day}"] = "Recovery/Mobility"
                else:
                    focus_distribution[f"Day {day}"] = "Full Body"

        # If we have too many days, remove the excess
        elif len(focus_distribution) > workouts_per_week:
            # Sort keys to ensure predictable removal
            days = sorted(focus_distribution.keys())
            # Keep just the first workouts_per_week days
            focus_distribution = {day: focus_distribution[day] for day in days[:workouts_per_week]}

        return focus_distribution

    def _validate_workout_plan(self, workout_plan, goal, experience_level):
        """
        Validates a workout plan meets criteria based on goal and experience
        """
        # Check if enough exercises per day
        for day, exercises in workout_plan.items():
            if len(exercises) < 6:  # We want at least 6 exercises
                return False, f"Not enough exercises for {day} (found {len(exercises)}, need at least 6)"

        # Check muscle group balance across the week
        all_exercises = []
        for day, exercises in workout_plan.items():
            all_exercises.extend(exercises)

        muscle_counts = {}
        for exercise in all_exercises:
            body_part = exercise.get('body_part', '').lower()
            if body_part:
                for part in body_part.split('/'):
                    part = part.strip()
                    if part:
                        muscle_counts[part] = muscle_counts.get(part, 0) + 1

        # Ensure balanced approach 
        min_threshold = 2  # Minimum exercises per major muscle group
        major_muscles = ['chest', 'back', 'legs', 'shoulders', 'arms', 'core']

        missing_muscles = []
        for muscle in major_muscles:
            if muscle_counts.get(muscle, 0) < min_threshold:
                missing_muscles.append(muscle)

        if missing_muscles:
            return False, f"Not enough exercises for: {', '.join(missing_muscles)}"

        # Check goal-specific requirements
        if "Body Building" in goal:
            exercise_types = [e.get('exercise_type', '').lower() for e in all_exercises]
            isolation_count = sum(1 for t in exercise_types if 'isolation' in t)

            if isolation_count < len(all_exercises) * 0.3:  # At least 30% isolation exercises
                return False, f"Not enough isolation exercises for bodybuilding (found {isolation_count}, need {int(len(all_exercises) * 0.3)})"

        elif "Weight Loss" in goal:
            cardio_count = 0
            for exercise in all_exercises:
                ex_type = exercise.get('exercise_type', '').lower()
                title = exercise.get('title', '').lower()
                if 'cardio' in ex_type or 'hiit' in ex_type or 'hiit' in title or 'cardio' in title:
                    cardio_count += 1

            if cardio_count < len(workout_plan) * 1.5:  # At least 1.5 cardio per day average
                return False, f"Not enough cardio for weight loss (found {cardio_count}, need {int(len(workout_plan) * 1.5)})"

        elif "Mobility" in goal:
            mobility_count = 0
            for exercise in all_exercises:
                ex_type = exercise.get('exercise_type', '').lower()
                title = exercise.get('title', '').lower()
                if 'mobility' in ex_type or 'flexibility' in ex_type or 'stretch' in title:
                    mobility_count += 1

            if mobility_count < len(all_exercises) * 0.4:  # At least 40% mobility exercises
                return False, f"Not enough mobility exercises (found {mobility_count}, need {int(len(all_exercises) * 0.4)})"

        elif "Body Weight" in goal:
            bodyweight_count = 0
            for exercise in all_exercises:
                equipment = exercise.get('equipment', '').lower()
                if 'bodyweight' in equipment or 'no equipment' in equipment:
                    bodyweight_count += 1

            if bodyweight_count < len(all_exercises) * 0.7:  # At least 70% bodyweight exercises
                return False, f"Not enough bodyweight exercises (found {bodyweight_count}, need {int(len(all_exercises) * 0.7)})"

        return True, "Plan validated successfully"

    def _fix_workout_plan(self, workout_plan, goal, experience_level):
        """
        Attempts to fix issues in a workout plan to meet requirements
        """
        fixed_plan = {}
        for day, exercises in workout_plan.items():
            # Ensure enough exercises per day (at least 8)
            if len(exercises) < 8:
                # Add appropriate exercises based on focus
                day_focus = day.lower()
                additional_exercises = self._get_additional_exercises(day_focus, goal, 8 - len(exercises))
                exercises.extend(additional_exercises)

            fixed_plan[day] = exercises

        # Check goal-specific needs
        all_exercises = []
        for exercises in fixed_plan.values():
            all_exercises.extend(exercises)

        # For Body Building: Add isolation exercises if needed
        if "Body Building" in goal:
            isolation_count = sum(1 for e in all_exercises if 'isolation' in e.get('exercise_type', '').lower())
            isolation_needed = int(len(all_exercises) * 0.3) - isolation_count

            if isolation_needed > 0:
                isolation_exercises = self._get_isolation_exercises(isolation_needed)

                # Distribute these across days focusing on appropriate muscle groups
                for day, exercises in fixed_plan.items():
                    day_focus = day.lower()
                    for exercise in isolation_exercises[:]:
                        # Check if exercise matches day focus
                        if self._exercise_matches_focus(exercise, day_focus):
                            exercises.append(exercise)
                            isolation_exercises.remove(exercise)
                            if not isolation_exercises:
                                break

                    if not isolation_exercises:
                        break

                # If any isolation exercises remain, add them anywhere
                for exercise in isolation_exercises:
                    fixed_plan[list(fixed_plan.keys())[0]].append(exercise)

        # For Weight Loss: Add cardio if needed
        elif "Weight Loss" in goal:
            cardio_exercises = []
            for exercises in fixed_plan.values():
                cardio_exercises.extend([e for e in exercises if 'cardio' in e.get('exercise_type', '').lower()])

            cardio_needed = int(len(fixed_plan) * 1.5) - len(cardio_exercises)

            if cardio_needed > 0:
                additional_cardio = self._get_cardio_exercises(cardio_needed)

                # Add cardio to each day that doesn't have enough
                cardio_per_day = {}
                for day, exercises in fixed_plan.items():
                    cardio_per_day[day] = sum(1 for e in exercises if 'cardio' in e.get('exercise_type', '').lower())

                # Sort days by cardio count
                sorted_days = sorted(cardio_per_day.items(), key=lambda x: x[1])

                # Add cardio to days with least cardio first
                for day, count in sorted_days:
                    if additional_cardio:
                        fixed_plan[day].append(additional_cardio.pop(0))
                    else:
                        break

        # For Mobility: Add mobility exercises if needed
        elif "Mobility" in goal:
            mobility_count = sum(1 for e in all_exercises if 'mobility' in e.get('exercise_type', '').lower())
            mobility_needed = int(len(all_exercises) * 0.4) - mobility_count

            if mobility_needed > 0:
                mobility_exercises = self._get_mobility_exercises(mobility_needed)

                # Add to each day proportionally
                for day, exercises in fixed_plan.items():
                    if mobility_exercises:
                        to_add = max(1, min(3, len(mobility_exercises)))
                        exercises.extend(mobility_exercises[:to_add])
                        mobility_exercises = mobility_exercises[to_add:]
                    else:
                        break

        # For Body Weight: Ensure enough bodyweight exercises
        elif "Body Weight" in goal:
            # Count bodyweight exercises
            bodyweight_count = sum(1 for e in all_exercises if 'bodyweight' in e.get('equipment', '').lower())
            bodyweight_needed = int(len(all_exercises) * 0.7) - bodyweight_count

            if bodyweight_needed > 0:
                bodyweight_exercises = self._get_bodyweight_exercises(bodyweight_needed)

                # Replace non-bodyweight exercises with bodyweight alternatives
                for day, exercises in fixed_plan.items():
                    non_bodyweight = [
                        i for i, e in enumerate(exercises) 
                        if 'bodyweight' not in e.get('equipment', '').lower() and bodyweight_exercises
                    ]

                    for idx in non_bodyweight:
                        if bodyweight_exercises:
                            exercises[idx] = bodyweight_exercises.pop(0)
                        else:
                            break

                    if not bodyweight_exercises:
                        break

        return fixed_plan

    def _get_additional_exercises(self, day_focus, goal, count):
        """
        Gets additional exercises based on day focus and goal
        """
        additional = []

        # Default exercises by body part
        defaults = {
            "chest": [
                {"id": -1, "title": "Push-ups", "exercise_type": "Compound", "body_part": "Chest", "equipment": "Bodyweight"},
                {"id": -2, "title": "Incline Push-ups", "exercise_type": "Compound", "body_part": "Chest", "equipment": "Bodyweight"},
                {"id": -3, "title": "Chest Dips", "exercise_type": "Compound", "body_part": "Chest/Triceps", "equipment": "Bodyweight"}
            ],
            "back": [
                {"id": -4, "title": "Pull-ups", "exercise_type": "Compound", "body_part": "Back", "equipment": "Bodyweight"},
                {"id": -5, "title": "Inverted Rows", "exercise_type": "Compound", "body_part": "Back", "equipment": "Bodyweight"},
                {"id": -6, "title": "Superman Hold", "exercise_type": "Isolation", "body_part": "Back", "equipment": "Bodyweight"}
            ],
            "legs": [
                {"id": -7, "title": "Bodyweight Squats", "exercise_type": "Compound", "body_part": "Legs", "equipment": "Bodyweight"},
                {"id": -8, "title": "Lunges", "exercise_type": "Compound", "body_part": "Legs", "equipment": "Bodyweight"},
                {"id": -9, "title": "Glute Bridges", "exercise_type": "Isolation", "body_part": "Glutes", "equipment": "Bodyweight"}
            ],
            "shoulders": [
                {"id": -10, "title": "Pike Push-ups", "exercise_type": "Compound", "body_part": "Shoulders", "equipment": "Bodyweight"},
                {"id": -11, "title": "Handstand Hold", "exercise_type": "Compound", "body_part": "Shoulders", "equipment": "Bodyweight"},
                {"id": -12, "title": "Lateral Raises", "exercise_type": "Isolation", "body_part": "Shoulders", "equipment": "Dumbbells"}
            ],
            "arms": [
                {"id": -13, "title": "Tricep Dips", "exercise_type": "Isolation", "body_part": "Triceps", "equipment": "Bodyweight"},
                {"id": -14, "title": "Chin-ups", "exercise_type": "Compound", "body_part": "Biceps/Back", "equipment": "Bodyweight"},
                {"id": -15, "title": "Diamond Push-ups", "exercise_type": "Compound", "body_part": "Triceps", "equipment": "Bodyweight"}
            ],
            "core": [
                {"id": -16, "title": "Plank", "exercise_type": "Isolation", "body_part": "Core", "equipment": "Bodyweight"},
                {"id": -17, "title": "Russian Twists", "exercise_type": "Isolation", "body_part": "Core", "equipment": "Bodyweight"},
                {"id": -18, "title": "Leg Raises", "exercise_type": "Isolation", "body_part": "Core", "equipment": "Bodyweight"}
            ],
            "cardio": [
                {"id": -19, "title": "Jumping Jacks", "exercise_type": "Cardio", "body_part": "Full Body", "equipment": "Bodyweight"},
                {"id": -20, "title": "Mountain Climbers", "exercise_type": "Cardio", "body_part": "Full Body", "equipment": "Bodyweight"},
                {"id": -21, "title": "Burpees", "exercise_type": "Cardio", "body_part": "Full Body", "equipment": "Bodyweight"}
            ],
            "mobility": [
                {"id": -22, "title": "Hip Flexor Stretch", "exercise_type": "Mobility", "body_part": "Hips", "equipment": "Bodyweight"},
                {"id": -23, "title": "Shoulder Dislocates", "exercise_type": "Mobility", "body_part": "Shoulders", "equipment": "Bodyweight"},
                {"id": -24, "title": "Ankle Mobility", "exercise_type": "Mobility", "body_part": "Ankles", "equipment": "Bodyweight"}
            ],
            "full": [
                {"id": -25, "title": "Burpees", "exercise_type": "Compound", "body_part": "Full Body", "equipment": "Bodyweight"},
                {"id": -26, "title": "Mountain Climbers", "exercise_type": "Cardio", "body_part": "Full Body", "equipment": "Bodyweight"},
                {"id": -27, "title": "Jump Squats", "exercise_type": "Compound", "body_part": "Legs", "equipment": "Bodyweight"}
            ]
        }

        # Add workout-specific exercises based on goal
        if "Body Building" in goal:
            defaults["isolation"] = [
                {"id": -28, "title": "Dumbbell Curls", "exercise_type": "Isolation", "body_part": "Biceps", "equipment": "Dumbbells"},
                {"id": -29, "title": "Lateral Raises", "exercise_type": "Isolation", "body_part": "Shoulders", "equipment": "Dumbbells"},
                {"id": -30, "title": "Tricep Extensions", "exercise_type": "Isolation", "body_part": "Triceps", "equipment": "Dumbbells"}
            ]
        elif "Weight Loss" in goal:
            defaults["hiit"] = [
                {"id": -31, "title": "HIIT Sprint Intervals", "exercise_type": "Cardio", "body_part": "Full Body", "equipment": "Bodyweight"},
                {"id": -32, "title": "Tabata Squats", "exercise_type": "Cardio", "body_part": "Legs", "equipment": "Bodyweight"},
                {"id": -33, "title": "Circuit Training", "exercise_type": "Cardio", "body_part": "Full Body", "equipment": "Bodyweight"}
            ]
        elif "Mobility" in goal:
            defaults["flexibility"] = [
                {"id": -34, "title": "Yoga Flow", "exercise_type": "Mobility", "body_part": "Full Body", "equipment": "Bodyweight"},
                {"id": -35, "title": "Dynamic Stretching", "exercise_type": "Mobility", "body_part": "Full Body", "equipment": "Bodyweight"},
                {"id": -36, "title": "Joint Mobility", "exercise_type": "Mobility", "body_part": "Full Body", "equipment": "Bodyweight"}
            ]

        # Determine which categories to pull from based on day focus
        categories = []
        day_focus = day_focus.lower()

        for category in defaults.keys():
            if category in day_focus:
                categories.append(category)

        # If no matches, use full body or based on goal
        if not categories:
            if "Body Building" in goal:
                categories = ["chest", "back", "legs", "shoulders", "arms"]
            elif "Weight Loss" in goal:
                categories = ["cardio", "hiit", "full"]
            elif "Mobility" in goal:
                categories = ["mobility", "flexibility"]
            else:
                categories = ["full"]

        # Get exercises from each matching category
        exercises_per_category = max(1, count // len(categories))
        remaining = count

        for category in categories:
            category_exercises = defaults.get(category, defaults["full"])
            to_add = min(remaining, exercises_per_category, len(category_exercises))

            # Make copies with unique negative IDs to avoid duplication issues
            next_id = -1000
            for i in range(to_add):
                exercise = category_exercises[i % len(category_exercises)].copy()
                exercise["id"] = next_id
                next_id -= 1
                additional.append(exercise)
                remaining -= 1

            if remaining <= 0:
                break

        # If we still need more, add from any category
        if remaining > 0:
            all_exercises = []
            for exercises in defaults.values():
                all_exercises.extend(exercises)

            # Add random selections
            for i in range(remaining):
                exercise = random.choice(all_exercises).copy()
                exercise["id"] = -2000 - i
                additional.append(exercise)

        return additional

    def _get_isolation_exercises(self, count):
        """Returns isolation exercises for bodybuilding focus"""
        isolations = [
            {"id": -1001, "title": "Bicep Curls", "exercise_type": "Isolation", "body_part": "Biceps", "equipment": "Dumbbells"},
            {"id": -1002, "title": "Tricep Extensions", "exercise_type": "Isolation", "body_part": "Triceps", "equipment": "Dumbbells"},
            {"id": -1003, "title": "Lateral Raises", "exercise_type": "Isolation", "body_part": "Shoulders", "equipment": "Dumbbells"},
            {"id": -1004, "title": "Chest Flyes", "exercise_type": "Isolation", "body_part": "Chest", "equipment": "Dumbbells"},
            {"id": -1005, "title": "Leg Extensions", "exercise_type": "Isolation", "body_part": "Quads", "equipment": "Machine"},
            {"id": -1006, "title": "Leg Curls", "exercise_type": "Isolation", "body_part": "Hamstrings", "equipment": "Machine"},
            {"id": -1007, "title": "Calf Raises", "exercise_type": "Isolation", "body_part": "Calves", "equipment": "Bodyweight"},
            {"id": -1008, "title": "Face Pulls", "exercise_type": "Isolation", "body_part": "Rear Delts", "equipment": "Cable"},
            {"id": -1009, "title": "Concentration Curls", "exercise_type": "Isolation", "body_part": "Biceps", "equipment": "Dumbbells"},
            {"id": -1010, "title": "Tricep Kickbacks", "exercise_type": "Isolation", "body_part": "Triceps", "equipment": "Dumbbells"}
        ]
        return random.sample(isolations, min(count, len(isolations)))

    def _get_cardio_exercises(self, count):
        """Returns cardio exercises for weight loss focus"""
        cardio = [
            {"id": -2001, "title": "HIIT Sprint Intervals", "exercise_type": "Cardio", "body_part": "Full Body", "equipment": "Bodyweight"},
            {"id": -2002, "title": "Jump Rope", "exercise_type": "Cardio", "body_part": "Full Body", "equipment": "Jump Rope"},
            {"id": -2003, "title": "Burpees", "exercise_type": "Cardio", "body_part": "Full Body", "equipment": "Bodyweight"},
            {"id": -2004, "title": "Mountain Climbers", "exercise_type": "Cardio", "body_part": "Full Body", "equipment": "Bodyweight"},
            {"id": -2005, "title": "Jumping Jacks", "exercise_type": "Cardio", "body_part": "Full Body", "equipment": "Bodyweight"},
            {"id": -2006, "title": "Box Jumps", "exercise_type": "Cardio", "body_part": "Legs", "equipment": "Box"},
            {"id": -2007, "title": "Battle Ropes", "exercise_type": "Cardio", "body_part": "Arms/Shoulders", "equipment": "Battle Ropes"},
            {"id": -2008, "title": "Rowing Machine", "exercise_type": "Cardio", "body_part": "Full Body", "equipment": "Machine"},
            {"id": -2009, "title": "Stair Climber", "exercise_type": "Cardio", "body_part": "Legs", "equipment": "Machine"},
            {"id": -2010, "title": "Cycling Intervals", "exercise_type": "Cardio", "body_part": "Legs", "equipment": "Bike"}
        ]
        return random.sample(cardio, min(count, len(cardio)))

    def _get_mobility_exercises(self, count):
        """Returns mobility exercises for mobility focus"""
        mobility = [
            {"id": -3001, "title": "Hip Flexor Stretch", "exercise_type": "Mobility", "body_part": "Hips", "equipment": "Bodyweight"},
            {"id": -3002, "title": "Shoulder Dislocates", "exercise_type": "Mobility", "body_part": "Shoulders", "equipment": "Resistance Band"},
            {"id": -3003, "title": "Ankle Mobility Drill", "exercise_type": "Mobility", "body_part": "Ankles", "equipment": "Bodyweight"},
            {"id": -3004, "title": "Thoracic Bridge", "exercise_type": "Mobility", "body_part": "Spine", "equipment": "Bodyweight"},
            {"id": -3005, "title": "Cat-Cow Stretch", "exercise_type": "Mobility", "body_part": "Spine", "equipment": "Bodyweight"},
            {"id": -3006, "title": "Jefferson Curl", "exercise_type": "Mobility", "body_part": "Hamstrings/Back", "equipment": "Bodyweight"},
            {"id": -3007, "title": "Wrist Mobility", "exercise_type": "Mobility", "body_part": "Wrists", "equipment": "Bodyweight"},
            {"id": -3008, "title": "Squat Mobility", "exercise_type": "Mobility", "body_part": "Hips/Ankles", "equipment": "Bodyweight"},
            {"id": -3009, "title": "Hip 90/90 Stretch", "exercise_type": "Mobility", "body_part": "Hips", "equipment": "Bodyweight"},
            {"id": -3010, "title": "Deep Lunge Stretch", "exercise_type": "Mobility", "body_part": "Hip Flexors", "equipment": "Bodyweight"}
        ]
        return random.sample(mobility, min(count, len(mobility)))

    def _get_bodyweight_exercises(self, count):
        """Returns bodyweight exercises for calisthenics focus"""
        bodyweight = [
            {"id": -4001, "title": "Push-ups", "exercise_type": "Compound", "body_part": "Chest/Triceps", "equipment": "Bodyweight"},
            {"id": -4002, "title": "Pull-ups", "exercise_type": "Compound", "body_part": "Back/Biceps", "equipment": "Bodyweight"},
            {"id": -4003, "title": "Bodyweight Squats", "exercise_type": "Compound", "body_part": "Legs", "equipment": "Bodyweight"},
            {"id": -4004, "title": "Dips", "exercise_type": "Compound", "body_part": "Chest/Triceps", "equipment": "Bodyweight"},
            {"id": -4005, "title": "Inverted Rows", "exercise_type": "Compound", "body_part": "Back", "equipment": "Bodyweight"},
            {"id": -4006, "title": "Pike Push-ups", "exercise_type": "Compound", "body_part": "Shoulders", "equipment": "Bodyweight"},
            {"id": -4007, "title": "Pistol Squats", "exercise_type": "Compound", "body_part": "Legs", "equipment": "Bodyweight"},
            {"id": -4008, "title": "L-Sit Hold", "exercise_type": "Isolation", "body_part": "Core", "equipment": "Bodyweight"},
            {"id": -4009, "title": "Plank", "exercise_type": "Isolation", "body_part": "Core", "equipment": "Bodyweight"},
            {"id": -4010, "title": "Hollow Body Hold", "exercise_type": "Isolation", "body_part": "Core", "equipment": "Bodyweight"}
        ]
        return random.sample(bodyweight, min(count, len(bodyweight)))

    def _exercise_matches_focus(self, exercise, day_focus):
        """Checks if an exercise matches the day's focus"""
        body_part = exercise.get('body_part', '').lower()

        # Check if any part of the body part is in the day focus
        for part in body_part.split('/'):
            if part.strip() in day_focus:
                return True

        return False

    def _add_workouts_to_database(self, plan_id, workout_plan, duration_weeks, goal, experience_level):
        """
        Adds workouts to the database for every week in the plan
        """
        for day_number, day_key in enumerate(sorted(workout_plan.keys()), 1):
            for week in range(1, duration_weeks + 1):
                exercises = workout_plan[day_key]
                for exercise in exercises:
                    # Skip exercises with negative IDs (placeholders)
                    exercise_id = exercise.get('id')
                    if exercise_id is None or exercise_id < 0:
                        continue

                    # Generate appropriate sets, reps based on experience and goal
                    target_sets, target_reps = self._calculate_sets_reps(exercise, experience_level, goal)

                    # Add workout to plan
                    self.db.add_plan_workout(
                        plan_id=plan_id,
                        exercise_id=exercise_id,
                        week=week,
                        day=day_number,
                        target_sets=target_sets,
                        target_reps=target_reps,
                        description=f"{day_key} - {exercise.get('body_part', 'General')} Focus"
                    )

    def _add_basic_exercises(self, plan_id, workouts_per_week, duration_weeks, goal, experience_level):
        """
        Fallback method to add basic exercises when the advanced plan creation fails
        """
        basic_exercises = {
            "Upper Body": [
                {"name": "Push-ups", "type": "Compound", "body_part": "Chest"},
                {"name": "Pull-ups", "type": "Compound", "body_part": "Back"},
                {"name": "Dips", "type": "Compound", "body_part": "Chest/Triceps"},
                {"name": "Overhead Press", "type": "Compound", "body_part": "Shoulders"}
            ],
            "Lower Body": [
                {"name": "Squats", "type": "Compound", "body_part": "Legs"},
                {"name": "Lunges", "type": "Compound", "body_part": "Legs"},
                {"name": "Glute Bridges", "type": "Isolation", "body_part": "Glutes"},
                {"name": "Calf Raises", "type": "Isolation", "body_part": "Calves"}
            ],
            "Core": [
                {"name": "Plank", "type": "Isolation", "body_part": "Core"},
                {"name": "Crunches", "type": "Isolation", "body_part": "Core"},
                {"name": "Russian Twists", "type": "Isolation", "body_part": "Core"},
                {"name": "Leg Raises", "type": "Isolation", "body_part": "Core"}
            ],
            "Cardio": [
                {"name": "Jumping Jacks", "type": "Cardio", "body_part": "Full Body"},
                {"name": "Mountain Climbers", "type": "Cardio", "body_part": "Full Body"},
                {"name": "Burpees", "type": "Cardio", "body_part": "Full Body"},
                {"name": "High Knees", "type": "Cardio", "body_part": "Full Body"}
            ]
        }

        # Create a basic plan with alternating focus
        focus_rotation = ["Upper Body", "Lower Body", "Core", "Upper Body", "Lower Body", "Cardio", "Rest"]

        for week in range(1, duration_weeks + 1):
            for day in range(1, workouts_per_week + 1):
                focus = focus_rotation[(day - 1) % len(focus_rotation)]
                if focus == "Rest":
                    continue

                exercises = basic_exercises[focus]
                for exercise in exercises:
                    # Find exercises in the database that match these criteria
                    try:
                        self.db.cursor.execute(
                            """
                            SELECT id FROM exercises 
                            WHERE title LIKE ? AND body_part LIKE ?
                            LIMIT 1
                            """,
                            (f"%{exercise['name']}%", f"%{exercise['body_part']}%")
                        )
                        result = self.db.cursor.fetchone()

                        if result:
                            exercise_id = result['id']
                            # Get default sets/reps based on experience
                            if experience_level == "Beginner":
                                sets, reps = 3, 10
                            elif experience_level == "Intermediate":
                                sets, reps = 4, 8
                            else:
                                sets, reps = 5, 6

                            self.db.add_plan_workout(
                                plan_id=plan_id,
                                exercise_id=exercise_id,
                                week=week,
                                day=day,
                                target_sets=sets,
                                target_reps=reps,
                                description=f"Day {day} - {focus}"
                            )
                    except Exception as e:
                        print(f"Error adding basic exercise: {str(e)}")
                        continue

    def _calculate_sets_reps(self, exercise, experience_level, goal):
        """Calculate target sets and reps based on exercise type, experience and goal"""
        exercise_type = exercise.get('exercise_type', '').lower()

        # Default values
        sets = 3
        reps = 10

        # Adjust based on experience level
        if experience_level == "Beginner":
            sets = 3
        elif experience_level == "Intermediate":
            sets = 4
        else:  # Advanced
            sets = 5

        # Adjust based on exercise type
        if 'compound' in exercise_type:
            if "Sports" in goal or "Athletic" in goal:
                reps = 6  # Lower reps for strength focus
            elif "Body Building" in goal:
                reps = 8  # Moderate reps for hypertrophy
            else:
                reps = 10  # Higher reps for general fitness
        elif 'isolation' in exercise_type:
            if "Body Building" in goal:
                reps = 12  # Higher reps for hypertrophy with isolation
            else:
                reps = 15  # Higher reps for general fitness
        elif 'cardio' in exercise_type:
            sets = 3
            reps = 20  # Higher reps for cardio/endurance
        elif 'mobility' in exercise_type:
            sets = 2
            reps = 10  # For mobility, reps are often holds or slower movements

        # For weight loss, higher reps across the board
        if "Weight Loss" in goal and 'cardio' not in exercise_type:
            reps += 5

        # For bodyweight fitness, adjust based on movement difficulty
        if "Body Weight" in goal:
            equipment = exercise.get('equipment', '').lower()
            if 'bodyweight' in equipment:
                # More advanced bodyweight movements get lower rep ranges
                if 'advanced' in exercise.get('level', '').lower():
                    reps = max(5, reps - 5)

        return sets, reps
