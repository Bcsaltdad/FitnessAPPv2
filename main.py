import streamlit as st
import pandas as pd
import json
import hashlib
from exercise_utils import ExerciseDatabase
from datetime import datetime
from workout_planner import WorkoutPlanner
from Engine import WorkoutRecommender, WorkoutEngine

# Initialize session state for user management
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
# Initialize developer mode
if 'dev_mode' not in st.session_state:
    st.session_state.dev_mode = False

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    hashed_pwd = hash_password(password)
    db.cursor.execute('SELECT id FROM users WHERE username = ? AND password = ?', (username, hashed_pwd))
    result = db.cursor.fetchone()
    return result[0] if result else None

def create_user(username, password):
    hashed_pwd = hash_password(password)
    try:
        db.cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_pwd))
        db.conn.commit()
        return db.cursor.lastrowid
    except:
        return None

# Initialize exercise database
db = ExerciseDatabase('fitness.db')

# Initialize users table if not exists
db.cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     username TEXT UNIQUE,
                     password TEXT)''')
db.conn.commit()

st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

# Login/Register UI
if not st.session_state.user_id:
    st.title("Welcome to Fitness Tracker")
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                user_id = authenticate_user(username, password)
                if user_id:
                    st.session_state.user_id = user_id
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            if st.form_submit_button("Register"):
                if create_user(new_username, new_password):
                    st.success("Registration successful! Please login.")
                else:
                    st.error("Username already exists")
    st.stop()

# Initialize session state for navigation
if 'view' not in st.session_state:
    st.session_state.view = 'plans'
if 'selected_plan' not in st.session_state:
    st.session_state.selected_plan = None
if 'selected_week' not in st.session_state:
    st.session_state.selected_week = None
if 'selected_day' not in st.session_state:
    st.session_state.selected_day = None

# Developer mode toggle in sidebar
with st.sidebar:
    # Hidden developer activation area
    with st.expander("Settings", expanded=False):
        # Use a "secret" key combination
        dev_key = st.text_input("Developer Key", type="password")
        if dev_key == "fitnessdev2025":  # You can change this to any secret key
            st.session_state.dev_mode = True
            st.success("Developer mode activated")
        elif dev_key and dev_key != "":
            st.session_state.dev_mode = False
            st.error("Invalid developer key")

    # Only show developer tools if dev_mode is True
    if st.session_state.dev_mode:
        st.sidebar.markdown("## Developer Tools")
        if st.sidebar.button("Test Recommendation Engine"):
            recommender = WorkoutRecommender(db)
            test_user_id = st.session_state.user_id  # Use current user instead of hardcoded ID
            recommendation = recommender.get_daily_recommendation(test_user_id)

            st.write("### Recommendation Test Results")
            st.json(recommendation)

            if recommendation.get('workouts'):
                st.write("### Suggested Workouts")
                for workout in recommendation['workouts']:
                    st.write(f"- {workout['title']}: {workout.get('sets', 'N/A')} sets × {workout.get('reps', 'N/A')} reps")

            if recommendation.get('adjustments'):
                st.write("### Suggested Adjustments")
                for adjustment in recommendation['adjustments']:
                    st.write(f"- {adjustment}")

            if recommendation.get('muscle_recovery'):
                st.write("### Muscle Recovery Status")
                for muscle, status in recommendation['muscle_recovery'].items():
                    st.write(f"- {muscle}: {status}")

        # Add more developer tools here as needed
        if st.sidebar.button("Reset User Data"):
            st.write("This would reset the current user's data")
            # Implement actual reset functionality

        if st.sidebar.button("Database Stats"):
            # Display some database statistics
            user_count = db.cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            plan_count = db.cursor.execute("SELECT COUNT(*) FROM fitness_plans").fetchone()[0]
            workout_count = db.cursor.execute("SELECT COUNT(*) FROM workout_logs").fetchone()[0]

            st.write("### Database Statistics")
            st.write(f"Total Users: {user_count}")
            st.write(f"Total Plans: {plan_count}")
            st.write(f"Total Logged Workouts: {workout_count}")

def show_workout_log(workout):
    st.subheader(workout['title'])
    st.write(f"**Description:** {workout['description']}")
    st.write("**Instructions:**")
    if workout.get('instructions'):
        instructions = workout['instructions'].split(',')
        for i, instruction in enumerate(instructions, 1):
            st.write(f"{i}. {instruction.strip()}")

    st.write(
        f"**Target:** {workout['target_sets']} sets × {workout['target_reps']} reps"
    )

    with st.form(f"log_form_{workout['id']}"):
        sets = st.number_input("Sets Completed", 1, 10, workout['target_sets'])
        reps = st.number_input("Reps Completed", 1, 30, workout['target_reps'])
        weight_lbs = st.number_input("Weight (lbs)",
                                     0.0,
                                     1000.0,
                                     0.0,
                                     step=5.0)

        if st.form_submit_button("Save"):
            weight_kg = weight_lbs / 2.20462
            db.log_workout(workout['id'], sets, reps, weight_kg)
            st.success("Workout logged!")
            st.session_state.view = 'day_summary'


# Navigation functions
def go_to_plans():
    st.session_state.view = 'plans'
    st.session_state.selected_plan = None
    st.session_state.selected_week = None
    st.session_state.selected_day = None


def go_to_week_view(plan_id, week):
    st.session_state.view = 'week_summary'
    st.session_state.selected_plan = plan_id
    st.session_state.selected_week = week


def go_to_day_view(plan_id, week, day):
    st.session_state.view = 'day_summary'
    st.session_state.selected_plan = plan_id
    st.session_state.selected_week = week
    st.session_state.selected_day = day

# Main UI
tabs = st.tabs(["My Plans", "Exercise Library", "Create New Plan"])
with tabs[0]:
    if st.session_state.view == 'plans':
        col1, col2 = st.columns([8, 2])
        with col1:
            st.header("My Active Plans")
        with col2:
            if st.button("Logout"):
                st.session_state.user_id = None
                st.session_state.username = None
                st.rerun()
        active_plans = db.get_active_plans(st.session_state.user_id)
        if not active_plans:
            st.info("No active plans found. Create a new plan to get started!")
        for plan in active_plans:
            col1, col2, col3, col4 = st.columns([3, 1, 0.5, 0.5])
            with col1:
                st.subheader(f"📋 {plan['name']}")
            with col2:
                if f"edit_goal_{plan['id']}" not in st.session_state:
                    st.session_state[f"edit_goal_{plan['id']}"] = False
                if st.session_state[f"edit_goal_{plan['id']}"]:
                    new_goal = st.text_input("New Goal",
                                             value=plan['goal'],
                                             key=f"goal_input_{plan['id']}")
                    if st.button("Save", key=f"save_goal_{plan['id']}"):
                        db.update_plan_goal(plan['id'], new_goal)
                        st.session_state[f"edit_goal_{plan['id']}"] = False
                        st.rerun()
                else:
                    st.write(f"Goal: {plan['goal']}")
            with col3:
                if st.button("✏️", key=f"edit_btn_{plan['id']}"):
                    st.session_state[f"edit_goal_{plan['id']}"] = True
            with col4:
                if st.button("❌", key=f"delete_btn_{plan['id']}"):
                    db.make_plan_inactive(plan['id'])  # This function needs to be implemented in your database logic
                    st.success(f"{plan['name']} has been made inactive.")
                    st.rerun()  # Refresh the state to reflect changes
            summary = db.get_plan_summary(plan['id'])
            if summary:
                cols = st.columns(4)
                with cols[0]:
                    st.metric("Total Weeks", plan['duration_weeks'])
                with cols[1]:
                    completed_workouts = sum(week['exercises_completed'] or 0
                                             for week in summary)
                    st.metric("Completed Workouts", completed_workouts)
                with cols[2]:
                    avg_weight = sum(
                        week['avg_weight'] or 0
                        for week in summary) / len(summary) if summary else 0
                    st.metric("Avg Weight (lbs)",
                              f"{(avg_weight * 2.20462):.1f}")
                with cols[3]:
                    days_worked = sum(week['days_worked'] or 0
                                      for week in summary)
                    st.metric("Days Worked", days_worked)


            # Show weeks as clickable buttons
            st.write("### Weekly Schedule")
            week_cols = st.columns(4)
            for week in range(1, plan['duration_weeks'] + 1):
                with week_cols[(week - 1) % 4]:
                    if st.button(f"Week {week}",
                                 key=f"week_{plan['id']}_{week}"):
                        go_to_week_view(plan['id'], week)

    elif st.session_state.view == 'week_summary':
        plan = db.get_active_plans(st.session_state.user_id)[0]  # Get the selected plan
        st.button("← Back to Plans", on_click=go_to_plans)
        st.header(f"Week {st.session_state.selected_week} Schedule")

        days = {
            1: "Monday",
            2: "Tuesday",
            3: "Wednesday",
            4: "Thursday",
            5: "Friday",
            6: "Saturday",
            7: "Sunday"
        }

        for day_num, day_name in days.items():
            workouts = db.get_plan_workouts(st.session_state.selected_plan,
                                            st.session_state.selected_week,
                                            day_num)
            if workouts:
                if st.button(f"{day_name} ({len(workouts)} workouts)",
                             key=f"day_{day_num}"):
                    go_to_day_view(st.session_state.selected_plan,
                                   st.session_state.selected_week, day_num)

    elif st.session_state.view == 'day_summary':
        st.button(
            "← Back to Week",
            on_click=lambda: go_to_week_view(st.session_state.selected_plan, st
                                             .session_state.selected_week))

        day_names = {
            1: "Monday",
            2: "Tuesday",
            3: "Wednesday",
            4: "Thursday",
            5: "Friday",
            6: "Saturday",
            7: "Sunday"
        }

        st.header(
            f"Week {st.session_state.selected_week} - {day_names[st.session_state.selected_day]}"
        )

        workouts = db.get_plan_workouts(st.session_state.selected_plan,
                                        st.session_state.selected_week,
                                        st.session_state.selected_day)

        for workout in workouts:
            with st.expander(workout['title']):
                show_workout_log(workout)

with tabs[1]:  # Exercise Library
    st.header("Exercise Library")
    goal = st.selectbox("Filter by Goal",
                        ["Strength", "Cardio", "Flexibility"])
    exercises = db.get_exercises_by_goal(goal)

    for exercise in exercises:
        with st.expander(f"📋 {exercise['title']}", expanded=False):
            st.write(f"**Description:** {exercise['description']}")
            st.write(f"**Equipment:** {exercise['equipment']}")
            st.write(f"**Level:** {exercise['level']}")
            if exercise.get('instructions'):
                st.write("**Instructions:**")
                instructions = exercise['instructions'].split(',')
                for i, instruction in enumerate(instructions, 1):
                    st.write(f"{i}. {instruction.strip()}")

with tabs[2]:  # Create New Plan
    st.header("Create Your Personalized Fitness Plan")

    # Two columns for form organization
    col1, col2 = st.columns(2)

    with col1:
        plan_name = st.text_input("Plan Name")
        plan_goal = st.selectbox("What's your primary fitness goal?", [
            "Sports and Athletics", "Body Building", "Body Weight Fitness",
            "Weight Loss", "Mobility Exclusive"
        ])
        experience_level = st.selectbox(
            "Your fitness experience level",
            ["Beginner", "Intermediate", "Advanced"])
        duration = st.number_input("Program duration (weeks)",
                                   min_value=4,
                                   value=8,
                                   max_value=52)

    with col2:
        workouts_per_week = st.selectbox(
            "How many workouts can you commit to per week?",
            options=list(range(1, 8)),
            index=2)
        equipment_access = st.multiselect(
            "What equipment do you have access to?", [
                "Full Gym", "Dumbbells", "Resistance Bands", "Pull-up Bar",
                "No Equipment"
            ],
            default=["Full Gym"])
        limitations = st.multiselect(
            "Do you have any physical limitations or areas to avoid?",
            ["None", "Lower Back", "Knees", "Shoulders", "Neck"],
            default=["None"])

    # More detailed options in an expander
    with st.expander("Advanced Options"):
        preferred_cardio = st.multiselect("Preferred cardio types", [
            "Running", "Cycling", "Swimming", "Rowing", "Jump Rope", "HIIT",
            "None"
        ],
                                          default=["HIIT"])

        specific_focus = st.multiselect(
            "Any specific areas you want to focus on?", [
                "Core Strength", "Upper Body", "Lower Body", "Explosiveness",
                "Endurance", "Balance", "None"
            ],
            default=["None"])

        time_per_workout = st.slider("Time available per workout (minutes)",
                                     min_value=15,
                                     max_value=120,
                                     value=45,
                                     step=5)

    if st.button("Create Personalized Plan"):
        with st.spinner("Creating your personalized workout plan..."):
            # Create plan details dictionary
            plan_details = {
                "workouts_per_week": workouts_per_week,
                "equipment_access": equipment_access,
                "limitations": limitations,
                "preferred_cardio": preferred_cardio,
                "specific_focus": specific_focus,
                "time_per_workout": time_per_workout,
                "experience_level": experience_level
            }

            # Initialize workout planner and recommendation engine
            planner = WorkoutPlanner(db.conn)
            recommender = WorkoutRecommender(db)
            engine = WorkoutEngine(db)

            # Create distribution of days based on workouts_per_week
            # For better workout scheduling based on muscle groups
            focus_distribution = {}

            if workouts_per_week <= 3:
                # Full body approach for fewer workouts
                focus_map = {
                    1: {"Day 1": "Full Body"},
                    2: {"Day 1": "Upper Body", "Day 2": "Lower Body"},
                    3: {"Day 1": "Push/Chest/Shoulders", "Day 2": "Pull/Back/Arms", "Day 3": "Legs/Core"}
                }
                focus_distribution = focus_map.get(workouts_per_week, {})
            elif workouts_per_week <= 5:
                # Push/Pull/Legs split with additional focus days
                focus_distribution = {
                    "Day 1": "Push/Chest/Shoulders",
                    "Day 2": "Pull/Back/Arms",
                    "Day 3": "Legs/Glutes",
                    "Day 4": "Core/Shoulders",
                    "Day 5": "Arms/Mobility"
                }
            else:
                # More advanced 6-day split
                focus_distribution = {
                    "Day 1": "Chest/Triceps",
                    "Day 2": "Back/Biceps",
                    "Day 3": "Legs/Core",
                    "Day 4": "Shoulders/Arms",
                    "Day 5": "Full Body Functional",
                    "Day 6": "Cardio/Mobility",
                    "Day 7": "Recovery/Light Mobility"
                }

            # Modify focus based on specific_focus selection
            if "Upper Body" in specific_focus and "Lower Body" not in specific_focus:
                # Increase upper body focus
                for day in range(1, min(4, workouts_per_week + 1)):
                    if f"Day {day}" in focus_distribution and "Legs" in focus_distribution[f"Day {day}"]:
                        focus_distribution[f"Day {day}"] = focus_distribution[f"Day {day}"].replace("Legs", "Upper")
            elif "Lower Body" in specific_focus and "Upper Body" not in specific_focus:
                # Increase lower body focus
                lower_days = 0
                for day in range(1, workouts_per_week + 1):
                    if f"Day {day}" in focus_distribution and "Legs" in focus_distribution[f"Day {day}"]:
                        lower_days += 1

                if lower_days < workouts_per_week // 2:
                    # Add an extra leg day
                    for day in range(1, workouts_per_week + 1):
                        if f"Day {day}" in focus_distribution and "Arms" in focus_distribution[f"Day {day}"]:
                            focus_distribution[f"Day {day}"] = "Legs/Glutes"
                            break

            # Modify workout focus based on goal
            if "Sports and Athletics" in plan_goal:
                # Add more functional/compound movements
                for day in range(1, workouts_per_week + 1):
                    if f"Day {day}" in focus_distribution:
                        focus_distribution[f"Day {day}"] += "/Functional"

                # Ensure at least one cardio day
                cardio_added = False
                for day in range(1, workouts_per_week + 1):
                    if f"Day {day}" in focus_distribution and "Cardio" in focus_distribution[f"Day {day}"]:
                        cardio_added = True
                        break

                if not cardio_added and workouts_per_week >= 3:
                    focus_distribution[f"Day {workouts_per_week}"] = "Cardio/Agility"

            elif "Weight Loss" in plan_goal:
                # Add HIIT and cardio components to more days
                for day in range(1, workouts_per_week + 1):
                    if f"Day {day}" in focus_distribution:
                        if "Cardio" not in focus_distribution[f"Day {day}"]:
                            focus_distribution[f"Day {day}"] += "/HIIT"

            # Validate equipment access
            has_full_equipment = "Full Gym" in equipment_access
            if not has_full_equipment:
                # Check what equipment is available and modify focus
                available_equipment = []
                if "Dumbbells" in equipment_access:
                    available_equipment.append("dumbbell")
                if "Resistance Bands" in equipment_access:
                    available_equipment.append("band")
                if "Pull-up Bar" in equipment_access:
                    available_equipment.append("bodyweight")

                # If very limited equipment, add bodyweight
                if not available_equipment or ("No Equipment" in equipment_access):
                    available_equipment.append("bodyweight")

                # Update plan details
                plan_details["limited_equipment"] = True
                plan_details["available_equipment"] = available_equipment

            # Create the actual workout plan
            try:
                workout_plan = planner.create_workout_plan(
                    days=workouts_per_week,
                    focus=focus_distribution,
                    equipment=equipment_access,
                    limitations=limitations,
                    experience_level=experience_level,
                    goal=plan_goal
                )

                # Validate the workout plan to ensure it meets criteria
                # For example, ensure proper muscle group distribution
                is_valid, validation_message = validate_workout_plan(workout_plan, plan_goal, experience_level)

                if not is_valid:
                    st.warning(f"Warning: {validation_message}. Attempting to fix...")
                    # Try to fix the issues
                    workout_plan = fix_workout_plan(workout_plan, plan_goal, experience_level)

                # Create plan in database
                plan_id = db.create_fitness_plan(
                    name=plan_name,
                    goal=plan_goal,
                    duration_weeks=duration,
                    plan_details=json.dumps(plan_details),
                    user_id=st.session_state.user_id
                )

                # Once we have the plan ID, add workouts to the database
                for day_number, day_key in enumerate(sorted(workout_plan.keys()), 1):
                    for week in range(1, duration + 1):
                        exercises = workout_plan[day_key]
                        for exercise in exercises:
                            # Generate appropriate sets, reps based on experience and goal
                            target_sets, target_reps = calculate_sets_reps(exercise, experience_level, plan_goal)

                            db.add_plan_workout(
                                plan_id=plan_id,
                                exercise_id=exercise.get('id'),
                                week=week,
                                day=day_number,
                                target_sets=target_sets,
                                target_reps=target_reps,
                                description=f"{day_key} - {exercise.get('body_part', 'General')} Focus"
                            )

                st.success("Your personalized plan has been created!")

                # Preview first week
                st.write("### Preview of Week 1")
                workouts = db.get_plan_workouts(plan_id, 1, None)

                # Group by day
                days = {}
                for workout in workouts:
                    day_num = workout['day']
                    if day_num not in days:
                        days[day_num] = []
                    days[day_num].append(workout)

                # Show each day's workouts
                day_names = {
                    1: "Monday",
                    2: "Tuesday",
                    3: "Wednesday",
                    4: "Thursday",
                    5: "Friday",
                    6: "Saturday",
                    7: "Sunday"
                }

                for day_num in sorted(days.keys()):
                    with st.expander(
                            f"{day_names[day_num]} - {days[day_num][0]['description'].split('-')[0].strip()}"
                    ):
                        for workout in days[day_num]:
                            st.write(
                                f"**{workout['title']}**: {workout['target_sets']} sets × {workout['target_reps']} reps"
                            )

                # Get recommendations for the first workout
                first_day_rec = recommender.get_daily_recommendation(st.session_state.user_id, plan_id)

                if first_day_rec and 'workouts' in first_day_rec:
                    with st.expander("Workout Recommendations"):
                        st.write("### Recommended Approach")
                        if 'message' in first_day_rec:
                            st.write(first_day_rec['message'])

                        for idx, workout in enumerate(first_day_rec['workouts'][:3]):
                            st.write(f"**{idx+1}. {workout.get('title', 'Exercise')}**: {workout.get('target_sets', 3)} sets × {workout.get('target_reps', 10)} reps")

                        if 'adjustments' in first_day_rec and first_day_rec['adjustments']:
                            st.write("**Suggestions:**")
                            for adj in first_day_rec['adjustments']:
                                st.write(f"- {adj}")

                st.session_state.view = 'plans'
                st.rerun()

            except Exception as e:
                st.error(f"Error creating workout plan: {str(e)}")
                # Fallback to basic plan creation
                plan_id = db.create_fitness_plan(
                    name=plan_name,
                    goal=plan_goal,
                    duration_weeks=duration,
                    plan_details=json.dumps(plan_details),
                    user_id=st.session_state.user_id
                )
                st.success("Basic plan created. Some advanced features couldn't be applied.")
                st.session_state.view = 'plans'
                st.rerun()


# Helper functions for workout plan validation and creation
def validate_workout_plan(workout_plan, goal, experience_level):
    """Validates a workout plan meets criteria based on goal and experience"""
    # Check if enough exercises per day
    for day, exercises in workout_plan.items():
        if len(exercises) < 5:
            return False, f"Not enough exercises for {day}"

    # Check muscle group balance across the week
    all_exercises = []
    for day, exercises in workout_plan.items():
        all_exercises.extend(exercises)

    muscle_counts = {}
    for exercise in all_exercises:
        body_part = exercise.get('body_part', '').lower()
        if body_part:
            muscle_counts[body_part] = muscle_counts.get(body_part, 0) + 1

    # Ensure balanced approach 
    min_threshold = 2  # Minimum exercises per major muscle group
    major_muscles = ['chest', 'back', 'legs', 'shoulders', 'arms']

    for muscle in major_muscles:
        if muscle_counts.get(muscle, 0) < min_threshold:
            return False, f"Not enough {muscle} exercises in the plan"

    # For bodybuilding goals, ensure higher volume for hypertrophy
    if "Body Building" in goal:
        exercise_types = [e.get('exercise_type', '').lower() for e in all_exercises]
        isolation_count = exercise_types.count('isolation')

        if isolation_count < len(all_exercises) * 0.3:  # At least 30% isolation exercises
            return False, "Not enough isolation exercises for bodybuilding goal"

    # For weight loss, ensure enough cardio
    if "Weight Loss" in goal:
        cardio_count = 0
        for exercise in all_exercises:
            if 'cardio' in exercise.get('exercise_type', '').lower() or 'hiit' in exercise.get('title', '').lower():
                cardio_count += 1

        if cardio_count < len(workout_plan):  # At least one cardio per day
            return False, "Not enough cardio exercises for weight loss goal"

    return True, "Plan validated successfully"


# Continued from previous artifact
def fix_workout_plan(workout_plan, goal, experience_level):
    """Attempts to fix issues with a workout plan"""
    # This is a simplified version - in production you'd have more complex logic
    fixed_plan = workout_plan.copy()

    # Add placeholder exercises for missing muscle groups if needed
    muscle_exercises = {
        'chest': {'title': 'Push-up Variations', 'body_part': 'Chest', 'exercise_type': 'Compound'},
        'back': {'title': 'Bodyweight Row', 'body_part': 'Back', 'exercise_type': 'Compound'},
        'legs': {'title': 'Bodyweight Squat', 'body_part': 'Legs', 'exercise_type': 'Compound'},
        'shoulders': {'title': 'Pike Push-up', 'body_part': 'Shoulders', 'exercise_type': 'Compound'},
        'arms': {'title': 'Tricep Dips', 'body_part': 'Arms', 'exercise_type': 'Isolation'},
        'cardio': {'title': 'HIIT Intervals', 'body_part': 'Full Body', 'exercise_type': 'Cardio'}
    }

    # If "Body Building" goal, ensure enough isolation exercises
    if "Body Building" in goal:
        for day, exercises in fixed_plan.items():
            isolation_count = len([e for e in exercises if e.get('exercise_type') == 'Isolation'])
            if isolation_count < 3:  # Aim for at least 3 isolation exercises
                # Add some isolation exercises
                day_focus = day.split(' - ')[-1].lower() if ' - ' in day else ''

                if 'chest' in day_focus:
                    exercises.append({'title': 'Chest Flyes', 'body_part': 'Chest', 'exercise_type': 'Isolation'})
                elif 'back' in day_focus:
                    exercises.append({'title': 'Straight Arm Pulldown', 'body_part': 'Back', 'exercise_type': 'Isolation'})
                elif 'legs' in day_focus:
                    exercises.append({'title': 'Leg Extension', 'body_part': 'Legs', 'exercise_type': 'Isolation'})
                else:
                    exercises.append({'title': 'Lateral Raises', 'body_part': 'Shoulders', 'exercise_type': 'Isolation'})

    # If "Weight Loss" goal, ensure cardio in each day
    if "Weight Loss" in goal:
        for day, exercises in fixed_plan.items():
            has_cardio = any('cardio' in e.get('exercise_type', '').lower() for e in exercises)
            if not has_cardio:
                exercises.append(muscle_exercises['cardio'])

    return fixed_plan


def calculate_sets_reps(exercise, experience_level, goal):
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
        if "Strength" in goal or "Sports" in goal:
            reps = 6  # Lower reps for strength focus
        else:
            reps = 8  # Moderate reps for compound movements
    elif 'isolation' in exercise_type:
        if "Body Building" in goal:
            reps = 12  # Higher reps for hypertrophy with isolation
        else:
            reps = 10
    elif 'cardio' in exercise_type:
        sets = 3
        reps = 15  # Higher reps for cardio/endurance

    # For weight loss, higher reps across the board
    if "Weight Loss" in goal and 'cardio' not in exercise_type:
        reps += 2

    return sets, reps


# Close database connection at the very end
if __name__ == "__main__":
    try:
        st.session_state
    finally:
        db.close()
