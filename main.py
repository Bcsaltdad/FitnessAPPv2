import streamlit as st
import pandas as pd
import json
import hashlib
from datetime import datetime, timedelta
from exercise_utils import ExerciseDatabase
from workout_planner import WorkoutPlanner
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

# Create default sports profiles if not exist
sport_profiles = db.get_sports_list()
if not sport_profiles:
    # Add some default sports profiles
    default_sports = ["Running", "Golf", "Soccer", "Swimming", "Basketball", "Tennis", 
                      "Weightlifting", "CrossFit", "Bodybuilding"]
    # Create a planner instance to generate generic profiles
    temp_planner = WorkoutPlanner(db.conn)
    for sport in default_sports:
        profile = temp_planner._create_generic_profile(sport)
        db.create_sports_profile(
            sport=sport,
            required_movements=profile["required_movements"],
            energy_systems=profile["energy_systems"],
            primary_muscle_groups=profile["primary_muscle_groups"],
            injury_risk_areas=profile.get("injury_risk_areas", []),
            training_phase_focus=profile["training_phase_focus"]
        )

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
            # Simplified recommendation test for now
            user_profile = db.get_user_profile(st.session_state.user_id)
            
            if user_profile:
                st.write("### User Profile")
                st.json(user_profile)
            else:
                st.write("No user profile found. Create a workout plan first.")

            # Show current plans
            try:
                active_plans = db.get_active_plans(st.session_state.user_id)
                st.write(f"User has {len(active_plans)} active plans")

        # Add more developer tools here as needed
        if st.sidebar.button("Reset User Data"):
            st.write("This would reset the current user's data")
            # Implement actual reset functionality

        if st.sidebar.button("Database Stats"):
            # Display some database statistics
            user_count = db.cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            plan_count = db.cursor.execute("SELECT COUNT(*) FROM fitness_plans").fetchone()[0]
            workout_count = db.cursor.execute("SELECT COUNT(*) FROM workout_logs").fetchone()[0]
            progress_count = db.cursor.execute("SELECT COUNT(*) FROM progress_tracking").fetchone()[0]
            exercise_count = db.cursor.execute("SELECT COUNT(*) FROM exercises").fetchone()[0]
            sport_count = db.cursor.execute("SELECT COUNT(*) FROM sports_profiles").fetchone()[0]

            st.write("### Database Statistics")
            st.write(f"Total Users: {user_count}")
            st.write(f"Total Plans: {plan_count}")
            st.write(f"Total Logged Workouts: {workout_count}")
            st.write(f"Total Progress Entries: {progress_count}")
            st.write(f"Total Exercises: {exercise_count}")
            st.write(f"Sport Profiles: {sport_count}")

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
        notes = st.text_area("Notes (optional)", "")

        if st.form_submit_button("Save"):
            weight_kg = weight_lbs / 2.20462
            db.log_workout(workout['id'], sets, reps, weight_kg)
            
            # Also log detailed progress for better analysis
            exercises_completed = [{
                "id": workout['id'],
                "title": workout['title'],
                "sets": sets,
                "reps": reps,
                "weight": weight_lbs,
                "body_part": workout['body_part']
            }]
            
            performance_metrics = {
                "total_volume": sets * reps * weight_lbs,
                "completion_percentage": 100 * (sets * reps) / (workout['target_sets'] * workout['target_reps']),
                "weight_used": weight_lbs
            }
            
            db.log_workout_progress(
                st.session_state.user_id,
                workout['id'],
                exercises_completed,
                performance_metrics,
                notes
            )
            
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

def go_to_progress():
    st.session_state.view = 'progress'
    
# Main UI
tabs = st.tabs(["My Plans", "Exercise Library", "Create New Plan", "Progress Tracking"])

with tabs[0]:  # My Plans
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
                try:
                    if plan.get('primary_sport'):
                        st.caption(f"Sport focus: {plan['primary_sport']}")
                except: 
                    st.info("No active plans found. Create a new plan to get started!")
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
                    db.make_plan_inactive(plan['id'])
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

    # Add this check around line 257 in the week_summary view section:

    elif st.session_state.view == 'week_summary':
        # Get the selected plan details
        db.cursor.execute("SELECT * FROM fitness_plans WHERE id = ?", (st.session_state.selected_plan,))
        plan = db.cursor.fetchone()
        
        st.button("← Back to Plans", on_click=go_to_plans)
        
        # Check if plan exists
        if plan is None:
            st.error("Plan not found. It may have been deleted.")
            go_to_plans()
            st.rerun()
        else:
            st.header(f"{plan['name']} - Week {st.session_state.selected_week} Schedule")
    
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

# Replace the exercise display section in the Exercise Library tab:

with tabs[1]:  # Exercise Library
    st.header("Exercise Library")
    
    # More detailed filtering
    col1, col2 = st.columns(2)
    with col1:
        goal = st.selectbox("Filter by Goal",
                        ["All", "Strength", "Cardio", "Flexibility", "Power", "Mobility"])
    with col2:
        body_part = st.selectbox("Filter by Body Part",
                         ["All", "Chest", "Back", "Legs", "Shoulders", "Arms", "Core", "Full Body"])
    
    # Optional sports-specific filter
    sport_filter = st.selectbox("Filter by Sport", ["All"] + db.get_sports_list())
    
    # Build the query
    query = "SELECT * FROM exercises WHERE 1=1"
    params = []
    
    if goal != "All":
        query += " AND exercise_type LIKE ?"
        params.append(f"%{goal}%")
        
    if body_part != "All":
        query += " AND body_part LIKE ?"
        params.append(f"%{body_part}%")
        
    if sport_filter != "All":
        query += " AND sports_focus LIKE ?"
        params.append(f"%{sport_filter}%")
    
    # Execute the query
    db.cursor.execute(query, params)
    exercises = db.cursor.fetchall()

    if not exercises:
        st.info("No exercises found with the selected filters.")
    else:
        for exercise in exercises:
            # Convert exercise to dictionary for safer access
            ex_dict = dict(exercise)
            with st.expander(f"📋 {ex_dict['title']}", expanded=False):
                st.write(f"**Description:** {ex_dict.get('description', 'Not specified')}")
                
                # Safely access equipment and level properties
                equipment = ex_dict.get('equipment', 'Not specified')
                level = ex_dict.get('level', 'Not specified')
                
                st.write(f"**Equipment:** {equipment}")
                st.write(f"**Level:** {level}")
                
                # Show sports-specific information if available
                sports_focus = ex_dict.get('sports_focus')
                if sports_focus:
                    try:
                        sports = json.loads(sports_focus)
                        if sports:
                            st.write(f"**Sports:** {', '.join(sports)}")
                    except (json.JSONDecodeError, TypeError):
                        # Handle invalid JSON or other errors silently
                        pass
                
                movement_pattern = ex_dict.get('primary_movement_pattern')
                if movement_pattern:
                    st.write(f"**Movement Pattern:** {movement_pattern}")
                
                instructions = ex_dict.get('instructions')
                if instructions:
                    st.write("**Instructions:**")
                    try:
                        # Try splitting by comma if it's a string
                        if isinstance(instructions, str):
                            inst_list = instructions.split(',')
                            for i, instruction in enumerate(inst_list, 1):
                                st.write(f"{i}. {instruction.strip()}")
                    except:
                        # Fall back to just showing the raw instructions
                        st.write(instructions)

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
        
        # Add sports selection
        primary_sport = st.selectbox(
            "Do you have a specific sport you're training for?",
            ["None"] + db.get_sports_list()
        )

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
        
        # Add training phase selection for sports
        if primary_sport != "None":
            training_phase = st.selectbox(
                "Current training phase",
                ["General", "Off-Season", "Pre-Season", "In-Season", "Post-Season"]
            )
        else:
            training_phase = "General"

        time_per_workout = st.slider("Time available per workout (minutes)",
                                     min_value=15,
                                     max_value=120,
                                     value=45,
                                     step=5)
    
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
                    if success:
                        plan_id = result
                        st.success("Your personalized plan has been created!")
    
                        try:
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
                        except Exception as e:
                            st.warning(f"Unable to preview plan. The plan was created but preview failed.")
                            if st.session_state.dev_mode:
                                st.error(f"Debug - Error: {str(e)}")
                        
                        # Navigate back to plans view
                        st.session_state.view = 'plans'
                        st.button("Go to My Plans", on_click=go_to_plans)
                    
                    
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
                        st.write(f"**{day_names[day]}** - {len(day_workouts)} exercises")
                        for workout in day_workouts[:3]:  # Show just a few exercises as preview
                            st.write(f"- {workout['title']}: {workout['target_sets']} sets × {workout['target_reps']} reps")
                        if len(day_workouts) > 3:
                            st.write(f"- ...and {len(day_workouts) - 3} more exercises")
                    
                    # Navigate back to plans view
                    st.session_state.view = 'plans'
                    st.button("Go to My Plans", on_click=go_to_plans)
                else:
                    if isinstance(result, int):
                        plan_id = result
                        st.warning("Basic plan created. Some advanced features couldn't be applied.")
                        st.session_state.view = 'plans'
                        st.button("Go to My Plans", on_click=go_to_plans)
                    else:
                        st.error(f"Error creating workout plan: {result}")

with tabs[3]:  # Progress Tracking
    st.header("Progress Tracking")
    
    # Get user profile to check if it exists
    user_profile = db.get_user_profile(st.session_state.user_id)
    if not user_profile:
        st.info("Complete your profile by creating a workout plan to enable detailed progress tracking.")
    else:
        # Time period selection
        col1, col2 = st.columns(2)
        with col1:
            time_period = st.selectbox(
                "Time Period", 
                ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"]
            )
        with col2:
            if user_profile.get('primary_sport'):
                st.write(f"Primary Sport: {user_profile['primary_sport']}")
            else:
                st.write("No primary sport selected")
        
        # Calculate date range
        end_date = datetime.now()
        if time_period == "Last 7 Days":
            start_date = end_date - timedelta(days=7)
        elif time_period == "Last 30 Days":
            start_date = end_date - timedelta(days=30)
        elif time_period == "Last 90 Days":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = None
        
        # Get progress history
        progress_history = db.get_progress_history(st.session_state.user_id, start_date, end_date)
        
        if not progress_history:
            st.info("No workout data logged in the selected period. Complete some workouts to see progress.")
        else:
            # Analyze progress data
            total_workouts = len(progress_history)
            total_exercises = sum(len(entry['exercises_completed']) for entry in progress_history)
            avg_volume = sum(entry['performance_metrics'].get('total_volume', 0) for entry in progress_history) / total_workouts if total_workouts > 0 else 0
            
            # Display summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Workouts", total_workouts)
            with col2:
                st.metric("Total Exercises", total_exercises)
            with col3:
                st.metric("Avg Volume per Workout", f"{avg_volume:.1f} lbs")
            
            # Body part frequency analysis
            body_parts = {}
            for entry in progress_history:
                for exercise in entry['exercises_completed']:
                    if 'body_part' in exercise:
                        parts = exercise['body_part'].split('/')
                        for part in parts:
                            part = part.strip()
                            body_parts[part] = body_parts.get(part, 0) + 1
            
            # Create a visualization using Streamlit's native charts
            if body_parts:
                st.subheader("Body Part Focus")
                
                # Sort by frequency and limit to top 8
                sorted_parts = sorted(body_parts.items(), key=lambda x: x[1], reverse=True)[:8]
                
                # Create a dataframe for the chart
                chart_data = pd.DataFrame({
                    'Body Part': [p[0] for p in sorted_parts],
                    'Frequency': [p[1] for p in sorted_parts]
                })
                
                # Display with Streamlit's bar chart
                st.bar_chart(chart_data.set_index('Body Part'))
            
            # Recent workouts
            st.subheader("Recent Workouts")
            for i, entry in enumerate(progress_history[:5]):
                with st.expander(f"Workout on {entry['workout_date'][:10]}", expanded=(i==0)):
                    # Show exercises
                    for j, exercise in enumerate(entry['exercises_completed']):
                        st.write(f"{j+1}. **{exercise['title']}**: {exercise['sets']} sets × {exercise['reps']} reps @ {exercise['weight']} lbs")
                    
                    # Show notes if any
                    if entry.get('notes'):
                        st.write(f"**Notes:** {entry['notes']}")
                    
                    # Show metrics
                    metrics = entry['performance_metrics']
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Total Volume:** {metrics.get('total_volume', 0):.1f} lbs")
                    with col2:
                        st.write(f"**Completion:** {metrics.get('completion_percentage', 0):.1f}%")

# Initialize Engine class for workout recommendations (placeholder for now)
class WorkoutEngine:
    def __init__(self, db):
        self.db = db
