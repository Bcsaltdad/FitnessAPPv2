import streamlit as st
import pandas as pd
from exercise_utils import ExerciseDatabase
from datetime import datetime

# Initialize exercise database
db = ExerciseDatabase('fitness.db')

st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

# Custom CSS
st.markdown("""
<style>
    .workout-card {
        padding: 1rem;
        border: 1px solid #ddd;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
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

# Main navigation
tabs = st.tabs(["My Plans", "Exercise Library", "Create New Plan"])

with tabs[0]:  # My Plans
    st.header("My Active Plans")
    active_plans = db.get_active_plans()

    if not active_plans:
        st.info("No active plans found. Create a new plan to get started!")

    for plan in active_plans:
        with st.expander(f"📋 {plan['name']} - {plan['goal']}", expanded=True):
            # Plan Summary Metrics
            summary = db.get_plan_summary(plan['id'])
            if summary:
                cols = st.columns(4)
                with cols[0]:
                    st.metric("Total Weeks", plan['duration_weeks'])
                with cols[1]:
                    completed_workouts = sum(week['exercises_completed'] or 0 for week in summary)
                    st.metric("Completed Workouts", completed_workouts)
                with cols[2]:
                    avg_weight = sum(week['avg_weight'] or 0 for week in summary) / len(summary) if summary else 0
                    st.metric("Avg Weight (kg)", f"{avg_weight:.1f}")
                with cols[3]:
                    days_worked = sum(week['days_worked'] or 0 for week in summary)
                    st.metric("Days Worked", days_worked)

            # Week Selection
            week = st.selectbox("Select Week", range(1, plan['duration_weeks'] + 1), key=f"week_{plan['id']}")

            # Get workouts for the selected week
            all_workouts = []
            for day in range(1, 8):
                workouts = db.get_plan_workouts(plan['id'], week, day)
                if workouts:
                    all_workouts.extend((day, w) for w in workouts)

            # Group workouts by type
            workout_types = ["Power", "Strength", "Agility", "Core", "Conditioning"]
            for workout_type in workout_types:
                relevant_workouts = [w for d, w in all_workouts if w['title'].startswith(workout_type)]
                if relevant_workouts:
                    st.subheader(f"{workout_type} Workouts")
                    for workout in relevant_workouts:
                        with st.expander(f"Day {workout['day_of_week']}: {workout['title']}", expanded=False):
                            st.write(f"**Description:** {workout['description']}")
                            st.write(f"**Equipment:** {workout['equipment']}")
                            st.write(f"**Target:** {workout['target_sets']} sets × {workout['target_reps']} reps")

                            # Logging section
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                sets = st.number_input("Sets Completed", 1, 10, workout['target_sets'], key=f"sets_{workout['id']}")
                            with col2:
                                reps = st.number_input("Reps Completed", 1, 30, workout['target_reps'], key=f"reps_{workout['id']}")
                            with col3:
                                weight = st.number_input("Weight (kg)", 0.0, 500.0, 0.0, key=f"weight_{workout['id']}")

                            if st.button("Log Workout", key=f"log_{workout['id']}"):
                                db.log_workout(workout['id'], sets, reps, weight)
                                st.success("Workout logged successfully!")
                                st.rerun()

with tabs[1]:  # Exercise Library
    st.header("Exercise Library")
    goal = st.selectbox("Filter by Goal", ["Strength", "Cardio", "Flexibility"])
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

    plan_name = st.text_input("Plan Name")
    plan_goal = st.selectbox(
        "What's your primary fitness goal?",
        [
            "Sports and Athletics",
            "Body Building",
            "Body Weight Fitness",
            "Weight Loss",
            "Mobility Exclusive"
        ]
    )

    workouts_per_week = st.selectbox(
        "How many workouts can you commit to per week?",
        options=list(range(1, 15)),
        index=2
    )
    duration = st.number_input("Program duration (weeks)", min_value=4, value=8, max_value=52)

    equipment_access = st.multiselect(
        "What equipment do you have access to?",
        ["Full Gym", "Dumbbells", "Resistance Bands", "Pull-up Bar", "No Equipment"],
        default=["Full Gym"]
    )

    limitations = st.multiselect(
        "Do you have any physical limitations or areas to avoid?",
        ["None", "Lower Back", "Knees", "Shoulders", "Neck"],
        default=["None"]
    )

    if st.button("Create Plan", use_container_width=True):
        plan_details = {
            "workouts_per_week": workouts_per_week,
            "equipment_access": equipment_access,
            "limitations": limitations
        }
        plan_id = db.create_fitness_plan(plan_name, plan_goal, duration, json.dumps(plan_details))
        st.success("Your personalized plan has been created!")
        st.rerun()

# Close database connection
db.close()