import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy import func

from app import db
from app.models import Student


main = Blueprint("main", __name__)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _registration_error():
    student_id = request.form.get("student_id", "").strip()
    full_name = request.form.get(
        "full_name",
        request.form.get("name", ""),
    ).strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not student_id or not full_name or not email or not password:
        return "All fields are required.", None
    if not EMAIL_PATTERN.fullmatch(email):
        return "Enter a valid email address.", None
    if len(password) < 8:
        return "Password must be at least 8 characters.", None
    if Student.query.filter(
        func.lower(Student.student_id) == student_id.lower()
    ).first():
        return "A student account with this student ID already exists.", None
    if Student.query.filter(func.lower(Student.email) == email).first():
        return "A student account with this email address already exists.", None
    return None, (student_id, full_name, email, password)


@main.route("/")
def index():
    student = None
    if "student_id" in session:
        student = Student.query.filter_by(student_id=session["student_id"]).first()
    return render_template("index.html", student=student)


@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        error, values = _registration_error()
        if error:
            flash(error, "error")
            return render_template("register.html")

        student_id, full_name, email, password = values
        student = Student(
            student_id=student_id,
            full_name=full_name,
            email=email,
        )
        student.set_password(password)
        db.session.add(student)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("main.login"))

    return render_template("register.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("email", "").strip()
        if not identifier:
            identifier = request.form.get("student_id", "").strip()
        password = request.form.get("password", "")

        if not identifier or not password:
            flash("Email or student ID and password are required.", "error")
            return render_template("login.html")

        student = Student.query.filter(
            (func.lower(Student.email) == identifier.lower())
            | (func.lower(Student.student_id) == identifier.lower())
        ).first()
        if student is None or not student.check_password(password):
            flash("Invalid email, student ID, or password.", "error")
            return render_template("login.html")

        session.clear()
        session["student_id"] = student.student_id
        session["user_id"] = student.id
        flash("Logged in successfully.", "success")
        return redirect(url_for("main.index"))

    return render_template("login.html")
