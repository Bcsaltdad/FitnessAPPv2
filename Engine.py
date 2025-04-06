import random
from datetime import datetime, timedelta

class WorkoutRecommender:
    def __init__(self, db_connection):
        self.db = db_connection

    def get_daily_recommendation(self, user_id, plan_id=None):
        """
        Generate a personalized daily workout recommendation

        Parameters:
        - user_id: User ID
        - plan_id: Optional plan ID to use as base

        Returns:
        - Dictionary with recommended workout
        """
        # Get user profile and active plans
        if not plan_id:
            active_plans = self.db.get_active_plans(user_id)
            if active_plans:
                plan_id = active_plans[0]['id']
            else:
                return self._generate_default_workout(user_id)

        # Get current date information
        today = datetime.now()
        weekday = today.weekday() + 1  # Convert to 1-7 range (Monday = 1)

        # Calculate which week we're in for this plan
        self.db.cursor.execute(
            "SELECT created_date FROM fitness_plans WHERE id = ?",
            (plan_id,)
        )
        plan_start = self.db.cursor.fetchone()

        if not plan_start:
            return self._generate_default_workout(user_id)

        start_date = datetime.strptime(plan_start['created_date'], "%Y-%m-%d")
        days_since_start = (today - start_date).days
        current_week = (days_since_start // 7) + 1

        # Get workouts for this day in current week
        self.db.cursor.execute(
            """
            SELECT * FROM plan_workouts 
            WHERE plan_id = ? AND week = ? AND day = ?
            """,
            (plan_id, current_week, weekday)
        )
        workouts = self.db.cursor.fetchall()

        if not workouts:
            # If no workouts scheduled for today, check if we need a recovery focus
            if self._needs_recovery(user_id):
                return self._generate_recovery_workout(user_id)
            else:
                # Suggest a workout from another day this week
                self.db.cursor.execute(
                    """
                    SELECT * FROM plan_workouts 
                    WHERE plan_id = ? AND week = ?
                    ORDER BY RANDOM() LIMIT 1
                    """,
                    (plan_id, current_week)
                )
                alternative = self.db.cursor.fetchone()

                if alternative:
                    # Find all workouts for this day
                    self.db.cursor.execute(
                        """
                        SELECT * FROM plan_workouts 
                        WHERE plan_id = ? AND week = ? AND day = ?
                        """,
                        (plan_id, current_week, alternative['day'])
                    )
                    alt_workouts = self.db.cursor.fetchall()

                    day_names = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 
                               4: "Thursday", 5: "Friday", 6: "Saturday", 7: "Sunday"}

                    return {
                        'type': 'alternative',
                        'message': f"No workout scheduled for today. Here's your {day_names[alternative['day']]} workout instead:",
                        'day': day_names[alternative['day']],
                        'workouts': alt_workouts
                    }

        # Check if user has already completed today's workout
        completed_workouts = []
        for workout in workouts:
            self.db.cursor.execute(
                """
                SELECT COUNT(*) FROM workout_logs
                WHERE workout_id = ? AND date = date('now')
                """,
                (workout['id'],)
            )
            if self.db.cursor.fetchone()[0] > 0:
                # User already did this workout today
                completed_workouts.append(workout)

        # Remove completed workouts
        workouts = [w for w in workouts if w not in completed_workouts]

        if not workouts:
            return {
                'type': 'completed',
                'message': "You've completed all scheduled workouts for today! Would you like a bonus workout?",
                'bonus_workout': self._generate_bonus_workout(user_id, plan_id)
            }

        # Get exercise details for each workout
        result_workouts = []
        for workout in workouts:
            self.db.cursor.execute(
                """
                SELECT * FROM exercises WHERE id = ?
                """,
                (workout['exercise_id'],)
            )
            exercise = self.db.cursor.fetchone()

            if exercise:
                workout_detail = dict(workout)
                workout_detail.update({
                    'title': exercise['title'],
                    'exercise_type': exercise.get('exercise_type', 'Strength'),
                    'equipment': exercise.get('equipment', ''),
                    'muscle_group': exercise.get('muscle_group', ''),
                    'level': exercise.get('level', '')
                })
                result_workouts.append(workout_detail)

        # Generate personalized adjustment recommendations
        adjustments = []
        # Check recent workouts to make appropriate recommendations
        recent_workouts = self._get_recent_workouts(user_id)

        # Get previous workouts for the same exercises to track progress
        for workout in result_workouts:
            try:
                # Check if there are previous logs for this exercise
                self.db.cursor.execute(
                    """
                    SELECT * FROM workout_logs
                    WHERE workout_id IN (
                        SELECT id FROM plan_workouts 
                        WHERE exercise_id = ? AND user_id = ?
                    )
                    ORDER BY date DESC
                    LIMIT 3
                    """,
                    (workout['exercise_id'], user_id)
                )
                previous_logs = self.db.cursor.fetchall()

                if previous_logs:
                    last_log = previous_logs[0]
                    # Check if weight has increased over time
                    if len(previous_logs) >= 2:
                        weight_trend = last_log['weight'] - previous_logs[-1]['weight']
                        if weight_trend <= 0:
                            adjustments.append(f"Try to increase weight on {workout['title']} today")

                    # Check if reps have been consistent
                    if last_log['sets_completed'] < last_log['target_sets'] or last_log['reps_completed'] < last_log['target_reps']:
                        adjustments.append(f"Focus on completing all {workout['target_sets']} sets of {workout['title']}")
            except Exception as e:
                # Skip this adjustment if there's an error
                pass

        return {
            'type': 'scheduled',
            'message': "Here's your workout for today:",
            'workouts': result_workouts,
            'adjustments': adjustments,
            'muscle_recovery': self._get_muscle_recovery_status(user_id)
        }

    def _needs_recovery(self, user_id):
        """Check if user needs a recovery day based on recent workout history"""
        # Get workouts from the last 3 days
        three_days_ago = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

        self.db.cursor.execute(
            """
            SELECT COUNT(*) FROM workout_logs
            WHERE date >= ? AND user_id = ?
            """,
            (three_days_ago, user_id)
        )
        recent_workout_count = self.db.cursor.fetchone()[0]

        # If more than 5 workouts in last 3 days, probably needs recovery
        return recent_workout_count > 5

    def _generate_recovery_workout(self, user_id):
        """Generate a recovery-focused workout"""
        recovery_options = [
            {
                'title': 'Active Recovery',
                'description': 'Low-intensity movement to promote recovery',
                'exercises': [
                    {'title': 'Light Walking', 'instructions': 'Walk at an easy pace for 20-30 minutes'},
                    {'title': 'Dynamic Stretching', 'instructions': 'Full body dynamic stretches, 30 seconds each movement'},
                    {'title': 'Foam Rolling', 'instructions': 'Roll major muscle groups, 1 minute per area'},
                ]
            },
            {
                'title': 'Mobility Focus',
                'description': 'Improve joint mobility and flexibility',
                'exercises': [
                    {'title': 'Hip Mobility Flow', 'instructions': '5 minutes of hip circles, lunges, and squats'},
                    {'title': 'Shoulder Mobility', 'instructions': 'Arm circles, wall slides, and band pull-aparts'},
                    {'title': 'Ankle Mobility', 'instructions': 'Ankle circles, calf stretches, and toe raises'},
                ]
            },
            {
                'title': 'Light Cardio',
                'description': 'Improve circulation without muscle stress',
                'exercises': [
                    {'title': 'Easy Cycling', 'instructions': '15-20 minutes at low resistance'},
                    {'title': 'Swimming', 'instructions': 'Easy laps for 10-15 minutes, focus on technique'},
                    {'title': 'Elliptical', 'instructions': '10-15 minutes at low intensity'},
                ]
            }
        ]

        selected = random.choice(recovery_options)

        return {
            'type': 'recovery',
            'message': "You've been working hard! Here's a recovery workout:",
            'workout': selected
        }

    def _generate_bonus_workout(self, user_id, plan_id):
        """Generate a bonus workout after completing scheduled training"""

        # Get plan's goal
        self.db.cursor.execute(
            "SELECT goal FROM fitness_plans WHERE id = ?",
            (plan_id,)
        )
        plan = self.db.cursor.fetchone()
        goal = plan['goal'] if plan else 'General Fitness'

        # Get recently worked muscle groups to avoid
        recent_muscles = self._get_recent_muscle_groups(user_id)

        # Determine appropriate bonus workout type
        if 'Body Building' in goal:
            # Get a lagging muscle group that hasn't been hit recently
            potential_groups = ['Arms', 'Shoulders', 'Calves', 'Abs']
            target_group = next((g for g in potential_groups if g not in recent_muscles), 'Arms')

            return {
                'title': f'{target_group} Specialization',
                'description': f'Focus on {target_group} with high volume',
                'exercises': self._get_exercises_for_muscle_group(target_group, 4)
            }
        elif 'Weight Loss' in goal:
            return {
                'title': 'Calorie Burner',
                'description': 'High-intensity interval training to burn extra calories',
                'exercises': [
                    {'title': 'HIIT Circuit', 'instructions': '30 seconds work, 15 seconds rest for 5 exercises, 4 rounds'},
                    {'title': 'Jump Rope', 'instructions': '3 sets of 1 minute fast jumping'},
                    {'title': 'Mountain Climbers', 'instructions': '3 sets of 30 seconds'},
                ]
            }
        else:
            return {
                'title': 'Core & Mobility',
                'description': 'Strengthen your core and improve overall mobility',
                'exercises': [
                    {'title': 'Plank Variations', 'instructions': '3 sets of 30-45 seconds each variation'},
                    {'title': 'Russian Twists', 'instructions': '3 sets of 20 reps'},
                    {'title': 'Hip Mobility Flow', 'instructions': '5 minutes of dynamic hip movements'},
                ]
            }

    def _get_exercises_for_muscle_group(self, muscle_group, count=3):
        """Get exercises targeting a specific muscle group"""
        try:
            self.db.cursor.execute(
                """
                SELECT * FROM exercises
                WHERE muscle_group LIKE ?
                ORDER BY RANDOM()
                LIMIT ?
                """,
                (f"%{muscle_group}%", count)
            )
            exercises = self.db.cursor.fetchall()

            # Format exercises for display
            return [{'title': ex['title'], 'instructions': ex.get('instructions', '')} for ex in exercises]
        except Exception as e:
            # Return default exercises if there's an error
            return [
                {'title': 'Dumbbell Curls', 'instructions': '3 sets of 12 reps'},
                {'title': 'Push-ups', 'instructions': '3 sets of 10-15 reps'},
                {'title': 'Bodyweight Squats', 'instructions': '3 sets of 15 reps'}
            ]

    def _get_recent_muscle_groups(self, user_id, days=2):
        """Get muscle groups worked in the last few days"""
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        try:
            self.db.cursor.execute(
                """
                SELECT DISTINCT e.muscle_group
                FROM workout_logs wl
                JOIN plan_workouts pw ON wl.workout_id = pw.id
                JOIN exercises e ON pw.exercise_id = e.id
                WHERE wl.date >= ? AND wl.user_id = ?
                """,
                (cutoff_date, user_id)
            )

            return [row['muscle_group'] for row in self.db.cursor.fetchall() if row['muscle_group']]
        except Exception as e:
            # Return empty list if there's an error
            return []

    def _get_muscle_recovery_status(self, user_id):
        """Get recovery status of major muscle groups"""
        muscle_groups = ['Chest', 'Back', 'Legs', 'Shoulders', 'Arms', 'Core']
        recovery_status = {}

        for muscle in muscle_groups:
            # Check when this muscle was last trained
            try:
                self.db.cursor.execute(
                    """
                    SELECT MAX(wl.date) as last_date
                    FROM workout_logs wl
                    JOIN plan_workouts pw ON wl.workout_id = pw.id
                    JOIN exercises e ON pw.exercise_id = e.id
                    WHERE e.muscle_group LIKE ? AND wl.user_id = ?
                    """,
                    (f"%{muscle}%", user_id)
                )

                result = self.db.cursor.fetchone()
                last_trained = result['last_date'] if result else None

                if not last_trained:
                    recovery_status[muscle] = "Ready"
                    continue

                last_date = datetime.strptime(last_trained, "%Y-%m-%d")
                days_since = (datetime.now() - last_date).days

                if days_since <= 1:
                    status = "Recovery needed"
                elif days_since <= 2:
                    status = "Partial recovery"
                else:
                    status = "Ready"

                recovery_status[muscle] = f"{status} ({days_since} days)"
            except Exception as e:
                recovery_status[muscle] = "Ready"

        return recovery_status

    def _get_recent_workouts(self, user_id, days=7):
        """Get recent workouts for a user"""
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        try:
            self.db.cursor.execute(
                """
                SELECT wl.*, pw.exercise_id, e.title, e.muscle_group
                FROM workout_logs wl
                JOIN plan_workouts pw ON wl.workout_id = pw.id
                JOIN exercises e ON pw.exercise_id = e.id
                WHERE wl.date >= ? AND wl.user_id = ?
                ORDER BY wl.date DESC
                """,
                (cutoff_date, user_id)
            )

            return self.db.cursor.fetchall()
        except Exception as e:
            # Return empty list if there's an error
            return []

    def _generate_default_workout(self, user_id):
        """Generate a default workout when no plans are available"""
        try:
            # Get user's experience level if available
            self.db.cursor.execute(
                """
                SELECT plan_details FROM fitness_plans 
                WHERE user_id = ? 
                ORDER BY created_date DESC LIMIT 1
                """,
                (user_id,)
            )

            result = self.db.cursor.fetchone()
            experience = "Beginner"  # Default

            if result and result['plan_details']:
                plan_details = json.loads(result['plan_details'])
                experience = plan_details.get('experience_level', 'Beginner')

            # Get random exercises based on experience
            self.db.cursor.execute(
                """
                SELECT * FROM exercises
                WHERE level = ?
                ORDER BY RANDOM()
                LIMIT 6
                """,
                (experience,)
            )

            exercises = self.db.cursor.fetchall()

            workout_details = []
            for exercise in exercises:
                if exercise['exercise_type'] == 'Compound':
                    sets, reps = (3, 10) if experience == 'Beginner' else (4, 8)
                else:
                    sets, reps = (3, 12) if experience == 'Beginner' else (3, 15)

                workout_details.append({
                    'title': exercise['title'],
                    'target_sets': sets,
                    'target_reps': reps,
                    'exercise_type': exercise['exercise_type'],
                    'muscle_group': exercise['muscle_group']
                })

            return {
                'type': 'default',
                'message': "Here's a general workout since you don't have an active plan:",
                'workouts': workout_details
            }

        except Exception as e:
            # Return very basic workout if there's an error
            return {
                'type': 'default',
                'message': "Here's a simple workout to get you started:",
                'workouts': [
                    {'title': 'Push-ups', 'target_sets': 3, 'target_reps': 10},
                    {'title': 'Bodyweight Squats', 'target_sets': 3, 'target_reps': 15},
                    {'title': 'Plank', 'target_sets': 3, 'target_reps': 30}
                ]
            }


class WorkoutEngine:
    def __init__(self, db_connection):
        self.db = db_connection

    def get_workout_details(self, workouts, user_id=1):
        """Get detailed workout information with progress tracking"""
        result_workouts = []
        for workout in workouts:
            self.db.cursor.execute(
                """
                SELECT * FROM exercises WHERE id = ?
                """,
                (workout['exercise_id'],)
            )
            exercise = self.db.cursor.fetchone()

            if exercise:
                workout_detail = dict(workout)
                workout_detail.update({
                    'exercise_type': exercise.get('exercise_type', 'Strength'),
                    'equipment': exercise.get('equipment', ''),
                    'muscle_group': exercise.get('muscle_group', ''),
                    'level': exercise.get('level', '')
                })
                result_workouts.append(workout_detail)

        return result_workouts

    def calculate_suggested_progression(self, workout_history):
        """Calculate suggested progression based on workout history"""
        if not workout_history:
            return {
                'sets': 3,
                'reps': '8-12',
                'weight': 0,
                'notes': 'Start with a weight you can handle for all sets'
            }

        last_workout = workout_history[-1]
        completed_all = last_workout['sets_completed'] >= last_workout['target_sets']
        weight_used = last_workout.get('weight', 0)

        if completed_all:
            return {
                'sets': last_workout['sets_completed'],
                'reps': last_workout['reps_completed'],
                'weight': weight_used * 1.05,  # 5% increase
                'notes': 'Increase weight by 5% from last session'
            }
        else:
            return {
                'sets': last_workout['target_sets'],
                'reps': last_workout['target_reps'],
                'weight': weight_used,
                'notes': 'Maintain current weight and focus on form'
            }
