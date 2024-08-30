from flask import Flask, render_template, url_for, flash, redirect, request, session
import sqlite3
import traceback
import hashlib

app = Flask(__name__)
app.secret_key = 'secrete'  # Required for flash messages

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        # Encrypt the password using MD5 to compare with the stored hash
        hashed_password = hashlib.md5(password.encode()).hexdigest()

        try:
            con = sqlite3.connect("advweb.db")
            cursor = con.cursor()

            # Fetch the user record with the matching email and password
            cursor.execute("SELECT first_name FROM student WHERE email = ? AND password = ?", (email, hashed_password))
            user = cursor.fetchone()

            if user:
                session['username'] = user[0]  # Store the username in the session
                return redirect(url_for('home'))
            else:
                flash("Invalid email or password. Please try again.", 'danger')

        except Exception as e:
            print(traceback.format_exc())  # Print the traceback for debugging
            flash("An error occurred during login. Please try again.", 'danger')
        finally:
            con.close()  # Ensure the connection is closed

    return render_template("login.html", title="Login")

@app.route("/student/home")
def home():
    username = session.get('username')
    return render_template('home.html', username=username)

@app.route("/student/enrollment")
def enroll():
    return render_template('enroll.html')

@app.route("/student/logout")
def logout():
    session.pop('username', None)  # Remove the username from the session
    return redirect(url_for('login'))

@app.route("/student/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        first_name = request.form.get('fname')
        last_name = request.form.get('lname')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        password = request.form.get('password')
        confirm_password = request.form.get('cpassword')

        # Check if password and confirm password match
        if not password or not confirm_password or password != confirm_password:
            flash("Passwords do not match or are missing. Please try again.", 'danger')
            return render_template("signup.html", title="Signup")

        # Encrypt the password using MD5
        hashed_password = hashlib.md5(password.encode()).hexdigest()

        try:
            con = sqlite3.connect("advweb.db")
            cursor = con.cursor()

            # Insert data into the student table
            cursor.execute("""
                INSERT INTO student (first_name, last_name, email, phone, address, password) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (first_name, last_name, email, phone, address, hashed_password))

            con.commit()  # Commit the transaction
            return redirect(url_for('login'))  # Redirect to login page

        except Exception as e:
            con.rollback()  # Rollback in case of an error
            print(traceback.format_exc())  # Print the traceback for debugging
            flash("An error occurred during signup. Please try again.", 'danger')
        finally:
            con.close()  # Ensure the connection is closed

    return render_template("signup.html", title="Signup")

if __name__ == "__main__":
    app.run(debug=True)
