import streamlit as st
import pandas as pd
import json
from exercise_utils import ExerciseDatabase

# Initialize exercise database
db = ExerciseDatabase('fitness.db')

# Page configuration for better mobile view
st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for mobile responsiveness
st.markdown("""
<style>
    /* Mobile-friendly containers */
    .stApp {
        max-width: 100%;
        padding: 1rem;
    }

    /* Make buttons more touch-friendly */
    .stButton>button {
        width: 100%;
        margin: 0.5rem 0;
        padding: 0.75rem !important;
    }

    /* Improve readability on mobile */
    .st-emotion-cache-1y4p8pa {
        max-width: 100% !important;
    }

    /* Adjust expander padding */
    .streamlit-expanderHeader {
        padding: 1rem !important;
    }

    /* Make inputs touch-friendly */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input {
        padding: 0.75rem !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("Fitness Training App 💪")

# Main navigation tabs
tabs = st.tabs(["Exercise Library", "Fitness Plans", "Workout Log"])

with tabs[0]:  # Exercise Library
    st.header("Exercise Library")
    col1, col2 = st.columns([1, 1])
    with col1:
        goal = st.selectbox("Goal", ["Strength", "Cardio", "Flexibility"], key="goal_filter_library")
    with col2:
        muscle = st.text_input("Target Muscle")

    if goal:
        exercises = db.get_exercises_by_goal(goal)
        for exercise in exercises:
            with st.expander(f"📋 {exercise['title']}"):
                st.write(f"**Description:** {exercise['description']}")
                st.write(f"**Equipment:** {exercise['equipment']}")
                st.write(f"**Level:** {exercise['level']}")
                if exercise.get('instructions'):
                    st.write("**Instructions:**")
                    instructions = exercise['instructions'].split(',')
                    for i, instruction in enumerate(instructions, 1):
                        st.write(f"{i}. {instruction.strip()}")

with tabs[1]:  # Fitness Plans
    st.header("Fitness Plans")

    # Create new plan section
    with st.expander("➕ Create New Plan", expanded=True):
        st.subheader("Create Your Personalized Fitness Plan")

        # Step 1: Basic Info
        st.write("### Step 1: Basic Information")
        plan_name = st.text_input("Plan Name")

        # Step 2: Goal Selection
        st.write("### Step 2: Select Your Primary Goal")
        plan_goal = st.selectbox(
            "What's your primary fitness goal?",
            [
                "Sports and Athletics",
                "Body Building",
                "Body Weight Fitness",
                "Weight Loss",
                "Mobility Exclusive"
            ],
            key="goal_filter_plan"
        )

        # Step 3: Time Commitment
        st.write("### Step 3: Time Commitment")
        workouts_per_week = st.selectbox(
            "How many workouts can you commit to per week?",
            options=list(range(1, 15)),  # 1 to 14 workouts
            index=2  # Default to 3 workouts
        )
        duration = st.number_input("Program duration (weeks)", min_value=4, value=8, max_value=52)

        # Step 5: Equipment Access
        st.write("### Step 5: Equipment Access")
        equipment_access = st.multiselect(
            "What equipment do you have access to?",
            ["Full Gym", "Dumbbells", "Resistance Bands", "Pull-up Bar", "No Equipment"],
            default=["Full Gym"]
        )

        # Step 6: Health Considerations
        st.write("### Step 6: Health Considerations")
        limitations = st.multiselect(
            "Do you have any physical limitations or areas to avoid?",
            ["None", "Lower Back", "Knees", "Shoulders", "Neck"],
            default=["None"]
        )

        if st.button("Create Personalized Plan", use_container_width=True):
            # Store additional information in JSON format
            plan_details = {
                "workouts_per_week": workouts_per_week,
                "equipment_access": equipment_access,
                "limitations": limitations
            }
            plan_id = db.create_fitness_plan(plan_name, plan_goal, duration, json.dumps(plan_details))
            st.success("Personalized plan created! Your plan will be optimized based on your responses.")
            st.rerun()

    # View and edit plans
    plans = db.get_fitness_plans()
    for plan in plans:
        with st.expander(f"📅 {plan['name']} - {plan['goal']}", expanded=False):
            cols = st.columns([1, 1])
            with cols[0]:
                week = st.selectbox(f"Week", range(1, plan['duration_weeks'] + 1), key=f"week_{plan['id']}")
            with cols[1]:
                day = st.selectbox(f"Day", range(1, 8), key=f"day_{plan['id']}")

            workouts = db.get_plan_workouts(plan['id'], week, day)
            if workouts:
                for workout in workouts:
                    st.write(f"**{workout['title']}**")
                    st.write(f"Target: {workout['target_sets']} sets × {workout['target_reps']} reps")

            st.divider()
            st.subheader("Add Workout")
            exercises = db.get_exercises_by_goal(plan['goal'])
            exercise = st.selectbox("Exercise", 
                                [ex['title'] for ex in exercises],
                                key=f"ex_{plan['id']}_{week}_{day}")
            cols = st.columns([1, 1])
            with cols[0]:
                sets = st.number_input("Sets", 1, 10, 3, key=f"sets_{plan['id']}_{week}_{day}")
            with cols[1]:
                reps = st.number_input("Reps", 1, 30, 10, key=f"reps_{plan['id']}_{week}_{day}")

            if st.button("Add to Plan", key=f"add_{plan['id']}_{week}_{day}", use_container_width=True):
                exercise_id = next(ex['id'] for ex in exercises if ex['title'] == exercise)
                db.add_workout_to_plan(plan['id'], exercise_id, day, week, sets, reps)
                st.success("Workout added!")
                st.rerun()

with tabs[2]:  # Workout Log
    st.header("Workout Log")
    plans = db.get_fitness_plans()
    if plans:
        plan = st.selectbox("Select Plan", [p['name'] for p in plans], key="select_plan")
        plan_id = next(p['id'] for p in plans if p['name'] == plan)

        cols = st.columns([1, 1])
        with cols[0]:
            week = st.number_input("Week", 1, 52, 1)
        with cols[1]:
            day = st.number_input("Day", 1, 7, 1)

        workouts = db.get_plan_workouts(plan_id, week, day)
        for workout in workouts:
            with st.expander(f"Log: {workout['title']}", expanded=False):
                cols = st.columns([1, 1, 1])
                with cols[0]:
                    sets = st.number_input("Sets", 1, 10, workout['target_sets'], key=f"log_sets_{workout['id']}")
                with cols[1]:
                    reps = st.number_input("Reps", 1, 30, workout['target_reps'], key=f"log_reps_{workout['id']}")
                with cols[2]:
                    weight = st.number_input("Weight (kg)", 0.0, 500.0, 0.0, key=f"log_weight_{workout['id']}")

                if st.button("Log Workout", key=f"log_{workout['id']}", use_container_width=True):
                    db.log_workout(workout['id'], sets, reps, weight)
                    st.success("Workout logged!")

# Close database connection
db.close()