
import streamlit as st
from exercise_utils import ExerciseDatabase

# Initialize exercise database
db = ExerciseDatabase('fitness.db')

st.title("Fitness Exercise Database 💪")

# Sidebar navigation
page = st.sidebar.selectbox("Navigation", ["Exercise Library", "Fitness Plans", "Workout Log"])

if page == "Exercise Library":
    # Existing exercise library code
    goal = st.sidebar.selectbox("Filter by Goal", ["Strength", "Cardio", "Flexibility"])
    muscle = st.sidebar.text_input("Filter by Muscle Group")

    if goal:
        st.subheader(f"{goal} Exercises")
        exercises = db.get_exercises_by_goal(goal)
        for exercise in exercises:
            with st.expander(f"📋 {exercise['title']}"):
                st.write(f"**Description:** {exercise['description']}")
                st.write(f"**Equipment:** {exercise['equipment']}")
                st.write(f"**Level:** {exercise['level']}")

elif page == "Fitness Plans":
    st.subheader("Fitness Plans")
    
    # Create new plan
    with st.expander("Create New Plan"):
        plan_name = st.text_input("Plan Name")
        plan_goal = st.selectbox("Goal", ["Strength", "Cardio", "Flexibility"])
        duration = st.number_input("Duration (weeks)", min_value=1, value=4)
        if st.button("Create Plan"):
            plan_id = db.create_fitness_plan(plan_name, plan_goal, duration)
            st.success("Plan created!")

    # View and edit plans
    plans = db.get_fitness_plans()
    for plan in plans:
        with st.expander(f"📅 {plan['name']} - {plan['goal']}"):
            week = st.selectbox(f"Week", range(1, plan['duration_weeks'] + 1), key=f"week_{plan['id']}")
            day = st.selectbox(f"Day", range(1, 8), key=f"day_{plan['id']}")
            
            # Show workouts for selected day
            workouts = db.get_plan_workouts(plan['id'], week, day)
            if workouts:
                for workout in workouts:
                    st.write(f"**{workout['title']}**")
                    st.write(f"Target: {workout['target_sets']} sets x {workout['target_reps']} reps")
            
            # Add workout to day
            st.divider()
            st.write("Add Workout")
            exercises = db.get_exercises_by_goal(plan['goal'])
            exercise = st.selectbox("Exercise", 
                                  [ex['title'] for ex in exercises],
                                  key=f"ex_{plan['id']}_{week}_{day}")
            sets = st.number_input("Sets", 1, 10, 3, key=f"sets_{plan['id']}_{week}_{day}")
            reps = st.number_input("Reps", 1, 30, 10, key=f"reps_{plan['id']}_{week}_{day}")
            
            if st.button("Add to Plan", key=f"add_{plan['id']}_{week}_{day}"):
                exercise_id = next(ex['id'] for ex in exercises if ex['title'] == exercise)
                db.add_workout_to_plan(plan['id'], exercise_id, day, week, sets, reps)
                st.success("Workout added!")
                st.rerun()

elif page == "Workout Log":
    st.subheader("Log Your Workout")
    plans = db.get_fitness_plans()
    if plans:
        plan = st.selectbox("Select Plan", [p['name'] for p in plans])
        plan_id = next(p['id'] for p in plans if p['name'] == plan)
        week = st.number_input("Week", 1, 52, 1)
        day = st.number_input("Day", 1, 7, 1)
        
        workouts = db.get_plan_workouts(plan_id, week, day)
        for workout in workouts:
            with st.expander(f"Log: {workout['title']}"):
                sets = st.number_input("Sets Completed", 1, 10, workout['target_sets'], key=f"log_sets_{workout['id']}")
                reps = st.number_input("Reps Completed", 1, 30, workout['target_reps'], key=f"log_reps_{workout['id']}")
                weight = st.number_input("Weight (kg)", 0.0, 500.0, 0.0, key=f"log_weight_{workout['id']}")
                
                if st.button("Log Workout", key=f"log_{workout['id']}"):
                    db.log_workout(workout['id'], sets, reps, weight)
                    st.success("Workout logged!")

# Close database connection
db.close()
