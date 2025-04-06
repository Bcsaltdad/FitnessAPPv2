
import sqlite3
import pandas as pd
import json

def setup_database():
    # Connect to SQLite database
    conn = sqlite3.connect('fitness.db')
    cursor = conn.cursor()
    
    # Create exercises table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        exercise_type TEXT,
        body_part TEXT,
        equipment TEXT,
        level TEXT,
        rating FLOAT,
        rating_desc TEXT
    )''')
    
    # Create muscles table for target muscles
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS target_muscles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exercise_id INTEGER,
        muscle_name TEXT,
        is_primary BOOLEAN,
        FOREIGN KEY (exercise_id) REFERENCES exercises (id)
    )''')
    
    # Create instructions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS exercise_instructions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exercise_id INTEGER,
        step_number INTEGER,
        instruction TEXT,
        FOREIGN KEY (exercise_id) REFERENCES exercises (id)
    )''')

    conn.commit()
    return conn, cursor

def import_exercise_data(conn, cursor, csv_file):
    # Read CSV file
    df = pd.read_csv(csv_file)
    
    # Insert exercises
    for _, row in df.iterrows():
        cursor.execute('''
        INSERT INTO exercises (title, description, exercise_type, body_part, equipment, level, rating, rating_desc)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            row['Title'],
            row['Desc'],
            row['Type'],
            row['BodyPart'],
            row['Equipment'],
            row['Level'],
            row['Rating'],
            row['RatingDesc']
        ))
        
        exercise_id = cursor.lastrowid
        
        # Handle instructions if they exist
        if isinstance(row.get('instructions'), str):
            try:
                instructions = eval(row['instructions'])
                for i, instruction in enumerate(instructions, 1):
                    cursor.execute('''
                    INSERT INTO exercise_instructions (exercise_id, step_number, instruction)
                    VALUES (?, ?, ?)
                    ''', (exercise_id, i, instruction))
            except:
                pass

    conn.commit()

if __name__ == "__main__":
    conn, cursor = setup_database()
    import_exercise_data(conn, cursor, 'attached_assets/workout_data.csv')
    print("Database setup complete!")
