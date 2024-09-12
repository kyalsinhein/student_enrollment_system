from flask import Flask, render_template, url_for, flash, redirect, request, session
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import hashlib
import traceback
from functools import wraps  # Added for custom decorators
from dbcontroller import query_db, execute_db
import time

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
            user = query_db("SELECT id,first_name FROM student WHERE email = ? AND password = ?", (email, hashed_password), one=True)

            if user:
                session['uid'] = user[0]
                session['username'] = user[1]
                session['user_type'] = 'student' 
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
    if 'username' not in session or session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
    
    username = session.get('username')
    return render_template("student/home.html", username=username)

# View Profile Route
@app.route("/student/profile")
def view_profile():
    if 'username' not in session or session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
    username = session.get('username')

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
    if 'username' not in session or session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
    username = session.get('username')

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
    if 'username' not in session or session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
    username = session.get('username')
    
    # Get the search query from the request arguments
    search_query = request.args.get('search', '')
    
    try:
        # Modify the SQL query to include a search condition if a search query is provided
        if search_query:
            # Use a parameterized query to prevent SQL injection
            courses = query_db("SELECT id, name, image, description FROM course WHERE name LIKE ?", ('%' + search_query + '%',))
        else:
            courses = query_db("SELECT id, name, image, description FROM course")
    except Exception as e:
        print(traceback.format_exc())
        courses = []
    
    return render_template('student/courses.html', courses=courses, username=username)


@app.route('/student/courses/detail/<int:course_id>')
def course_detail(course_id):
    if 'username' not in session or session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
    username = session.get('username')
    try:
        course = query_db("SELECT name, image, description, credits, lecturer FROM course WHERE id = ?", (course_id,), one=True)
        if course:
            return render_template('student/course_detail.html', course=course, username=username)
        else:
            return "Course not found", 404
    except Exception as e:
        print(traceback.format_exc())
        return "An error occurred while fetching course details.", 500


@app.route("/student/enrollment", methods=["GET", "POST"])
def student_enroll():
    if 'username' not in session or session.get('user_type') != 'student':
        return redirect(url_for('student_login'))

    username = session.get('username')

    if request.method == "POST":
        course_id = request.form.get('course_id')
        
        if not course_id:
            flash("Please select a course.", "warning")
            return redirect(url_for('student_enroll'))

        try:
            # Fetch the student ID based on the username
            student_id_row = query_db("SELECT id FROM student WHERE first_name = ?", (username,), one=True)
            if not student_id_row:
                return redirect(url_for('student_enroll'))
            student_id = student_id_row[0]

            # Check if the student is already enrolled in the selected course
            existing_enrollment = query_db("""
                SELECT * FROM enrollment WHERE student_id = ? AND course_id = ?
            """, (student_id, course_id), one=True)

            if existing_enrollment:
                flash("You are already enrolled in this course.", "warning")
                return redirect(url_for('student_enroll'))

            # Fetch the schedule of the course the student is trying to enroll in
            new_course_schedule = query_db("""
                SELECT day_of_week FROM schedule WHERE course_id = ?
            """, (course_id,), one=True)

            if not new_course_schedule:
                flash("Course schedule not found.", "danger")
                return redirect(url_for('student_enroll'))

            # Split the days of the new course into a list
            new_days = new_course_schedule[0].split(', ')

            # Fetch the schedule of courses the student is already enrolled in
            existing_schedule = query_db("""
                SELECT sc.day_of_week
                FROM schedule sc
                JOIN enrollment e ON sc.course_id = e.course_id
                WHERE e.student_id = ?
            """, (student_id,))

            # Split the days of the existing courses into a list
            for existing_schedule_entry in existing_schedule:
                existing_days = existing_schedule_entry[0].split(', ')
                
                # Check for any overlapping days
                for day in new_days:
                    if day in existing_days:
                        flash(f"You cannot enrolled this course! You have another class in these days!", "danger")
                        return redirect(url_for('student_enroll'))

            # If no conflict, proceed with enrollment
            execute_db("""
                INSERT INTO enrollment (student_id, course_id, enroll_date) 
                VALUES (?, ?, ?)
            """, (student_id, course_id, datetime.now().strftime('%Y-%m-%d')))

            flash("Enrollment successful!", "success")
            return redirect(url_for('home'))

        except Exception as e:
            print(traceback.format_exc())
            flash("An error occurred during enrollment.", "danger")
            return redirect(url_for('student_enroll'))

    try:
        # Fetch student details
        student = query_db("SELECT first_name, last_name FROM student WHERE first_name = ?", (username,), one=True)
        full_name = f"{student[0]} {student[1]}" if student else "N/A"

        # Fetch available courses
        courses = query_db("SELECT id, name FROM course")

    except Exception as e:
        print(f"Exception during GET request: {e}")
        full_name = "N/A"
        courses = []

    return render_template("student/enroll.html", full_name=full_name, courses=courses, username=username)


@app.route('/student/records')
def view_enrollment_records():
    if 'username' not in session or session.get('user_type') != 'student':
        return redirect(url_for('student_login'))

    student_id = session.get('uid')  # Get student ID from session

    if not student_id:
        return redirect(url_for('home'))

    try:
        # Query to get enrollment records along with course names
        enrollments = query_db("""
            SELECT e.student_id, s.first_name, c.name AS course_name, e.enroll_date
            FROM enrollment e
            JOIN student s ON e.student_id = s.id
            JOIN course c ON e.course_id = c.id
            WHERE e.student_id = ?
        """, (student_id,))

        # Query to get the timetable of the current student's enrolled subjects
        timetable = query_db("""
            SELECT sc.course_id, c.name AS course_name, sc.day_of_week, sc.start_time, sc.end_time
            FROM schedule sc
            JOIN course c ON sc.course_id = c.id
            WHERE sc.course_id IN (
                SELECT e.course_id FROM enrollment e WHERE e.student_id = ?
            )
            ORDER BY sc.day_of_week, sc.start_time
        """, (student_id,))
        
    except Exception as e:
        print(traceback.format_exc())
        enrollments = []
        timetable = []

    return render_template('student/records.html', 
                           enrollments=enrollments, 
                           timetable=timetable, 
                           username=session.get('username'))



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
            user = query_db("SELECT id,first_name FROM admin WHERE email = ? AND password = ?", (email, hashed_password), one=True)

            if user:
                session['adminuid'] = user[0]
                session['username'] = user[1]
                session['user_type'] = 'admin' 
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

@app.route("/admin/dashboard")
def admin_dashboard():
    if 'username' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))

    username = session.get('username')

    try:
        # Fetch the total counts
        total_students = query_db("SELECT COUNT(*) FROM student", one=True)[0]
        total_courses = query_db("SELECT COUNT(*) FROM course", one=True)[0]
        total_enrollments = query_db("SELECT COUNT(*) FROM enrollment", one=True)[0]

        # Fetch enrolled students' data
        enrolled_students = query_db("""
            SELECT 
                student.id AS student_id, 
                student.first_name || ' ' || student.last_name AS student_name, 
                course.name AS course_name, 
                enrollment.enroll_date 
            FROM enrollment 
            JOIN student ON enrollment.student_id = student.id
            JOIN course ON enrollment.course_id = course.id
        """)

        # Print the data to debug
        print("Enrolled students:", enrolled_students)

    except Exception as e:
        print(traceback.format_exc())
        total_students = total_courses = total_enrollments = 0
        enrolled_students = []

    return render_template(
        "admin/dashboard.html", 
        username=username, 
        total_students=total_students, 
        total_courses=total_courses, 
        total_enrollments=total_enrollments, 
        enrolled_students=enrolled_students  # Pass the enrolled students data
    )

    
@app.route("/admin/courses", methods=["GET"])
def admin_view_courses():
    if 'username' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))

    username = session.get('username')
    page = int(request.args.get('page', 1))  # Get current page from query parameter, default to 1
    per_page = 6  # Number of courses per page

    # Get total count of courses
    total_courses = query_db("SELECT COUNT(*) FROM course")[0][0]

    # Calculate pagination values
    offset = (page - 1) * per_page
    total_pages = (total_courses + per_page - 1) // per_page  # Ceiling division to get total pages

    # Retrieve courses for the current page
    courses = query_db("SELECT * FROM course LIMIT ? OFFSET ?", (per_page, offset))

    courses_list = []
    for course in courses:
        course_dict = {
            "id": course[0],
            "name": course[1],
            "image": course[2],
            "description": course[3],
            "credits": course[4],
            "lecturer": course[5],
        }
        courses_list.append(course_dict)

    return render_template("admin/courses.html", courses=courses_list, username=username, time=time, page=page, total_pages=total_pages)




@app.route("/admin/course/add", methods=["GET", "POST"])
def add_course():
    if 'username' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    # Use absolute path
    upload_folder = os.path.abspath(os.path.join('static', 'images', 'courses'))
    app.config['UPLOAD_FOLDER'] = upload_folder

    # Ensure the upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    username = session.get('username')
    if request.method == "POST":
        name = request.form['name']
        description = request.form['description']
        credits = request.form['credit']
        lecturer = request.form['lecturer']
        cfile = request.files['cimage']
        filename = secure_filename(cfile.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Debugging print statements
        print("Upload folder path:", app.config['UPLOAD_FOLDER'])
        print("File path:", file_path)
        print("Directory exists:", os.path.exists(app.config['UPLOAD_FOLDER']))

        try:
            cfile.save(file_path)
            execute_db("INSERT INTO course (name, image, description, credits, lecturer) VALUES (?, ?, ?, ?, ?)",
                       (name, filename, description, credits, lecturer))
            return redirect(url_for('admin_view_courses'))
        except Exception as e:
            print(traceback.format_exc())

    return render_template("admin/addcourse.html", username=username)

@app.route("/admin/courses/edit/<int:course_id>", methods=["GET", "POST"])
def edit_course(course_id):
    if 'username' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))

    # Fetch the current course details from the database
    try:
        course = query_db("SELECT id, name, image, description, credits, lecturer FROM course WHERE id = ?", (course_id,), one=True)
        
        if not course:
            flash("Course not found.", 'danger')
            return redirect(url_for('admin_view_courses'))
        
    except Exception as e:
        print(traceback.format_exc())
        flash("Error fetching course details.", 'danger')
        return redirect(url_for('admin_view_courses'))

    # Use absolute path for uploads
    upload_folder = os.path.abspath(os.path.join('static', 'images', 'courses'))
    app.config['UPLOAD_FOLDER'] = upload_folder

    # Ensure the upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # If form is submitted, update the course details
    if request.method == "POST":
        name = request.form['name']
        description = request.form['description']
        credits = request.form['credit']
        lecturer = request.form['lecturer']
        cfile = request.files['cimage']
        
        # If a new image is uploaded
        if cfile and cfile.filename:
            filename = secure_filename(cfile.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                cfile.save(file_path)
            except Exception as e:
                print(traceback.format_exc())
                flash("Error uploading image.", 'danger')
                return render_template("admin/editcourse.html", course=course)
        else:
            # If no new image is uploaded, use the old one
            filename = course[2]

        try:
            # Update the course in the database
            execute_db("""
                UPDATE course 
                SET name = ?, image = ?, description = ?, credits = ?, lecturer = ?
                WHERE id = ?
            """, (name, filename, description, credits, lecturer, course_id))
            
            flash("Course updated successfully!", 'success')
            return redirect(url_for('admin_view_courses'))

        except Exception as e:
            print(traceback.format_exc())
            flash("Error updating course details.", 'danger')

    return render_template("admin/editcourse.html", course=course)


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

@app.route("/admin/students", methods=["GET"])
def admin_view_students():
    if 'username' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))

    username = session.get('username')
    
    # Get page number from query parameters, default to 1 if not present
    page = int(request.args.get('page', 1))
    per_page = 10  # Number of rows per page
    
    # Query the total number of students
    total_students_query = "SELECT COUNT(*) FROM student"
    total_students = query_db(total_students_query)[0][0]
    
    # Calculate offset for the query
    offset = (page - 1) * per_page
    
    # Query the students for the current page
    students_query = f"""
        SELECT * FROM student
        LIMIT {per_page} OFFSET {offset}
    """
    students = query_db(students_query)
    
    students_list = []
    for student in students:
        student_dict = {
            "id": student[0],
            "fname": student[1],
            "lname": student[2],
            "email": student[3],
            "phone": student[4],
            "address": student[5],
        }
        students_list.append(student_dict)

    # Calculate total pages
    total_pages = (total_students + per_page - 1) // per_page
    
    return render_template(
        "admin/students.html", 
        students=students_list, 
        username=username, 
        time=time,
        current_page=page,
        total_pages=total_pages
    )



@app.route("/admin/student/add", methods=["GET", "POST"])
def add_student():
    if 'username' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))

    username = session.get('username')
    if request.method == "POST":
        fname = request.form['first_name']
        lname = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        password = request.form['password']

        # Hash the password with MD5
        hashed_password = hashlib.md5(password.encode()).hexdigest()

        try:
            execute_db("INSERT INTO student (first_name, last_name, email, phone, address, password) VALUES (?, ?, ?, ?, ?, ?)",
                       (fname, lname, email, phone, address, hashed_password))
            return redirect(url_for('admin_view_students'))
        except Exception as e:
            print(traceback.format_exc())

    return render_template("admin/addstudent.html", username=username)


@app.route("/admin/students/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    if 'username' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))

    # Fetch the current student details from the database
    try:
        student = query_db("SELECT first_name, last_name, email, phone, address FROM student WHERE id = ?", (student_id,), one=True)
        
        if not student:
            flash("Student not found.", 'danger')
            return redirect(url_for('admin_view_students'))
        
    except Exception as e:
        print(traceback.format_exc())
        flash("Error fetching student details.", 'danger')
        return redirect(url_for('admin_view_students'))

    # If form is submitted, update the student details
    if request.method == "POST":
        fname = request.form['first_name']
        lname = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        
        try:
            # Update the student in the database
            execute_db("""
                UPDATE student 
                SET first_name = ?, last_name = ?, email = ?, phone = ?, address = ?
                WHERE id = ?
            """, (fname, lname, email, phone, address, student_id))
            
            flash("Student updated successfully!", 'success')
            return redirect(url_for('admin_view_students'))

        except Exception as e:
            print(traceback.format_exc())
            flash("Error updating student details.", 'danger')

    return render_template("admin/editstudent.html", student=student)



@app.route("/admin/students/delete/<int:id>", methods=["POST"])
def delete_student(id):
    try:

            execute_db("DELETE FROM student WHERE id = ?", (id,))
            flash("Student deleted successfully.", 'success')

    except Exception as e:
        print(traceback.format_exc())
        flash("An error occurred while trying to delete the student. Please try again.", 'danger')

    return redirect(url_for('admin_view_students'))

@app.route("/admin/schedules", methods=["GET"])
def admin_view_schedules():
    if 'username' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))

    # Pagination parameters
    per_page = 10
    page = request.args.get('page', 1, type=int)

    # Fetch all schedules
    schedules = query_db("SELECT * FROM schedule")
    
    # Total number of pages
    total_schedules = len(schedules)
    total_pages = (total_schedules + per_page - 1) // per_page  # Calculate total pages

    # Paginate the schedules
    start = (page - 1) * per_page
    end = start + per_page
    schedules_list = [
        {
            "id": schedule[0],
            "course_id": schedule[1],
            "day_of_week": schedule[2],
            "start_time": schedule[3],
            "end_time": schedule[4]
        }
        for schedule in schedules[start:end]
    ]

    return render_template(
        "admin/schedules.html", 
        schedules=schedules_list, 
        username=session.get('username'), 
        current_page=page, 
        total_pages=total_pages
    )



@app.route("/admin/schedule/add", methods=["GET", "POST"])
def add_schedule():
    if 'username' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))

    username = session.get('username')
    if request.method == "POST":
        course_id = request.form['course_id']
        day_of_week = request.form['day_of_week']
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        try:
            execute_db("INSERT INTO schedule (course_id, day_of_week, start_time, end_time) VALUES (?, ?, ?, ?)",
                       (course_id, day_of_week, start_time, end_time))
            return redirect(url_for('admin_view_schedules'))
        except Exception as e:
            print(traceback.format_exc())
            flash("Error adding schedule.", 'danger')

    return render_template("admin/addschedule.html", username=username)

@app.route("/admin/schedules/edit/<int:schedule_id>", methods=["GET", "POST"])
def edit_schedule(schedule_id):
    if 'username' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))

    if request.method == "POST":
        course_id = request.form['course_id']
        day_of_week = request.form['day_of_week']
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        try:
            execute_db("""
                UPDATE schedule 
                SET course_id = ?, day_of_week = ?, start_time = ?, end_time = ?
                WHERE id = ?
            """, (course_id, day_of_week, start_time, end_time, schedule_id))

            flash("Schedule updated successfully!", 'success')
            return redirect(url_for('admin_view_schedules'))
        except Exception as e:
            print(traceback.format_exc())
            flash("Error updating schedule.", 'danger')

    try:
        schedule = query_db("SELECT course_id, day_of_week, start_time, end_time FROM schedule WHERE id = ?", (schedule_id,), one=True)
        if not schedule:
            flash("Schedule not found.", 'danger')
            return redirect(url_for('admin_view_schedules'))

        # Ensure times are in 24-hour format
        schedule = (
            schedule[0],  # course_id
            schedule[1],  # day_of_week
            schedule[2],  # start_time
            schedule[3]   # end_time
        )
    except Exception as e:
        print(traceback.format_exc())
        flash("Error fetching schedule details.", 'danger')
        return redirect(url_for('admin_view_schedules'))

    return render_template("admin/editschedule.html", schedule=schedule)



@app.route("/admin/schedules/delete/<int:id>", methods=["POST"])
def delete_schedule(id):
    try:
        execute_db("DELETE FROM schedule WHERE id = ?", (id,))
        flash("Schedule deleted successfully.", 'success')

    except Exception as e:
        print(traceback.format_exc())
        flash("Error deleting schedule. Please try again.", 'danger')

    return redirect(url_for('admin_view_schedules'))

@app.route("/admin/enrollmentmgt", methods=["GET"])
def admin_view_enrollment():
    if 'username' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))

    username = session.get('username')
    
    # Get the page number from query parameters, default to 1
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of enrollments per page

    # Query to get total number of enrollments
    total_enrollment = query_db("SELECT COUNT(*) FROM enrollment")[0][0]

    # Fetch enrollment data for the current page with a LIMIT and OFFSET
    offset = (page - 1) * per_page
    enrollment_query = f"SELECT * FROM enrollment LIMIT {per_page} OFFSET {offset}"
    enrollment = query_db(enrollment_query)

    # Convert enrollment data into a list of dictionaries
    enrollment_list = []
    for record in enrollment:
        enrollment_dict = {
            "id": record[0],
            "student_id": record[1],
            "course_id": record[2],
            "enroll_date": record[3],
        }
        enrollment_list.append(enrollment_dict)

    # Calculate total pages
    total_pages = (total_enrollment + per_page - 1) // per_page

    return render_template(
        "admin/enrollmentmgmt.html", 
        enrollment_list=enrollment_list, 
        username=username, 
        current_page=page, 
        total_pages=total_pages, 
        per_page=per_page
    )



@app.route("/admin/enrollment", methods=["GET", "POST"])
def admin_enroll():
    
    if 'username' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    
    if request.method == "POST":
        student_id = request.form.get('student_id')
        course_id = request.form.get('course_id')
        
        if not student_id or not course_id:
            return redirect(url_for('admin_enroll'))

        try:
            # Insert into the enrollment table
            execute_db("""
                INSERT INTO enrollment (student_id, course_id, enroll_date) 
                VALUES (?, ?, ?)
            """, (student_id, course_id, datetime.now().strftime('%Y-%m-%d')))

            return redirect(url_for('admin_view_enrollment'))

        except Exception as e:
            print(traceback.format_exc())

    try:
        # Get students and courses from the database
        students = query_db("SELECT id, first_name, last_name FROM student")
        courses = query_db("SELECT id, name FROM course")

    except Exception as e:
        print(f"Exception during GET request: {e}")
        students = []
        courses = []

    return render_template("admin/enroll.html", students=students, courses=courses)

@app.route("/admin/enrollment/delete/<int:id>", methods=["POST"])
def delete_enrollment(id):
    try:
            execute_db("DELETE FROM enrollment WHERE id = ?", (id,))
            flash("Enrollment deleted successfully.", 'success')

    except Exception as e:
        print(traceback.format_exc())
        flash("An error occurred while trying to delete the course. Please try again.", 'danger')

    return redirect(url_for('admin_view_enrollment'))

# Admin Logout Route
@app.route("/admin/logout")
def admin_logout():
    session.pop('username', None)
    return redirect(url_for('choose_user_type'))

if __name__ == "__main__":
    app.run(debug=True)
