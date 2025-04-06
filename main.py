import streamlit as st
import pandas as pd
import json
import hashlib
from exercise_utils import ExerciseDatabase
from datetime import datetime
from workout_planner import WorkoutPlanner
from Engine import WorkoutRecommender, WorkoutEngine
from WorkoutGenerator import WorkoutGenerator

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
            # Create workout generator instance
            planner = WorkoutPlanner(db.conn)
            generator = WorkoutGenerator(db, planner, WorkoutEngine(db))
            
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
                time_per_workout=time_per_workout
            )
            
            if success:
                plan_id = result
                st.success("Your personalized plan has been created!")
                
                # Preview first week
                st.write("### Preview of Week 1")
                workouts = db.get_plan_workouts(plan_id, 1, None)
                
                # Group by day and display
                # Display code...
                
                # Navigate back to plans view
                st.session_state.view = 'plans'
                st.rerun()
            else:
                if isinstance(result, int):
                    plan_id = result
                    st.warning("Basic plan created. Some advanced features couldn't be applied.")
                    st.session_state.view = 'plans'
                    st.rerun()
                else:
                    st.error(f"Error creating workout plan: {result}")
