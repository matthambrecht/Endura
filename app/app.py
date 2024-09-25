import logging

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
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"


## Begin Views
@login_manager.user_loader
def load_user(user_id):
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
    if request.method == "POST":  # On send create user request
        username = request.form["username"].lower()
        password = request.form["password"]

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
