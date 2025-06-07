from flask import *
from flask_mail import *
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = "admin"

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'vincenavarrete3@gmail.com'      # your email
app.config['MAIL_PASSWORD'] = 'Bbkateilove123'       # your app password or email password
app.config['MAIL_DEFAULT_SENDER'] = ('Vince Navarrete', 'vincenavarrete3@gmail.com')

mail = Mail(app)

conn = mysql.connector.connect(
    host=os.environ['DB_HOST'],
    port=os.environ.get('DB_PORT', 3306),
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    database=os.environ['DB_NAME']
)

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="admin",
        database="einvites"
    )

@app.route("/")
def loginPage():
    email = request.args.get('email')
    return render_template("loginPage.html")

@app.route("/submit", methods=["POST"])
def login():
    name = request.form.get('name')
    email = request.form.get('email')

    # ✅ Check if it's the admin
    if name == "admin123" and email == "admin@email.com":
        session['user_email'] = email
        session['user_name'] = name
        flash("Welcome, Admin!", "success")
        return redirect(url_for("admin_dashboard"))

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if user already exists in users table
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            # Insert user if not existing
            cursor.execute("INSERT INTO users (name, email) VALUES (%s, %s)", (name, email))
            conn.commit()

        # Set session info
        session['user_email'] = email
        session['user_name'] = name

        # Check RSVP status from invited table
        cursor.execute("SELECT if_coming FROM invited WHERE email = %s", (email,))
        invited_row = cursor.fetchone()
        session['rsvp_status'] = invited_row['if_coming'] if invited_row else None

        cursor.close()
        conn.close()

        flash(f"Welcome, {name}!", "success")
        return redirect(url_for("homePage"))

    except Exception as e:
        flash("Something went wrong: " + str(e), "error")
        return redirect(url_for("loginPage"))


@app.route("/home")
def homePage():
    user_email = session.get('user_email')

    if not user_email:
        flash("Please log in first.", "error")
        return redirect(url_for("loginPage"))

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if user email is in invited table
        cursor.execute("SELECT if_coming FROM invited WHERE email = %s", (user_email,))
        invited_row = cursor.fetchone()

        cursor.close()
        conn.close()

        if invited_row:
            user_rsvp = invited_row['if_coming']  # 1 or 0 or maybe NULL
            return render_template("homePage.html", rsvp=user_rsvp, is_invited=True)
        else:
            # User not invited
            return render_template("homePage.html", is_invited=False)

    except Exception as e:
        flash(f"Error checking RSVP status: {e}", "error")
        return redirect(url_for("loginPage"))

@app.route('/rsvp', methods=['POST'])
def rsvp():
    email = session.get('user_email')

    if not email:
        flash("You must be logged in to RSVP.", "error")
        return redirect(url_for('loginPage'))

    try:
        response = request.form['response']  # "1" or "0"

        conn = get_connection()
        cursor = conn.cursor()

        # Update RSVP status
        cursor.execute("UPDATE invited SET if_coming = %s WHERE email = %s", (response, email))
        conn.commit()

        session['rsvp_status'] = int(response)  # Update session value

        cursor.close()
        conn.close()

        flash("Thank you for your response!", "success")

    except Exception as e:
        flash(f"Something went wrong: {e}", "error")

    return redirect(url_for('homePage'))

@app.route('/change-rsvp', methods=['POST'])
def change_rsvp():
    email = session.get('user_email')
    new_response = request.form.get('response')

    if not email:
        flash("You must be logged in to change your RSVP.", "error")
        return redirect(url_for('loginPage'))

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("UPDATE invited SET if_coming = %s WHERE email = %s", (new_response, email))
        conn.commit()
        session['rsvp_status'] = int(new_response)

        cursor.close()
        conn.close()

        flash("Your RSVP has been updated.", "success")
        return redirect(url_for('homePage'))

    except Exception as e:
        flash(f"Could not update RSVP: {e}", "error")
        return redirect(url_for('homePage'))

@app.route('/who-will-come')
def who_will_come():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT name FROM invited WHERE if_coming = 1")
        people = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('comming.html', people=people)
    except Exception as e:
        flash(f"Error loading list: {e}", "error")
        return redirect(url_for('homePage'))

@app.route('/who-are-invited')
def who_are_invited():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT name FROM invited")
        everyone = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('invited.html', everyone=everyone)
    except Exception as e:
        flash(f"Error loading list: {e}","error")
        return redirect(url_for('homePage'))

@app.route("/exit")
def exit():
    session.clear()  # Clear all session data
    flash("You have been logged out.", "info")
    return redirect(url_for("loginPage"))

@app.route('/admin')
def admin_dashboard():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # All invited
        cursor.execute("SELECT name, email FROM invited")
        invited = cursor.fetchall()

        # RSVP responses
        cursor.execute("SELECT name, email FROM invited WHERE if_coming = 1")
        coming = cursor.fetchall()

        cursor.execute("SELECT name, email FROM invited WHERE if_coming = 0")
        not_coming = cursor.fetchall()

        cursor.execute("SELECT name, email FROM invited WHERE if_coming IS NULL")
        no_response = cursor.fetchall()

        # Invitation requests (registered but not yet invited)
        cursor.execute("SELECT name, email FROM users WHERE email NOT IN (SELECT email FROM invited)")
        requests = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('admin.html',
                               invited=invited,
                               coming=coming,
                               not_coming=not_coming,
                               no_response=no_response,
                               requests=requests)
    except Exception as e:
        flash(f"Error loading admin data: {e}", "error")
        return redirect(url_for("loginPage"))


@app.route('/admin/invite', methods=['POST'])
def admin_invite():
    name = request.form.get('name')
    email = request.form.get('email')
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO invited (name, email) VALUES (%s, %s)", (name, email))
        conn.commit()
        cursor.close()
        conn.close()
        flash("User successfully invited.", "success")
    except Exception as e:
        flash(f"Could not invite user: {e}", "error")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/send_email', methods=['POST'])
def admin_send_email():
    email = request.form.get('email')
    if not email:
        flash("Email is missing.", "error")
        return redirect(url_for('admin_dashboard'))

    # Your email sending logic here, e.g.:
    try:
        send_email_to_guest(email)
        flash(f"Email sent to {email}", "success")
    except Exception as e:
        flash(f"Failed to send email to {email}: {str(e)}", "error")

    return redirect(url_for('admin_dashboard'))


def send_email_to_guest(email):
    invitation_url = url_for('invitation_page', email=email, _external=True)
    body = f"""
    Hello!

    You are invited to our event. Please click the link below to view your invitation and RSVP:

    {invitation_url}

    We look forward to your response!
    """

    msg = Message(
        subject="Your Invitation to Our Event",
        recipients=[email],
        body=body
    )
    mail.send(msg)

if __name__ == '__main__':
    app.run(debug=True)
