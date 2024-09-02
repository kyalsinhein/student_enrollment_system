from flask import Flask, render_template, url_for, flash, redirect, request, session
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import hashlib
import traceback
from dbconn import query_db, execute_db

app = Flask(__name__)
app.secret_key = 'secrete'  # Required for flash messages

# Configuration for file uploads
upload_folder = os.path.join('static', 'images', 'uploads')
app.config['UPLOAD_FOLDER'] = upload_folder

# Default Route to Choose User Type
@app.route("/", methods=["GET", "POST"])
def choose_user_type():
    if request.method == "POST":
        user_type = request.form.get('user_type')

        if user_type == "student":
            return redirect(url_for('student_login'))
        elif user_type == "admin":
            return redirect(url_for('admin_login'))

    return render_template("choose_user.html", title="Choose User Type")

# Student Login Route
@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = hashlib.md5(password.encode()).hexdigest()

        try:
            user = query_db("SELECT first_name FROM student WHERE email = ? AND password = ?", (email, hashed_password), one=True)

            if user:
                session['username'] = user[0]
                return redirect(url_for('home'))
            else:
                flash("Invalid email or password. Please try again.", 'danger')

        except Exception as e:
            print(traceback.format_exc())
            flash("An error occurred during login. Please try again.", 'danger')

    return render_template("student/login.html", title="Student Login")

# Student Signup Route
@app.route("/student/signup", methods=["GET", "POST"])
def student_signup():
    if request.method == "POST":
        first_name = request.form.get('fname')
        last_name = request.form.get('lname')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        password = request.form.get('password')
        confirm_password = request.form.get('cpassword')

        if not password or not confirm_password or password != confirm_password:
            flash("Passwords do not match or are missing. Please try again.", 'danger')
            return render_template("student/signup.html", title="Student Signup")

        hashed_password = hashlib.md5(password.encode()).hexdigest()

        try:
            execute_db("""
                INSERT INTO student (first_name, last_name, email, phone, address, password) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (first_name, last_name, email, phone, address, hashed_password))

            return redirect(url_for('student_login'))

        except Exception as e:
            print(traceback.format_exc())
            flash("An error occurred during signup. Please try again.", 'danger')

    return render_template("student/signup.html", title="Student Signup")

# Student Home Route
@app.route("/student/home")
def home():
    username = session.get('username')
    return render_template("student/home.html", username=username)

# View Profile Route
@app.route("/student/profile")
def view_profile():
    username = session.get('username')

    if not username:
        return redirect(url_for('student_login'))

    try:
        profile = query_db("SELECT first_name, last_name, email, phone, address FROM student WHERE first_name = ?", (username,), one=True)

        if not profile:
            return redirect(url_for('home'))

    except Exception as e:
        print(traceback.format_exc())
        profile = {}
        
    return render_template("student/profile.html", profile=profile, username=username)

# Edit Profile Route
@app.route("/student/profile/edit", methods=["GET", "POST"])
def edit_profile():
    username = session.get('username')

    if not username:
        return redirect(url_for('student_login'))

    if request.method == "POST":
        first_name = request.form.get('fname')
        last_name = request.form.get('lname')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')

        try:
            execute_db("""
                UPDATE student 
                SET first_name = ?, last_name = ?, email = ?, phone = ?, address = ?
                WHERE first_name = ?
            """, (first_name, last_name, email, phone, address, username))

            session['username'] = first_name  # Update session with the new name if changed
            return redirect(url_for('view_profile'))

        except Exception as e:
            print(traceback.format_exc())

    else:
        try:
            profile = query_db("SELECT first_name, last_name, email, phone, address FROM student WHERE first_name = ?", (username,), one=True)

            if not profile:
                return redirect(url_for('home'))

        except Exception as e:
            print(traceback.format_exc())
            profile = {}

        return render_template("student/edit_profile.html", profile=profile, username=username)

@app.route('/student/courses')
def view_courses():
    username = session.get('username')
    try:
        courses = query_db("SELECT name, image, description FROM course")
    except Exception as e:
        print(traceback.format_exc())
        courses = []
    return render_template('student/courses.html', courses=courses, username=username)

@app.route("/student/enrollment", methods=["GET", "POST"])
def student_enroll():
    username = session.get('username')

    if not username:
        return redirect(url_for('student_login'))

    if request.method == "POST":
        course_id = request.form.get('course_id')
        
        if not course_id:
            return redirect(url_for('student_enroll'))

        try:
            student_id_row = query_db("SELECT id FROM student WHERE first_name = ?", (username,), one=True)
            if not student_id_row:
                return redirect(url_for('student_enroll'))
            student_id = student_id_row[0]

            execute_db("""
                INSERT INTO enrollment (student_id, course_id, enroll_date) 
                VALUES (?, ?, ?)
            """, (student_id, course_id, datetime.now().strftime('%Y-%m-%d')))

            return redirect(url_for('home'))

        except Exception as e:
            print(traceback.format_exc())

    try:
        student = query_db("SELECT first_name, last_name FROM student WHERE first_name = ?", (username,), one=True)
        full_name = f"{student[0]} {student[1]}" if student else "N/A"

        courses = query_db("SELECT id, name FROM course")

    except Exception as e:
        print(f"Exception during GET request: {e}")
        full_name = "N/A"
        courses = []

    return render_template("student/enroll.html", full_name=full_name, courses=courses, username=username)

# Student Logout Route
@app.route("/student/logout")
def student_logout():
    session.pop('username', None)
    return redirect(url_for('choose_user_type'))

# Admin Login Route
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = hashlib.md5(password.encode()).hexdigest()

        try:
            user = query_db("SELECT first_name FROM admin WHERE email = ? AND password = ?", (email, hashed_password), one=True)

            if user:
                session['username'] = user[0]
                return redirect(url_for('admin_dashboard'))
            else:
                flash("Invalid email or password. Please try again.", 'danger')

        except Exception as e:
            print(traceback.format_exc())
            flash("An error occurred during login. Please try again.", 'danger')

    return render_template("admin/login.html", title="Admin Login")

# Admin Signup Route (if needed)
@app.route("/admin/signup", methods=["GET", "POST"])
def admin_signup():
    if request.method == "POST":
        first_name = request.form.get('fname')
        last_name = request.form.get('lname')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        password = request.form.get('password')
        confirm_password = request.form.get('cpassword')

        if not password or not confirm_password or password != confirm_password:
            flash("Passwords do not match or are missing. Please try again.", 'danger')
            return render_template("admin/signup.html", title="Admin Signup")

        hashed_password = hashlib.md5(password.encode()).hexdigest()

        try:
            execute_db("""
                INSERT INTO admin (first_name, last_name, email, phone, address, password) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (first_name, last_name, email, phone, address, hashed_password))

            return redirect(url_for('admin_login'))

        except Exception as e:
            print(traceback.format_exc())
            flash("An error occurred during signup. Please try again.", 'danger')

    return render_template("admin/signup.html", title="Admin Signup")

# Admin Dashboard Route
@app.route("/admin/dashboard")
def admin_dashboard():
    username = session.get('username')

    try:
        total_students = query_db("SELECT COUNT(*) FROM student", one=True)[0]
        total_courses = query_db("SELECT COUNT(*) FROM course", one=True)[0]
        total_enrollments = query_db("SELECT COUNT(*) FROM enrollment", one=True)[0]

    except Exception as e:
        print(traceback.format_exc())
        total_students = total_courses = total_enrollments = 0

    return render_template(
        "admin/dashboard.html", 
        username=username, 
        total_students=total_students, 
        total_courses=total_courses, 
        total_enrollments=total_enrollments
    )

@app.route("/admin/courses", methods=["GET"])
def admin_view_courses():
    username = session.get('username')
    courses = query_db("SELECT * FROM course")
    
    courses = [
        {
            "id": course[0],
            "name": course[1],
            "image": course[2],
            "description": course[3],
            "credits": course[4],
            "lecturer": course[5],
        }
        for course in courses
    ]

    return render_template("admin/courses.html", courses=courses, username=username)

@app.route("/admin/course/add", methods=["GET", "POST"])
def add_course():
    username = session.get('username')
    if request.method == "POST":
        name = request.form['name']
        description = request.form['description']
        credits = request.form['credit']
        lecturer = request.form['lecturer']
        cfile = request.files['cimage']
        filename = secure_filename(cfile.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        cfile.save(file_path)
        try:
            execute_db("INSERT INTO course (name, image, description, credits, lecturer) VALUES (?, ?, ?, ?, ?)",
                       (name, filename, description, credits, lecturer))
            # flash("Course added successfully.", 'success')  # Flash removed
            return redirect(url_for('admin_view_courses'))
        except Exception as e:
            print(traceback.format_exc())

    return render_template("admin/addcourse.html", username=username)

@app.route("/admin/courses/delete/<int:id>", methods=["POST"])
def delete_course(id):
    try:
        # Check if the course is enrolled
        enrollment_count = query_db("SELECT COUNT(*) FROM enrollment WHERE course_id = ?", (id,), one=True)[0]
        
        if enrollment_count > 0:
            flash("Cannot delete the course as it is currently enrolled in.", 'danger')
        else:
            execute_db("DELETE FROM course WHERE id = ?", (id,))
            flash("Course deleted successfully.", 'success')

    except Exception as e:
        print(traceback.format_exc())
        flash("An error occurred while trying to delete the course. Please try again.", 'danger')

    return redirect(url_for('admin_view_courses'))


# Admin Logout Route
@app.route("/admin/logout")
def admin_logout():
    session.pop('username', None)
    return redirect(url_for('choose_user_type'))

if __name__ == "__main__":
    app.run(debug=True)
