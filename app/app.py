import logging
import datetime

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

    # Some default user stats (if null we need to disable the caloric calculator)
    weight = db.Column(
        db.Float,
        nullable=True)
    height = db.Column(
        db.Float,
        nullable=True)
    age = db.Column(
        db.Integer,
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
        nullable=False) # Format MMDDYYYY
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
def create_workout(): # Action for the create workout button
    now = datetime.datetime.now()
    day = now.strftime("%m%d%Y")

    if not Workout.query.filter_by(day=day).first():
        workout = Workout(day=day)
        db.session.add(workout)
        db.session.commit()
        print("Doesn't Exist")
    else:
        print("Exists")
        return None


## Begin Views
@login_manager.user_loader
def load_user(user_id: int):
    return User.query.get(int(user_id))


@app.route("/")
def dashboard():
    if current_user.is_authenticated:
        return render_template("dashboard.html")
    else:
        return redirect(url_for("login"))
## End Views

## Begin Account Management Methods
@app.route("/create_user", methods=["GET", "POST"])  # Create user page and endpoint
def create_user():
    create_workout()
    if request.method == "POST":  # On send create user request
        username = request.form["username"].lower()
        password = request.form["password"]

        if len(username) > 16 or len(password) > 16:
            flash("Username and password must be shorter than 16 characters", "error")
        if not User.query.filter_by(username=username).first():
            password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

            query = User(username=username, password_hash=password_hash)
            db.session.add(query)
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
            flash("Username and password must be shorter than 16 characters", "error")
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
## End Account Management Methods

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
