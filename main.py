import streamlit as st
from exercise_utils import ExerciseDatabase

# Initialize exercise database
db = ExerciseDatabase('fitness.db')

st.title("Fitness Exercise Database 💪")

# Sidebar filters
st.sidebar.header("Filters")
goal = st.sidebar.selectbox("Filter by Goal", ["Strength", "Cardio", "Flexibility"])
muscle = st.sidebar.text_input("Filter by Muscle Group")

# Main content
if goal:
    st.subheader(f"{goal} Exercises")
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
                    st.write(f"{i}. {instruction}")

if muscle:
    st.subheader(f"Exercises for {muscle}")
    muscle_exercises = db.get_exercises_by_muscle(muscle)

    for exercise in muscle_exercises:
        with st.expander(f"📋 {exercise['title']}"):
            st.write(f"**Description:** {exercise['description']}")
            st.write(f"**Equipment:** {exercise['equipment']}")
            st.write(f"**Level:** {exercise['level']}")
            if exercise.get('instructions'):
                st.write("**Instructions:**")
                instructions = exercise['instructions'].split(',')
                for i, instruction in enumerate(instructions, 1):
                    st.write(f"{i}. {instruction}")

# Close database connection
db.close()