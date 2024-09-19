from flask import Flask, render_template, url_for, flash, redirect, request, session
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import hashlib
import traceback
from dbcontroller import query_db, execute_db
import time

app = Flask(__name__)
app.secret_key = 'secrete'  

@app.route("/", methods=["GET", "POST"])
def choose_user_type():
    if request.method == "POST":
        user_type = request.form.get('user_type')

        if user_type == "student":
            return redirect(url_for('student_login'))
        elif user_type == "admin":
            return redirect(url_for('admin_login'))

    return render_template("choose_user.html", title="Choose User Type")

@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = hashlib.md5(password.encode()).hexdigest()

        try:
            user = query_db("SELECT id, first_name FROM student WHERE email = ? AND password = ?", (email, hashed_password))

            if user:  
                user = user[0] 
                session['uid'] = user[0]
                session['first_name'] = user[1]
                session['user_type'] = 'student' 
                return redirect(url_for('home'))
            else:
                flash("Invalid email or password. Please try again.", 'danger')

        except Exception as e:
            print(traceback.format_exc())
            flash("An error occurred during login. Please try again.", 'danger')

    return render_template("student/login.html", title="Student Login")

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

        existing_students = query_db("SELECT * FROM student WHERE email = ?", (email,))
        if existing_students:
            flash("Email is already taken. Please use a different email.", 'danger')
            return render_template("student/signup.html", title="Student Signup")

        hashed_password = hashlib.md5(password.encode()).hexdigest()

        try:
            execute_db("""
                INSERT INTO student (first_name, last_name, phone, email, address, password) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (first_name, last_name, phone, email, address, hashed_password))

            return redirect(url_for('student_login'))

        except Exception as e:
            print(traceback.format_exc())
            flash("An error occurred during signup. Please try again.", 'danger')

    return render_template("student/signup.html", title="Student Signup")


@app.route("/student/home")
def home():
    if 'uid' not in session or session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
    
    first_name = session.get('first_name')
    uid = session.get('uid')
    return render_template("student/home.html", first_name=first_name,uid=uid)

@app.route("/student/profile")
def view_profile():
    if 'uid' not in session or session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
    uid = session.get('uid')
    first_name = session.get('first_name')
    try:
        profile = query_db("SELECT first_name, last_name, email, phone, address FROM student WHERE id = ?", (uid,))
    except Exception as e:
        print(traceback.format_exc())
        profile = {}
        
    return render_template("student/profile.html", profile=profile, first_name=first_name,uid=uid)

@app.route("/student/profile/edit", methods=["GET", "POST"])
def edit_profile():
    if 'uid' not in session or session.get('user_type') != 'student':
        return redirect(url_for('student_login'))

    first_name = session.get('first_name')
    uid = session.get('uid')

    if request.method == "POST":
        first_name = request.form.get('fname')
        last_name = request.form.get('lname')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        password = request.form.get('password')

        try:
            if password:
                execute_db("""
                    UPDATE student 
                    SET first_name = ?, last_name = ?, email = ?, phone = ?, address = ?, password = ?
                    WHERE id = ?
                """, (first_name, last_name, email, phone, address, hashlib.md5(password.encode()).hexdigest(), uid))
            else:
                execute_db("""
                    UPDATE student 
                    SET first_name = ?, last_name = ?, email = ?, phone = ?, address = ?
                    WHERE id = ?
                """, (first_name, last_name, email, phone, address, uid))

            session['first_name'] = first_name 
            return redirect(url_for('view_profile'))

        except Exception as e:
            print(traceback.format_exc())

    else:
        try:
            profile = query_db("SELECT first_name, last_name, email, phone, address FROM student WHERE id = ?", (uid,))

            if not profile:
                return redirect(url_for('home'))

            profile = profile[0] 

        except Exception as e:
            print(traceback.format_exc())
            profile = {}

        return render_template("student/edit_profile.html", profile=profile, first_name=first_name, uid=uid)


@app.route('/student/courses')
def view_courses():
    if 'uid' not in session or session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
    first_name = session.get('first_name')
    uid = session.get('uid')

    search_query = request.args.get('search', '')
    
    try:

        if search_query:

            courses = query_db("SELECT id, name, image, description FROM course WHERE name LIKE ?", ('%' + search_query + '%',))
        else:
            courses = query_db("SELECT id, name, image, description FROM course")
    except Exception as e:
        print(traceback.format_exc())
        courses = []
    
    return render_template('student/courses.html', courses=courses, first_name=first_name,uid=uid)


@app.route('/student/courses/detail/<int:course_id>')
def course_detail(course_id):
    if 'uid' not in session or session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
    first_name = session.get('first_name')
    uid = session.get('uid')
    try:

        course = query_db("SELECT name, image, description, credits, lecturer FROM course WHERE id = ?", (course_id,))

        if course:
            course = course[0]  
            return render_template('student/course_detail.html', course=course, first_name=first_name,uid=uid)
        else:
            return "Course not found", 404
    except Exception as e:
        print(traceback.format_exc())
        return "An error occurred while fetching course details.", 500

@app.route("/student/enrollment", methods=["GET", "POST"])
def student_enroll():
    if 'uid' not in session or session.get('user_type') != 'student':
        return redirect(url_for('student_login'))


    uid = session.get('uid')
    first_name = session.get('first_name')

    try:
  
        student = query_db("SELECT first_name, last_name FROM student WHERE id = ?", (uid,))
        if not student:
            flash("Student not found.", "danger")
            return redirect(url_for('student_enroll'))
        

        fullname = f"{student[0][0]} {student[0][1]}"
    except Exception as e:
        print(traceback.format_exc())
        flash("An error occurred while fetching student details.", "danger")
        fullname = "Unknown"

    if request.method == "POST":
        course_id = request.form.get('course_id')

        if not course_id:
            flash("Please select a course.", "warning")
            return redirect(url_for('student_enroll'))

        try:

            enrollment = query_db("SELECT 1 FROM enrollment WHERE student_id = ? AND course_id = ?", (uid, course_id))
            if enrollment:  
                flash("You are already enrolled in this course!", "warning")
                return redirect(url_for('student_enroll'))

            new_schedule = query_db("SELECT day_of_week FROM schedule WHERE course_id = ?", (course_id,))
            if not new_schedule:
                flash("Course schedule not found.", "danger")
                return redirect(url_for('student_enroll'))


            new_days = set(new_schedule[0][0].split(', '))


            existing_schedule = query_db("""
                SELECT sc.day_of_week
                FROM schedule sc
                JOIN enrollment e ON sc.course_id = e.course_id
                WHERE e.student_id = ?
            """, (uid,))

            for schedule in existing_schedule:
                existing_days = set(schedule[0].split(', '))
                if new_days.intersection(existing_days):
                    flash("You cannot enroll in this course! You have another class on these days!", "danger")
                    return redirect(url_for('student_enroll'))

            execute_db("INSERT INTO enrollment (student_id, course_id, enroll_date) VALUES (?, ?, ?)", 
                       (uid, course_id, datetime.now().strftime('%Y-%m-%d')))
            flash("Enrollment successful!", "success")
            return redirect(url_for('student_enroll'))

        except Exception as e:
            print(traceback.format_exc())
            flash("An error occurred during enrollment.", "danger")
            return redirect(url_for('student_enroll'))

    try:

        courses = query_db("SELECT id, name FROM course")
    except Exception as e:
        print(f"Exception during GET request: {e}")
        courses = []

    return render_template("student/enroll.html", courses=courses, fullname=fullname, uid=uid,first_name=first_name)



@app.route('/student/records')
def view_enrollment_records():
    if 'uid' not in session or session.get('user_type') != 'student':
        return redirect(url_for('student_login'))

    uid = session.get('uid') 
    first_name = session.get('first_name')
    
    try:

        enrollments = query_db("""
            SELECT e.student_id, 
                   s.first_name || ' ' || s.last_name AS fullname, 
                   c.id AS course_id,
                   c.name AS course_name, 
                   e.enroll_date
            FROM enrollment e
            JOIN student s ON e.student_id = s.id
            JOIN course c ON e.course_id = c.id
            WHERE e.student_id = ?
        """, (uid,))


        timetable = query_db("""
            SELECT sc.course_id, c.name AS course_name, sc.day_of_week, sc.start_time, sc.end_time
            FROM schedule sc
            JOIN course c ON sc.course_id = c.id
            WHERE sc.course_id IN (
                SELECT e.course_id FROM enrollment e WHERE e.student_id = ?
            )
            ORDER BY sc.day_of_week, sc.start_time
        """, (uid,))

    except Exception as e:
        print(traceback.format_exc())
        enrollments = []
        timetable = []

    return render_template('student/records.html', 
                           enrollments=enrollments, 
                           timetable=timetable, 
                           first_name=first_name,
                           uid=uid
                         )



@app.route("/student/logout")
def student_logout():
    session.pop('uid', None)
    session.pop('first_name', None)
    return redirect(url_for('choose_user_type'))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = hashlib.md5(password.encode()).hexdigest()

        try:

            user = query_db("SELECT id, first_name FROM admin WHERE email = ? AND password = ?", (email, hashed_password))

            if user:
                user = user[0] 
                session['admin_uid'] = user[0]
                session['first_name'] = user[1]
                session['user_type'] = 'admin'
                return redirect(url_for('admin_dashboard'))
            else:
                flash("Invalid email or password. Please try again.", 'danger')

        except Exception as e:
            print(traceback.format_exc())
            flash("An error occurred during login. Please try again.", 'danger')

    return render_template("admin/login.html")


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


        existing_admins = query_db("SELECT * FROM admin WHERE email = ?", (email,))
        if existing_admins:
            flash("Email is already taken. Please use a different email.", 'danger')
            return render_template("admin/signup.html", title="Admin Signup")

        hashed_password = hashlib.md5(password.encode()).hexdigest()

        try:
            execute_db("""
                INSERT INTO admin (first_name, last_name, phone, email, address, password) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (first_name, last_name, phone, email, address, hashed_password))

            return redirect(url_for('admin_login'))

        except Exception as e:
            print(traceback.format_exc())
            flash("An error occurred during signup. Please try again.", 'danger')

    return render_template("admin/signup.html", title="Admin Signup")


@app.route("/admin/dashboard")
def admin_dashboard():
    if 'admin_uid' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))

    first_name = session.get('first_name')
    admin_uid = session.get('admin_uid')
    try:

        total_students = query_db("SELECT COUNT(*) FROM student")[0][0]
        total_courses = query_db("SELECT COUNT(*) FROM course")[0][0]
        total_enrollments = query_db("SELECT COUNT(*) FROM enrollment")[0][0]


        page = request.args.get('page', 1, type=int)
        per_page = 10
        offset = (page - 1) * per_page


        enrolled_students = query_db("""
            SELECT 
                student.id AS student_id, 
                student.first_name || ' ' || student.last_name AS student_name, 
                course.name AS course_name, 
                enrollment.enroll_date 
            FROM enrollment 
            JOIN student ON enrollment.student_id = student.id
            JOIN course ON enrollment.course_id = course.id
            LIMIT ? OFFSET ?
        """, (per_page, offset))


        total_enrolled_students = query_db("""
            SELECT COUNT(*) 
            FROM enrollment 
            JOIN student ON enrollment.student_id = student.id
            JOIN course ON enrollment.course_id = course.id
        """)[0][0]
        total_pages = (total_enrolled_students + per_page - 1) // per_page

    except Exception as e:
        print(traceback.format_exc())
        total_students = total_courses = total_enrollments = 0
        enrolled_students = []
        total_pages = 0

    return render_template(
        "admin/dashboard.html", 
        first_name=first_name, 
        admin_uid = admin_uid,
        total_students=total_students, 
        total_courses=total_courses, 
        total_enrollments=total_enrollments, 
        enrolled_students=enrolled_students, 
        current_page=page,
        total_pages=total_pages
    )
   
@app.route("/admin/courses", methods=["GET"])
def admin_view_courses():
    if 'admin_uid' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))

    first_name = session.get('first_name')
    admin_uid = session.get('admin_uid')
    
    page = int(request.args.get('page', 1))  
    per_page = 6 


    total_courses = query_db("SELECT COUNT(*) FROM course")[0][0]


    offset = (page - 1) * per_page
    total_pages = (total_courses + per_page - 1) // per_page 


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

    return render_template("admin/courses.html", courses=courses_list, first_name=first_name, admin_uid = admin_uid ,time=time, page=page, total_pages=total_pages)




@app.route("/admin/course/add", methods=["GET", "POST"])
def add_course():
    if 'admin_uid' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    
    admin_uid = session.get('admin_uid')

    upload_folder = os.path.abspath(os.path.join('static', 'images', 'courses'))
    app.config['UPLOAD_FOLDER'] = upload_folder

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    first_name = session.get('first_name')
    if request.method == "POST":
        name = request.form['name']
        description = request.form['description']
        credits = request.form['credit']
        lecturer = request.form['lecturer']
        cfile = request.files['cimage']
        filename = secure_filename(cfile.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)


        try:
            cfile.save(file_path)
            execute_db("INSERT INTO course (name, image, description, credits, lecturer) VALUES (?, ?, ?, ?, ?)",
                       (name, filename, description, credits, lecturer))
            return redirect(url_for('admin_view_courses'))

        except Exception as e:
            print(traceback.format_exc())

    return render_template("admin/addcourse.html", first_name=first_name,admin_uid=admin_uid )

@app.route("/admin/courses/edit/<int:course_id>", methods=["GET", "POST"])
def edit_course(course_id):
    if 'admin_uid' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    
    admin_uid = session.get('admin_uid')

    try:
        first_name = session.get('first_name')
        course = query_db("SELECT id, name, image, description, credits, lecturer FROM course WHERE id = ?", (course_id,))
        
        if not course:
            flash("Course not found.", 'danger')
            return redirect(url_for('admin_view_courses'))
        
        course = course[0] 
        
    except Exception as e:
        print(traceback.format_exc())
        flash("Error fetching course details.", 'danger')
        return redirect(url_for('admin_view_courses'))


    upload_folder = os.path.abspath(os.path.join('static', 'images', 'courses'))
    app.config['UPLOAD_FOLDER'] = upload_folder


    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])


    if request.method == "POST":
        name = request.form['name']
        description = request.form['description']
        credits = request.form['credit']
        lecturer = request.form['lecturer']
        cfile = request.files['cimage']
        
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

            filename = course[2]

        try:

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

    return render_template("admin/editcourse.html", course=course, first_name = first_name, admin_uid = admin_uid)


@app.route("/admin/courses/delete/<int:id>", methods=["POST"])
def delete_course(id):
    try:

        enrollment_count = query_db("SELECT COUNT(*) FROM enrollment WHERE course_id = ?", (id,))
        
        if enrollment_count and enrollment_count[0][0] > 0:
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
    if 'admin_uid' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))

    first_name = session.get('first_name')
    admin_uid = session.get('admin_uid')

    page = int(request.args.get('page', 1))
    per_page = 10 
    

    total_students_query = "SELECT COUNT(*) FROM student"
    total_students = query_db(total_students_query)[0][0]

    offset = (page - 1) * per_page
    

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
            "email": student[4],
            "phone": student[3],
            "address": student[5],
        }
        students_list.append(student_dict)

    total_pages = (total_students + per_page - 1) // per_page
    
    return render_template(
        "admin/students.html", 
        students=students_list, 
        first_name=first_name, 
        time=time,
        current_page=page,
        total_pages=total_pages,
        admin_uid=admin_uid 
    )



@app.route("/admin/student/add", methods=["GET", "POST"])
def add_student():
    if 'admin_uid' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))

    first_name = session.get('first_name')
    admin_uid = session.get('admin_uid')
    if request.method == "POST":
        fname = request.form['first_name']
        lname = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        password = request.form['password']


        hashed_password = hashlib.md5(password.encode()).hexdigest()

        try:
            execute_db("INSERT INTO student (first_name, last_name, email, phone, address, password) VALUES (?, ?, ?, ?, ?, ?)",
                       (fname, lname, email, phone, address, hashed_password))
            return redirect(url_for('admin_view_students'))
        except Exception as e:
            print(traceback.format_exc())

    return render_template("admin/addstudent.html", first_name=first_name,admin_uid=admin_uid)


@app.route("/admin/students/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    if 'admin_uid' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    
    admin_uid = session.get('admin_uid')

    try:
        first_name = session.get('first_name')
        student = query_db("SELECT first_name, last_name, email, phone, address FROM student WHERE id = ?", (student_id,))
        
        if not student:
            flash("Student not found.", 'danger')
            return redirect(url_for('admin_view_students'))
        
        student = student[0]
        
    except Exception as e:
        print(traceback.format_exc())
        flash("Error fetching student details.", 'danger')
        return redirect(url_for('admin_view_students'))


    if request.method == "POST":
        fname = request.form['first_name']
        lname = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        
        try:

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

    return render_template("admin/editstudent.html", student=student, first_name=first_name,admin_uid=admin_uid)

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
    if 'admin_uid' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))

    first_name = session.get('first_name')
    admin_uid = session.get('admin_uid')

    per_page = 10
    page = request.args.get('page', 1, type=int)

    schedules = query_db("SELECT * FROM schedule")
    

    total_schedules = len(schedules)
    total_pages = (total_schedules + per_page - 1) // per_page

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
        current_page=page, 
        total_pages=total_pages,
        first_name = first_name,
        admin_uid = admin_uid
    )



@app.route("/admin/schedule/add", methods=["GET", "POST"])
def add_schedule():
    if 'admin_uid' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))

    first_name = session.get('first_name')
    admin_uid = session.get('admin_uid')
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

    return render_template("admin/addschedule.html", first_name=first_name,admin_uid=admin_uid)

@app.route("/admin/schedules/edit/<int:schedule_id>", methods=["GET", "POST"])
def edit_schedule(schedule_id):
    if 'admin_uid' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    
    first_name = session.get('first_name')
    admin_uid = session.get('admin_uid')
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
        schedule = query_db("SELECT course_id, day_of_week, start_time, end_time FROM schedule WHERE id = ?", (schedule_id,))
        if not schedule:
            flash("Schedule not found.", 'danger')
            return redirect(url_for('admin_view_schedules'))

        schedule = schedule[0]
    except Exception as e:
        print(traceback.format_exc())
        flash("Error fetching schedule details.", 'danger')
        return redirect(url_for('admin_view_schedules'))

    return render_template("admin/editschedule.html", schedule=schedule, first_name=first_name,admin_uid=admin_uid)

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
    if 'admin_uid' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))

    first_name = session.get('first_name')
    admin_uid = session.get('admin_uid')

    page = request.args.get('page', 1, type=int)
    per_page = 10  

    total_enrollment = query_db("SELECT COUNT(*) FROM enrollment")[0][0]

    offset = (page - 1) * per_page
    enrollment_query = f"SELECT * FROM enrollment LIMIT {per_page} OFFSET {offset}"
    enrollment = query_db(enrollment_query)

    enrollment_list = []
    for record in enrollment:
        enrollment_dict = {
            "id": record[0],
            "student_id": record[1],
            "course_id": record[2],
            "enroll_date": record[3],
        }
        enrollment_list.append(enrollment_dict)


    total_pages = (total_enrollment + per_page - 1) // per_page

    return render_template(
        "admin/enrollmentmgmt.html", 
        enrollment_list=enrollment_list, 
        first_name=first_name, 
        current_page=page, 
        total_pages=total_pages, 
        per_page=per_page,
        admin_uid=admin_uid
    )


@app.route("/admin/enrollment", methods=["GET", "POST"])
def admin_enroll():
    if 'admin_uid' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    
    first_name = session.get('first_name')
    admin_uid = session.get('admin_uid')

    if request.method == "POST":
        student_id = request.form.get('student_id')
        course_id = request.form.get('course_id')

        if not student_id or not course_id:
            return redirect(url_for('admin_enroll'))

        try:

            execute_db("""
                INSERT INTO enrollment (student_id, course_id, enroll_date) 
                VALUES (?, ?, ?)
            """, (student_id, course_id, datetime.now().strftime('%Y-%m-%d')))

            return redirect(url_for('admin_view_enrollment'))

        except Exception as e:
            print(traceback.format_exc())

    try:
        students = query_db("SELECT id, first_name, last_name FROM student") or []
        courses = query_db("SELECT id, name FROM course") or []

    except Exception as e:
        print(f"Exception during GET request: {e}")
        students = []
        courses = []

    return render_template("admin/enroll.html", students=students, courses=courses, first_name=first_name, admin_uid=admin_uid)


@app.route("/admin/enrollment/delete/<int:id>", methods=["POST"])
def delete_enrollment(id):
    try:
            execute_db("DELETE FROM enrollment WHERE id = ?", (id,))
            flash("Enrollment deleted successfully.", 'success')

    except Exception as e:
        print(traceback.format_exc())
        flash("An error occurred while trying to delete the course. Please try again.", 'danger')

    return redirect(url_for('admin_view_enrollment'))

@app.route("/admin/logout")
def admin_logout():
    session.pop('admin_uid', None)
    session.pop('first_name', None)
    return redirect(url_for('choose_user_type'))

if __name__ == "__main__":
    app.run(debug=True)
