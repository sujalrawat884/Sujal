from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from models import db, User
import Syllabus.sub as sub  # Use this instead of subjects
import resources  # Use this instead of resources
from resources.resources import get_drive_link  # Import the function to get drive links
from chatbot.chat import get_chatbot_response
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# MySQL Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "mysql://username:password@localhost/sujal_db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database with the app
db.init_app(app)

# Add this after db.init_app(app)

# Initialize syllabus data
@app.before_request
def initialize_syllabus():
    with app.app_context():
        sub.subjects_by_year, sub.units_by_subject = sub.load_data_from_db()
        print("Syllabus data loaded successfully!")

# Add after db.init_app(app)

# Initialize resource data
@app.before_request
def initialize_resources():
    from resources.resources import load_resources_from_db
    with app.app_context():
        load_resources_from_db()
        print("Resource data loaded successfully!")

# Configure session
app.config['SESSION_TYPE'] = 'filesystem'
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
                flash('Invalid email or password!', 'danger')

        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        try:
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email already registered!', 'danger')
                return redirect('/signup')
                
            # Create new user
            new_user = User(
                name=name,
                email=email,
                email_verified=False
            )
            new_user.set_password(password)
            
            # Add to database
            db.session.add(new_user)
            db.session.commit()

            flash('Account created! Please login.', 'success')
            return redirect('/login')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    return render_template('signup.html')

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

# # Add a new route to get resource content
# @app.route('/get_resource_content/<resource_type>/<subject>/<unit>')
# def get_resource_content(resource_type, subject, unit):
#     # Convert to codes if full names were provided
#     subject_code = sub.get_subject_code(subject)
    
#     # Extract unit number (e.g., "Unit 1" -> "U1")
#     unit_code = None
#     if unit.startswith("Unit "):
#         unit_num = unit.split(" ")[1]
#         unit_code = f"U{unit_num}"
    
#     # Generate path for resource
#     resource_path = f"resources/{resource_type}/{subject_code}/{unit_code}"
    
#     # This is a placeholder - in a real app, you would check if the resource exists
#     # and return its URL or content
#     return jsonify({
#         "path": resource_path,
#         "exists": False,  # You would check this in a real implementation
#         "message": f"Resource for {resource_type} - {subject} - {unit} would be found at {resource_path}"
#     })

# @app.route('/get_youtube_url/<subject>/<unit>')
# def get_youtube_url(subject, unit):
#     from youtube.youtube import get_youtube_url
#     year = session['user'].get('year', '1Y')  # Default to 1Y if not set
#     subject_code = subject_codes(subject)
#     print(f"year: {year}, subject_code: {subject_code}, unit: {unit}")  # Debugging line
#     url = get_youtube_url(year,subject_code, unit)
#     if url:
#         # Extract video ID for embedding
#         video_id = url.split('v=')[1] if 'v=' in url else None
#         return jsonify({"url": url, "video_id": video_id})
#     else:
#         return jsonify({"error": "Video not found"}), 404

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

# Add this route to clear chat history
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
    
    # Fix: Use session data instead of current_user
    user_name = session['user']['name'] if 'user' in session else "Anonymous"
    
    # Use same email for both sender and receiver
    sender_email = os.getenv("EMAIL_ADDRESS")
    receiver_email = sender_email  # Use the same email as both sender and receiver
    password = os.getenv("EMAIL_PASSWORD")
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"Feedback: {subject}"
    
    body = f"""
    Feedback from: {user_name} ({user_email})
    
    {message}
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        # Connect to server and send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()
        flash("Thank you for your feedback!", "success")
    except Exception as e:
        flash(f"Failed to send feedback: {str(e)}", "error")
        print(f"Email sending error: {str(e)}")  # Log the error for debugging
    
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully!', 'success')
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
