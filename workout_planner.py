import sqlite3
import json
import datetime
import logging
from typing import Dict, List, Any, Tuple, Optional

class WorkoutPlanner:
    def __init__(self, db_connection=None, db_path='fitness.db'):
        """
        Initialize the workout planner with a database connection.
        
        Args:
            db_connection: Optional existing database connection
            db_path: Path to the database file if no connection is provided
        """
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        if db_connection:
            self.db = db_connection
        else:
            self.db = sqlite3.connect(db_path)
        
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()
                
    def create_workout_plan(self, user_id: int, plan_name: str, goal: str, 
                          duration_weeks: int, primary_sport: str = None,
                          training_phase: str = "General") -> int:
        """
        Create a new workout plan for a user.
        
        Args:
            user_id: User ID
            plan_name: Name of the plan
            goal: Primary fitness goal
            duration_weeks: Duration in weeks
            primary_sport: Optional sport focus
            training_phase: Training phase (Off-Season, In-Season, etc.)
            
        Returns:
            ID of the created plan
        """
        created_at = datetime.datetime.now()
        
        try:
            self.cursor.execute('''
            INSERT INTO fitness_plans
