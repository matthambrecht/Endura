import logging
import datetime

from sqlalchemy import Text
from flask_toastr import Toastr
from flask import Flask, request, redirect, url_for, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    UserMixin,
    LoginManager,
    login_required,
    current_user,
    login_user,
    logout_user,
)
from flask_bcrypt import Bcrypt
from flask.logging import logging

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///endura.db"
app.config["SECRET_KEY"] = "super_secret_endura_key"
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)
toastr = Toastr(app)
toastr.init_app(app)
app.logger.setLevel(logging.INFO)

# Database Schemas
class User(UserMixin, db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True)
    username = db.Column(
        db.String(64),
        unique=True,
        nullable=False)
    password_hash = db.Column(
        db.String(128),
        nullable=False)
    profile = db.relationship(
        'Profile',
        backref='user',
        uselist=False)

    def __repr__(self):
        return f"<User {self.id}>"


class Profile(db.Model):
    __tablename__ = "profiles"

    id = db.Column(
        db.Integer,
        primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False)

    # Some default user stats (if null we need to disable the caloric
    # calculator)
    weight = db.Column(
        db.Float,
        nullable=True)
    height = db.Column(
        db.Float,
        nullable=True)
    age = db.Column(
        db.Integer,
        nullable=True)
    gender = db.Column(
        Text,
        nullable=True)

    # Many Workouts -> One Profile
    workouts = db.relationship(
        'Workout',
        backref='workout',
        lazy=True)

    def __repr__(self):
        return f"<Profile {self.user_id}>"


class Workout(db.Model):
    __tablename__ = 'workouts'

    id = db.Column(
        db.Integer,
        primary_key=True)
    day = db.Column(
        db.String(8),
        nullable=False)  # Format MMDDYYYY
    profile_id = db.Column(
        db.Integer,
        db.ForeignKey('profiles.id'),
        nullable=False)

    # Many Exercises -> One Workout
    exercises = db.relationship(
        'Exercise',
        backref='workout',
        lazy=True)

    def __repr__(self):
        return f"<Workout {self.name}>"


class Exercise(db.Model):
    __tablename__ = 'exercises'

    id = db.Column(
        db.Integer,
        primary_key=True)
    name = db.Column(
        db.String(100),
        nullable=False)
    workout_type = db.Column(
        db.String(10),
        nullable=False)
    workout_id = db.Column(
        db.Integer,
        db.ForeignKey('workouts.id'),
        nullable=False)

    __mapper_args__ = {
        'polymorphic_on': workout_type,
        'polymorphic_identity': 'exercise',
    }

    def __repr__(self):
        return f"<Exercise {self.name} {self.type}>"


class Lift(Exercise):
    __tablename__ = 'lifts'

    id = db.Column(
        db.Integer,
        db.ForeignKey('exercises.id'),
        primary_key=True)
    weight = db.Column(
        db.Float,
        nullable=False)
    sets = db.Column(
        db.Integer,
        nullable=False)
    reps = db.Column(
        db.Integer,
        nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'lift',
    }

    def __repr__(self):
        return f"<Lift {self.name} {self.weight} {self.reps} x {self.sets}>"


class Cardio(Exercise):
    __tablename__ = 'cardios'

    id = db.Column(
        db.Integer,
        db.ForeignKey('exercises.id'),
        primary_key=True)
    duration = db.Column(
        db.Integer,
        nullable=False)  # Duration in minutes

    __mapper_args__ = {
        'polymorphic_identity': 'cardio',
    }

    def __repr__(self):
        return f"<Cardio {self.name} {self.duration}>"


# Helper Functions
@app.route("/api/create_workout", methods=["POST"])
@login_required
def create_workout():  # Action for the create workout button
    now = datetime.datetime.now()
    day = now.strftime("%Y%m%d")

    if not Workout.query.filter_by(day=day,
                                   profile_id=current_user.id).first():
        workout = Workout(day=day, profile_id=current_user.id)
        db.session.add(workout)
        db.session.commit()

        return {"msg": "Created a new workout for today", "status": 200}
    else:
        return {
            "msg": "You've already created a workout for today",
            "status": 500}


@app.route("/api/create_exercise", methods=["POST"])
@login_required
def create_exercise():
    data = request.json
    workout_id = data.get("workout_id")
    exercise_name = data.get("name")
    workout_type = data.get("workout_type").lower()

    if not exercise_name:
        return {"msg": "An exercise name must be provided", "status": 500}

    profile = Profile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return {"msg": "User profile not found", "status": 404}

    workout = Workout.query.filter_by(
        id=workout_id, profile_id=profile.id).first()
    if not workout:
        return {
            "msg": "Workout not found or unauthorized access",
            "status": 404}

    if workout_type == "lift":
        if not ((weight := data.get("weight")) and
                (sets := data.get("sets")) and
                (reps := data.get("reps"))):
            return {
                "msg": "Weight, sets, and reps are required for lifts",
                "status": 400}

        exercise = Lift(
            name=exercise_name,
            workout_type=workout_type,
            workout_id=workout_id,
            weight=weight,
            sets=sets,
            reps=reps
        )
    elif workout_type == "cardio":
        if not (duration := data.get("duration")):
            return {
                "msg": "Duration is required for cardio exercises",
                "status": 400}

        exercise = Cardio(
            name=exercise_name,
            workout_type=workout_type,
            workout_id=workout_id,
            duration=duration
        )
    else:
        return {"msg": "Invalid workout type", "status": 400}

    db.session.add(exercise)
    db.session.commit()
    return {
        "msg": f"Exercise '{exercise_name}' added to workout {workout_id}",
        "status": 200}


@app.route("/api/update_exercise", methods=["POST"])
@login_required
def update_exercise():
    data = request.json
    exercise_id = data.get("exercise_id")
    exercise_name = data.get("exercise_name")
    workout_type = data.get("workout_type").lower()
    exercise = Exercise.query.get(exercise_id)

    if not exercise:
        return {"msg": "Exercise not found", "status": 404}

    if not exercise_name:
        return {"msg": "An exercise name must be provided", "status": 500}

    exercise.name = exercise_name
    profile = Profile.query.filter_by(user_id=current_user.id).first()

    if not profile or exercise.workout.profile_id != profile.id:
        return {"msg": "Unauthorized access to this exercise", "status": 403}

    if workout_type == "lift":
        if not ((weight := data.get("weight"))
                and (sets := data.get("sets"))
                and (reps := data.get("reps"))):
            return {
                "msg": "Weight, sets, and reps are required for lifts",
                "status": 400}

        exercise.weight = weight
        exercise.sets = sets
        exercise.reps = reps
    elif workout_type == "cardio":
        if not (duration := data.get("duration")):
            return {
                "msg": "Duration is required for cardio exercises",
                "status": 400}

        exercise.duration = duration
    else:
        return {"msg": "Invalid workout type", "status": 400}

    db.session.commit()
    return {
        "msg": f"Exercise '{exercise_name}' updated successfully",
        "status": 200}


@app.route("/api/delete_exercise", methods=["POST"])
@login_required
def delete_exercise():
    data = request.json
    exercise_id = data.get("exercise_id")

    exercise = Exercise.query.get(exercise_id)
    if not exercise:
        return {"msg": "Exercise not found", "status": 404}

    profile = Profile.query.filter_by(user_id=current_user.id).first()
    if not profile or exercise.workout.profile_id != profile.id:
        return {"msg": "Unauthorized access to this exercise", "status": 403}

    db.session.delete(exercise)
    db.session.commit()
    return {"msg": "Exercise deleted successfully", "status": 200}


@app.route("/api/delete_workout", methods=["POST"])
@login_required
def delete_workout():
    data = request.json
    workout_id = data.get("workout_id")

    workout = Workout.query.get(workout_id)
    if not workout:
        return {"msg": "Workout not found", "status": 404}

    profile = Profile.query.filter_by(user_id=current_user.id).first()
    if not profile or workout.profile_id != profile.id:
        return {"msg": "Unauthorized access to this workout", "status": 403}

    db.session.delete(workout)
    db.session.commit()
    return {
        "msg": "Workout and associated exercises deleted successfully",
        "status": 200}


def get_all_workouts():
    profile = Profile.query.filter_by(user_id=current_user.id).first()

    if not profile:
        return {"error": "You must create a profile first to create workouts"}

    workouts = Workout.query.filter_by(
        profile_id=profile.id).order_by(
        Workout.day.desc()).all()

    return [{
        "id": workout.id,
        "day": workout.day,
        "profile_id": workout.profile_id,
        "exercises": [
            {
                "id": exercise.id,
                "name": exercise.name,
                "workout_type": exercise.workout_type,
                "weight": getattr(exercise, 'weight', None),
                "sets": getattr(exercise, 'sets', None),
                "reps": getattr(exercise, 'reps', None),
                "duration": getattr(exercise, 'duration', None),
            }
            for exercise in workout.exercises
        ]
    } for workout in workouts]


# Begin Utils
def get_profile():
    profile = Profile.query.filter_by(user_id=current_user.id).first()

    if profile:
        return {
            "feet": int(profile.height // 12) if profile.height else None,
            "inches": int(profile.height % 12) if profile.height else None,
            "weight": profile.weight if profile.weight else None,
            "age": int(profile.age) if profile.age else None,
            "gender": profile.gender if profile.gender else None,
        }
    else:
        return None
# End Utils

# Begin Views
@login_manager.user_loader
def load_user(user_id: int):
    return User.query.get(int(user_id))


@app.route("/")
def dashboard():
    if current_user.is_authenticated:
        return render_template("dashboard.html", workouts=get_all_workouts())
    else:
        return redirect(url_for("login"))
# End Views

# Begin Account Management Methods
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        try:
            feet = int(request.form["feet"])
            if feet < 3 or feet > 8:
                flash("Feet must be between 3 and 8", 'error')
                return redirect(url_for("profile"))
            inches = int(request.form["inches"])
            if inches < 0 or inches > 11:
                flash("Inches must be between 0 and 11", 'error')
                return redirect(url_for("profile"))
            age = int(request.form["age"])
            if age < 5 or age > 100:
                flash("Age must be between 5 and 100", 'error')
                return redirect(url_for("profile"))
            weight = float(request.form["weight"])
            if weight < 45 or weight > 600:
                flash("Enter Valid Weight in Lbs", 'error')
                return redirect(url_for("profile"))
            gender = request.form["gender"]
            if gender not in ["M", "F"]:
                flash("Gender must be M or F", 'error')
                return redirect(url_for("profile"))

            profile = get_profile()

            if profile:     # Update
                profile = Profile.query.filter_by(
                    user_id=current_user.id).first()
                profile.height = feet * 12 + inches
                profile.weight = weight
                profile.age = age
                profile.gender = gender
            else:   # Create
                profile = Profile(
                    user_id=current_user.id,
                    height=feet * 12 + inches,
                    weight=weight,
                    age=age,
                    gender=gender
                )

            db.session.add(profile)
            db.session.commit()

            flash("Profile updated successfully", 'success')
        except (ValueError, TypeError):
            flash(
                f"Make sure profile values are of the proper type prior to submitting",
                'error')
        except Exception as e:
            app.logger.warning(e)
            flash(f"We ran across an issue on our end", 'error')

    return render_template("profile.html", profile=get_profile())


@app.route("/update_password", methods=["POST"])
def update_password():
    if request.method == "POST":
        old_password = request.form["old_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]
        user = User.query.filter_by(id=current_user.id).first()

        if user and bcrypt.check_password_hash(
                user.password_hash, old_password):
            if new_password != confirm_password:
                flash(f"Passwords do not match", 'error')
            elif len(new_password) < 2 or len(new_password) > 16:
                flash(f"Passwords must be between 2 and 16 characters", 'error')
            else:
                user.password_hash = bcrypt.generate_password_hash(
                    new_password).decode("utf-8")
                db.session.add(user)
                db.session.commit()

                flash(f"Password changed successfully", 'success')
        else:
            flash(f"The old password is incorrect", 'error')

    return redirect(url_for('manage_account'))


@app.route("/manage_account")
def manage_account():
    return render_template("manage_account.html")


# Create user page and endpoint
@app.route("/create_user", methods=["GET", "POST"])
def create_user():
    if request.method == "POST":  # On send create user request
        username = request.form["username"].lower()
        password = request.form["password"]

        if len(username) > 16 or len(password) > 16:
            flash(
                "Username and password must be shorter than 16 characters",
                "error")
        if not User.query.filter_by(username=username).first():
            password_hash = bcrypt.generate_password_hash(
                password).decode("utf-8")

            query = User(username=username, password_hash=password_hash)
            db.session.add(query)
            db.session.commit()

            profile = Profile(user_id=query.id)
            db.session.add(profile)
            db.session.commit()

            flash("Account created!", 'success')
            return redirect(url_for("dashboard"))
        else:
            flash("Username taken!", 'error')

    return render_template("create_user.html")


@app.route("/login", methods=["GET", "POST"])  # Login page and endpoint
def login():
    if request.method == "POST":
        username = request.form["username"].lower()
        password = request.form["password"]

        if len(username) > 16 or len(password) > 16:
            flash(
                "Username and password must be shorter than 16 characters",
                "error")
            return render_template("login.html")

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            flash("Logged in!", 'success')
            return redirect(url_for("dashboard"))
        else:
            flash("Account doesn't exist or incorrect password", 'error')

    return render_template("login.html")


@app.route("/logout")  # Logout endpoint
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))
# End Account Management Methods


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
