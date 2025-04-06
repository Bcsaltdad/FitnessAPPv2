
import sqlite3
from typing import List, Dict, Any

class ExerciseDatabase:
    def __init__(self, db_path: str = 'fitness.db'):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
    
    def get_exercises_by_goal(self, goal: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get exercises based on fitness goal"""
        mapping = {
            'strength': ['Strength', 'Powerlifting'],
            'cardio': ['Cardio', 'Plyometrics'],
            'flexibility': ['Stretching'],
        }
        
        exercise_types = mapping.get(goal.lower(), ['Strength'])
        
        query = '''
        SELECT e.*, GROUP_CONCAT(i.instruction) as instructions
        FROM exercises e
        LEFT JOIN exercise_instructions i ON e.id = i.exercise_id
        WHERE e.exercise_type IN ({})
        GROUP BY e.id
        LIMIT ?
        '''.format(','.join(['?'] * len(exercise_types)))
        
        self.cursor.execute(query, exercise_types + [limit])
        rows = self.cursor.fetchall()
        
        return [self._row_to_dict(row) for row in rows]
    
    def get_exercises_by_muscle(self, muscle: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get exercises targeting specific muscle group"""
        query = '''
        SELECT e.*, GROUP_CONCAT(i.instruction) as instructions
        FROM exercises e
        LEFT JOIN exercise_instructions i ON e.id = i.exercise_id
        WHERE e.body_part LIKE ?
        GROUP BY e.id
        LIMIT ?
        '''
        
        self.cursor.execute(query, (f'%{muscle}%', limit))
        rows = self.cursor.fetchall()
        
        return [self._row_to_dict(row) for row in rows]
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert a database row to a dictionary"""
        columns = [col[0] for col in self.cursor.description]
        return {columns[i]: row[i] for i in range(len(columns))}
    
    def close(self):
        self.conn.close()
