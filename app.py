from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
import requests
import smtplib
import random
import string
from models import db, User
import Syllabus.sub as sub  # Use this instead of subjects
import resources  # Use this instead of resources
from resources.resources import get_drive_link  # Import the function to get drive links
from chatbot.chat import get_chatbot_response
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


# Database Configuration - Updated for Heroku PostgreSQL
database_url = os.getenv("DATABASE_URL")
# Fix for Heroku PostgreSQL URLs starting with "postgres://"
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database with the app
db.init_app(app)

# Initialize syllabus data
@app.before_request
def initialize_syllabus():
    with app.app_context():
        sub.subjects_by_year, sub.units_by_subject = sub.load_data_from_db()
        print("Syllabus data loaded successfully!")

# Initialize resource data
@app.before_request
def initialize_resources():
    from resources.resources import load_resources_from_db
    with app.app_context():
        load_resources_from_db()
        print("Resource data loaded successfully!")

# Configure session
if os.getenv("ON_HEROKU", "0") == "1":
    # Use database for session storage on Heroku
    app.config['SESSION_TYPE'] = 'sqlalchemy'  
    app.config['SESSION_SQLALCHEMY'] = db
else:
    # Use filesystem for local development
    app.config['SESSION_TYPE'] = 'filesystem'

app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
Session(app)


# Create database tables
with app.app_context():
    db.create_all()

def subject_codes(subject):
    """Extracts the subject code from the subject name if present"""
    if "(" in subject and ")" in subject:
        return subject.split("(")[1].split(")")[0]
    return subject

@app.route('/')
def home():
    if 'user' in session:
        return render_template('dashboard.html', user=session['user'])
    return render_template('/index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            # Find user by email
            user = User.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                # Authentication successful
                # Store user data in session
                session['user'] = user.to_session_dict()
                flash('Login successful!', 'success')
                return redirect('/')
            else:
                # Authentication failed
                return redirect('/login?error=invalid')  # Redirect back with error parameter

        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        # Check if user already exists BEFORE proceeding with OTP
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered! Please login or use a different email.', 'danger')
            return redirect(url_for('signup'))
        
        # Store user info in session temporarily
        session['signup_name'] = name
        session['signup_email'] = email
        session['signup_password'] = password  # In production, hash this immediately
        
        # Redirect to send-otp route instead of calling the function directly
        return redirect(url_for('send_otp'))
        
    return render_template('signup.html')

# Generate a random 6-digit OTP
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


# Routes for OTP verification flow
@app.route('/send-otp', methods=['GET', 'POST'])
def send_otp():
    email = session.get('signup_email')
    name = session.get('signup_name')
    
    # Redirect if no email in session
    if not email or not name:
        flash("Please complete the signup form first", "error")
        return redirect('/signup')

    # Generate OTP
    otp = generate_otp()
    
    # Store OTP in session with timestamp
    session['otp'] = otp
    session['otp_email'] = email
    session['otp_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(email)
    # Send OTP
    try:
        send_otp_email(name, email, otp)
        print(f"OTP sent to {email}: {otp}")  # Debugging line
        return redirect(url_for('verify_otp'))
    except Exception as e:
        flash(f"Error sending email: {e}", "error")
        return redirect(url_for('signup'))
        
# Update the existing send_otp_email function to support password reset
def send_otp_email(name, email, otp, is_password_reset=False):
    try:
        api_key = os.getenv('MAILJET_API_KEY')
        api_secret = os.getenv('MAILJET_API_SECRET')
        from_email = os.getenv('MAILJET_FROM_EMAIL', 'noreply@studybuddy.com')
        from_name = os.getenv('MAILJET_FROM_NAME', 'StudyBuddy')
        
        if not api_key or not api_secret:
            raise Exception("Mailjet API credentials not found in environment variables")
        
        url = "https://api.mailjet.com/v3.1/send"
        
        # Change subject and content based on email type
        if is_password_reset:
            subject = "StudyBuddy - Password Reset Code"
            text_content = f"Hi {name},\n\nYour password reset code is: {otp}\n\nThis code will expire in 10 minutes.\n\nRegards,\nStudyBuddy Team"
            html_content = f"<h3>Hi {name},</h3><p>Your password reset code is: <strong>{otp}</strong></p><p>This code will expire in 10 minutes.</p><p>If you didn't request this, please ignore this email.</p><p>Regards,<br>StudyBuddy Team</p>"
        else:
            subject = "StudyBuddy - Email Verification Code"
            text_content = f"Hi {name},\n\nYour verification code is: {otp}\n\nThis code will expire in 10 minutes.\n\nRegards,\nStudyBuddy Team"
            html_content = f"<h3>Hi {name},</h3><p>Your verification code is: <strong>{otp}</strong></p><p>This code will expire in 10 minutes.</p><p>Regards,<br>StudyBuddy Team</p>"
        
        payload = {
            "Messages": [
                {
                    "From": {
                        "Email": from_email,
                        "Name": from_name
                    },
                    "To": [
                        {
                            "Email": email,
                            "Name": name
                        }
                    ],
                    "Subject": subject,
                    "TextPart": text_content,
                    "HTMLPart": html_content
                }
            ]
        }
        
        print(f"Sending {'password reset' if is_password_reset else 'verification'} email to {email}")
        response = requests.post(
            url,
            auth=(api_key, api_secret),
            json=payload
        )
        
        print(f"Mailjet response: {response.status_code}, {response.text}")
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Mailjet error: {str(e)}")
        raise e


@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        stored_otp = session.get('otp')
        otp_time = session.get('otp_time')
        
        # Check if OTP exists
        if not stored_otp or not otp_time:
            flash("OTP expired or not found. Please request a new one.", "error")
            return redirect(url_for('signup'))
        
        # Check if OTP is expired (10 minutes)
        otp_datetime = datetime.strptime(otp_time, '%Y-%m-%d %H:%M:%S')
        if datetime.now() - otp_datetime > timedelta(minutes=10):
            flash("OTP has expired. Please request a new one.", "error")
            return redirect(url_for('signup'))
        
        # Check if OTP matches
        if entered_otp == stored_otp:
            # Mark email as verified
            session['email_verified'] = True
            flash("Email verified successfully!", "success")
            return redirect(url_for('complete_signup'))
        else:
            flash("Invalid OTP. Please try again.", "error")
    
    return render_template('verify_otp.html')


@app.route('/complete-signup')
def complete_signup():
    # Check if email is verified
    if not session.get('email_verified'):
        flash('Please verify your email first', 'error')
        return redirect(url_for('signup'))
    
    # Get user info from session
    name = session.get('signup_name')
    email = session.get('signup_email')
    password = session.get('signup_password')
    
    try:
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if (existing_user):
                flash('Email already registered!', 'danger')
                return redirect('/signup')
                
            # Create new user
            new_user = User(
                name=name,
                email=email,
                email_verified=True
            )
            new_user.set_password(password)
            
            # Add to database
            db.session.add(new_user)
            db.session.commit()

            # Clear sensitive session data
            session.pop('signup_name', None)
            session.pop('signup_email', None) 
            session.pop('signup_password', None)
            session.pop('otp', None)
            session.pop('otp_time', None)
            
            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('signup'))

    
    

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if "user" not in session:
        return redirect(url_for("login"))  # Redirect if not logged in

    user_id = session["user"]["uid"]
    user = User.query.get(user_id)
    
    if not user:
        flash("User not found!", "danger")
        session.pop('user', None)
        return redirect(url_for("login"))

    if request.method == "POST":
        # Get form data
        user.name = request.form.get("name")
        user.roll_no = request.form.get("roll_no")
        user.dob = request.form.get("dob")
        user.current_year = request.form.get("current_year")
        user.branch = request.form.get("branch")
        user.college = request.form.get("college")
        
        # Update password if provided
        new_password = request.form.get("new_password")
        if new_password:
            user.set_password(new_password)

        # Save changes to database
        try:
            db.session.commit()
            
            # Update session data
            session['user'] = user.to_session_dict()
            
            flash("Profile updated successfully!", "success")
            return redirect(url_for("home"))  # Redirect to dashboard instead
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating profile: {str(e)}", "danger")
            return redirect(url_for("profile"))

    return render_template("profile.html", user=user)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if "user" not in session:
        return redirect(url_for("login"))  # Redirect if not logged in

    user_id = session["user"]["uid"]
    user = User.query.get(user_id)
    
    if not user:
        flash("User not found!", "danger")
        session.pop('user', None)
        return redirect(url_for("login"))

    if request.method == 'POST':
        # Get all form values
        user.current_year = request.form.get('year')
        user.subject = request.form.get('subject')
        user.unit = request.form.get('unit')
        
        try:
            # Save to database
            db.session.commit()
            
            # Update session data
            session['user'] = user.to_session_dict()
            
            flash("Selections saved successfully", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error saving selections: {str(e)}", "danger")
            
        return redirect(url_for("chat"))

    return render_template("chat.html", user=user)

@app.route('/get_subjects_by_year/<year>')
def get_subjects_by_year(year):
    """Get all subjects for a specific year"""
    subjects_list = sub.get_subjects_by_year(year)

    return jsonify(subjects_list)

@app.route('/get_subjects')
def get_subjects():
    """Get all subjects across all years"""
    # Collect subjects from all years
    all_subjects = set()
    for year in ["1Y", "2Y", "3Y", "4Y"]:
        all_subjects.update(sub.get_subjects_by_year(year))
    return jsonify(list(all_subjects))

@app.route('/get_units/<subject>')
def get_units(subject):
    """Get all units with topics for a specific subject"""
    # Extract the subject code if it's in the format "Subject Name (Code)"
    units = sub.get_units_for_subject(subject_codes(subject))
    if units:
        return jsonify(units)
    else:
        return jsonify({"error": "Subject not found"}), 404

@app.route('/chat_message', methods=['POST'])
def chat_message():
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.json
    message = data.get('message', '')
    subject = data.get('subject', session['user'].get('subject', ''))
    unit = data.get('unit', session['user'].get('unit', ''))
    
    if not subject or not unit:
        return jsonify({
            "response": "Please select a subject and unit from the dashboard first to get more relevant answers."
        })
    
    # Get response from chatbot (it will pull syllabus content internally)
    try:
        response = get_chatbot_response(subject, unit, message)
        return jsonify({"response": response})
    except Exception as e:
        print(f"Error generating response: {e}")
        return jsonify({"response": "Sorry, I encountered an error. Please try again later."})

# route to clear chat history
@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    user_id = session["user"]["uid"]
    subject = session['user'].get('subject', '')
    unit = session['user'].get('unit', '')
    
    # Import the chat histories dictionary
    from chatbot.chat import chat_histories
    
    # Create the conversation key
    conversation_key = f"{user_id}-{subject}-{unit}"
    
    # Clear the chat history
    if conversation_key in chat_histories:
        # Keep only the system message
        system_message = chat_histories[conversation_key][0]
        chat_histories[conversation_key] = [system_message]
    
    return jsonify({"success": True})

@app.route('/get_drive_link/<resource_type>/<subject>/<unit>', methods=['GET'])
def fetch_drive_link(resource_type, subject, unit):
    """
    API endpoint to fetch the Google Drive link for a given resource type, subject, and unit.
    """
    subject_code = subject_codes(subject)  # Extract the subject code if it's in the format "Subject Name (Code)"
    drive_link = get_drive_link(resource_type, subject_code, unit)
    if drive_link:
        return jsonify({"drive_link": drive_link})
    else:
        return jsonify({"error": "Drive link not found"}), 404

@app.route('/send_feedback', methods=['POST'])
def send_feedback():
    subject = request.form.get('subject')
    message = request.form.get('message')
    user_email = request.form.get('email')
    
    # Use session data instead of current_user
    user_name = session['user']['name'] if 'user' in session else "Anonymous"
    
    try:
        # Send feedback using Mailjet
        send_feedback_email(user_name, user_email, subject, message)
        flash("Thank you for your feedback!", "success")
    except Exception as e:
        flash(f"Failed to send feedback: {str(e)}", "error")
        print(f"Email sending error: {str(e)}")  # Log the error for debugging
    
    return redirect(url_for('home'))

def send_feedback_email(user_name, user_email, subject, message):
    """Send feedback email using Mailjet API"""
    try:
        api_key = os.getenv('MAILJET_API_KEY')
        api_secret = os.getenv('MAILJET_API_SECRET')
        from_email = os.getenv('MAILJET_FROM_EMAIL', 'noreply@studybuddy.com')
        from_name = os.getenv('MAILJET_FROM_NAME', 'StudyBuddy')
        to_email = os.getenv('MAILJET_FROM_EMAIL')  # Send to same email as sender
        
        if not api_key or not api_secret:
            raise Exception("Mailjet API credentials not found in environment variables")
        
        url = "https://api.mailjet.com/v3.1/send"
        
        # Create email content
        text_content = f"Feedback from: {user_name} ({user_email})\n\n{message}"
        html_content = f"""
        <h3>Feedback from: {user_name} ({user_email})</h3>
        <p>{message}</p>
        """
        
        payload = {
            "Messages": [
                {
                    "From": {
                        "Email": from_email,
                        "Name": from_name
                    },
                    "To": [
                        {
                            "Email": to_email,
                            "Name": "StudyBuddy Admin"
                        }
                    ],
                    "Subject": f"Feedback: {subject}",
                    "TextPart": text_content,
                    "HTMLPart": html_content
                }
            ]
        }
        
        print(f"Sending feedback email from {user_email}")
        response = requests.post(
            url,
            auth=(api_key, api_secret),
            json=payload
        )
        
        print(f"Mailjet response: {response.status_code}, {response.text}")
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Mailjet error: {str(e)}")
        raise e

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully!', 'success')
    return redirect('/')

@app.route('/test-email')
def test_email():
    try:
        send_otp_email("Test User", "sujalrawat884@gmail.com", "123456")
        return "Email sent successfully! Check logs for details."
    except Exception as e:
        return f"Email sending failed: {str(e)}"

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No account found with that email address.', 'error')
            return render_template('forgot_password.html')
            
        # Generate OTP
        otp = generate_otp()
        
        # Store OTP in session with timestamp
        session['reset_otp'] = otp
        session['reset_email'] = email
        session['reset_otp_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Send OTP
        try:
            send_otp_email(user.name, email, otp, is_password_reset=True)
            flash('Password reset code has been sent to your email.', 'success')
            return redirect(url_for('reset_password'))
        except Exception as e:
            flash(f"Error sending email: {str(e)}", "error")
            return render_template('forgot_password.html')
            
    return render_template('forgot_password.html')


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        stored_otp = session.get('reset_otp')
        otp_time = session.get('reset_otp_time')
        email = session.get('reset_email')
        
        # Check if OTP exists
        if not stored_otp or not otp_time or not email:
            flash("Password reset session expired. Please try again.", "error")
            return redirect(url_for('forgot_password'))
        
        # Check if OTP is expired (10 minutes)
        otp_datetime = datetime.strptime(otp_time, '%Y-%m-%d %H:%M:%S')
        if datetime.now() - otp_datetime > timedelta(minutes=10):
            flash("Verification code has expired. Please request a new one.", "error")
            return redirect(url_for('forgot_password'))
        
        # Check if passwords match
        if new_password != confirm_password:
            flash("Passwords don't match.", "error")
            return render_template('reset_password.html')
            
        # Check if OTP matches
        if entered_otp == stored_otp:
            # Find user and update password
            user = User.query.filter_by(email=email).first()
            if user:
                user.set_password(new_password)
                db.session.commit()
                
                # Clear session data
                session.pop('reset_otp', None)
                session.pop('reset_email', None)
                session.pop('reset_otp_time', None)
                
                flash("Password has been reset successfully! Please login with your new password.", "success")
                return redirect(url_for('login'))
            else:
                flash("User not found.", "error")
                return redirect(url_for('forgot_password'))
        else:
            flash("Invalid verification code. Please try again.", "error")
    
    return render_template('reset_password.html')

if __name__ == '__main__':
    app.run(debug=True)
