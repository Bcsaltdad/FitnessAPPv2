import streamlit as st
import sqlite3
import pandas as pd
import http.client

# API connection details
API_KEY = "9943fa8927msh9f5dd0b4afc6aa8p1166c3jsnd4ce488a3caf"  # Replace with your actual API key
API_HOST = "exercisedb.p.rapidapi.com"

def fetch_exercises():
    conn = http.client.HTTPSConnection(API_HOST)
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': API_HOST
    }
    conn.request("GET", "/status", headers=headers) #This API endpoint needs to be updated to fetch exercises.  Placeholder for now.
    res = conn.getresponse()
    data = res.read()
    try:
        exercises = eval(data.decode("utf-8")) #Assuming the API returns a list of dictionaries.  Adjust accordingly.
        return exercises
    except:
        return []


# Database setup
conn = sqlite3.connect("workouts.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client TEXT,
        date TEXT,
        exercise TEXT,
        category TEXT,
        sets INTEGER,
        reps INTEGER,
        weight FLOAT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS exercise_library (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        category TEXT,
        description TEXT,
        recommended_sets INTEGER,
        recommended_reps INTEGER
    )
""")
conn.commit()

# Exercise categories
CATEGORIES = [
    "Strength Training",
    "Cardio",
    "Flexibility",
    "HIIT",
    "Core"
]

# Sidebar for adding workouts
st.sidebar.header("Log a Workout")
client_name = st.sidebar.text_input("Client Name")
date = st.sidebar.date_input("Date")
category = st.sidebar.selectbox("Category", CATEGORIES)
exercise = st.sidebar.text_input("Exercise")
sets = st.sidebar.number_input("Sets", min_value=1, value=3)
reps = st.sidebar.number_input("Reps", min_value=1, value=10)
weight = st.sidebar.number_input("Weight (kg)", min_value=0.0, value=20.0)

if st.sidebar.button("Add Workout"):
    cursor.execute(
        "INSERT INTO workouts (client, date, exercise, category, sets, reps, weight) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (client_name, date, exercise, category, sets, reps, weight),
    )
    conn.commit()
    st.sidebar.success("Workout added!")

# Main UI
st.title("Fitness Trainer Dashboard 💪")

# Filters
st.sidebar.header("Filters")
filter_client = st.sidebar.text_input("Filter by Client Name")
filter_category = st.sidebar.multiselect("Filter by Category", CATEGORIES)

# Load and filter data
df = pd.read_sql_query("SELECT * FROM workouts", conn)
if filter_client:
    df = df[df["client"].str.contains(filter_client, case=False)]
if filter_category:
    df = df[df["category"].isin(filter_category)]

if not df.empty:
    # Interactive Data Table
    st.subheader("Workout Log")
    df_display = df.drop(columns=["id"])
    st.data_editor(df_display, use_container_width=True, height=300)

    # Summary Stats
    st.subheader("Workout Statistics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Sets", df["sets"].sum())
    col2.metric("Total Reps", df["reps"].sum())
    col3.metric("Total Volume (kg)", (df["sets"] * df["reps"] * df["weight"]).sum())
    col4.metric("Unique Exercises", df["exercise"].nunique())

    # Progress Charts
    st.subheader("Progress Tracking")

    # Weight progression per exercise
    if st.checkbox("Show Weight Progression"):
        exercise_choice = st.selectbox("Select Exercise", df["exercise"].unique())
        exercise_progress = df[df["exercise"] == exercise_choice].sort_values("date")
        st.line_chart(exercise_progress.set_index("date")["weight"])

    # Per-client workout summary
    st.subheader("Client Summaries")
    clients = df["client"].unique()
    for client in clients:
        with st.expander(f"📊 {client}'s Progress"):
            client_df = df[df["client"] == client].drop(columns=["id"])

            # Client stats
            st.write("Recent Activity")
            st.data_editor(client_df.sort_values("date", ascending=False).head(),
                         use_container_width=True, height=150)

            # Category breakdown
            cat_data = client_df["category"].value_counts()
            st.write("Workout Category Distribution")
            st.bar_chart(cat_data)

else:
    st.info("No workouts logged yet. Start by adding a workout!")

# Exercise Library Management
with st.expander("📚 Exercise Library Management"):
    if st.button("Import Exercises from API"):
        with st.spinner("Fetching exercises from API..."):
            try:
                exercises = fetch_exercises()
                for exercise in exercises:
                    # Map API data to our database structure
                    cursor.execute("""
                        INSERT OR IGNORE INTO exercise_library 
                        (name, category, description, recommended_sets, recommended_reps)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        exercise.get('name', ''),
                        exercise.get('bodyPart', ''),
                        exercise.get('instructions', ''),
                        3,  # Default recommended sets
                        12  # Default recommended reps
                    ))
                conn.commit()
                st.success(f"Successfully imported {len(exercises)} exercises!")
            except Exception as e:
                st.error(f"Failed to fetch exercises: {str(e)}")


# Close database connection
conn.close()