from flask import Flask, render_template, url_for, flash, redirect, request, session
import sqlite3
import traceback
import hashlib

app = Flask(__name__)
app.secret_key = 'secrete'  # Required for flash messages

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
            con = sqlite3.connect("advweb.db")
            cursor = con.cursor()

            cursor.execute("SELECT first_name FROM student WHERE email = ? AND password = ?", (email, hashed_password))
            user = cursor.fetchone()

            if user:
                session['username'] = user[0]
                return redirect(url_for('home'))
            else:
                flash("Invalid email or password. Please try again.", 'danger')

        except Exception as e:
            print(traceback.format_exc())
            flash("An error occurred during login. Please try again.", 'danger')
        finally:
            con.close()

    return render_template("/student/login.html", title="Student Login")

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
            return render_template("/student/signup.html", title="Student Signup")

        hashed_password = hashlib.md5(password.encode()).hexdigest()

        try:
            con = sqlite3.connect("advweb.db")
            cursor = con.cursor()

            cursor.execute("""
                INSERT INTO student (first_name, last_name, email, phone, address, password) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (first_name, last_name, email, phone, address, hashed_password))

            con.commit()
            return redirect(url_for('student_login'))

        except Exception as e:
            con.rollback()
            print(traceback.format_exc())
            flash("An error occurred during signup. Please try again.", 'danger')
        finally:
            con.close()

    return render_template("/student/signup.html", title="Student Signup")

# Student Home Route
@app.route("/student/home")
def home():
    username = session.get('username')
    return render_template('/student/home.html', username=username)

@app.route("/student/enrollment")
def student_enroll():
    return render_template('/student/enroll.html')

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
            con = sqlite3.connect("advweb.db")
            cursor = con.cursor()

            cursor.execute("SELECT first_name FROM admin WHERE email = ? AND password = ?", (email, hashed_password))
            user = cursor.fetchone()

            if user:
                session['username'] = user[0]
                return redirect(url_for('admin_dashboard'))
            else:
                flash("Invalid email or password. Please try again.", 'danger')

        except Exception as e:
            print(traceback.format_exc())
            flash("An error occurred during login. Please try again.", 'danger')
        finally:
            con.close()

    return render_template("/admin/login.html", title="Admin Login")

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
            return render_template("/admin/signup.html", title="Admin Signup")

        hashed_password = hashlib.md5(password.encode()).hexdigest()

        try:
            con = sqlite3.connect("advweb.db")
            cursor = con.cursor()

            cursor.execute("""
                INSERT INTO admin (first_name, last_name, email, phone, address, password) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (first_name, last_name, email, phone, address, hashed_password))

            con.commit()
            return redirect(url_for('admin_login'))

        except Exception as e:
            con.rollback()
            print(traceback.format_exc())
            flash("An error occurred during signup. Please try again.", 'danger')
        finally:
            con.close()

    return render_template("/admin/signup.html", title="Admin Signup")

# Admin Dashboard Route
@app.route("/admin/dashboard")
def admin_dashboard():
    username = session.get('username')

    # Fetch data for the dashboard
    try:
        con = sqlite3.connect("advweb.db")
        cursor = con.cursor()

        # Fetch total number of students
        cursor.execute("SELECT COUNT(*) FROM student")
        total_students = cursor.fetchone()[0]

        # Fetch total number of courses
        cursor.execute("SELECT COUNT(*) FROM course")
        total_courses = cursor.fetchone()[0]

        # Fetch total number of enrollments
        cursor.execute("SELECT COUNT(*) FROM enrollment")
        total_enrollments = cursor.fetchone()[0]

    except Exception as e:
        print(traceback.format_exc())
        flash("An error occurred while fetching dashboard data.", 'danger')
        total_students = total_courses = total_enrollments = 0
    finally:
        con.close()

    return render_template(
        '/admin/dashboard.html', 
        username=username, 
        total_students=total_students, 
        total_courses=total_courses, 
        total_enrollments=total_enrollments
    )


if __name__ == "__main__":
    app.run(debug=True)
