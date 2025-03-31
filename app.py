from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
import firebase_admin
from firebase_admin import credentials, auth, firestore
from flask_session import Session
from dotenv import load_dotenv
import os
import Syllabus.sub as sub  # Use this instead of subjects
import resources  # Use this instead of resources
from resources.resources import get_drive_link  # Import the function to get drive links
from chatbot.chat import get_chatbot_response
import requests

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Configure session
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Initialize Firebase Admin SDK
cred = credentials.Certificate('firebase-adminsdk.json')
firebase_admin.initialize_app(cred)

# Initialize Firestore DB
db = firestore.client()

FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")  # Add your Firebase API key to your .env file

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
            # Use Firebase REST API to authenticate the user
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            response = requests.post(url, json=payload)
            response_data = response.json()

            if response.status_code == 200:
                # Authentication successful
                user_id = response_data['localId']
                id_token = response_data['idToken']

                # Fetch user details from Firestore
                user_doc = db.collection("users").document(user_id).get()
                user_data = user_doc.to_dict() if user_doc.exists else {}

                # Store user data in session
                session['user'] = {
                    'uid': user_id,
                    'email': email,
                    'name': user_data.get("name", "User"),  # Default to "User" if name is missing
                    'year': user_data.get("current_year", None)  # Default to None if year is missing
                }

                flash('Login successful!', 'success')
                return redirect('/')
            else:
                # Authentication failed
                error_message = response_data.get('error', {}).get('message', 'Invalid credentials!')
                flash(f'Error: {error_message}', 'danger')

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
            # Create user in Firebase Authentication
            user = auth.create_user(email=email, password=password)

            # Store additional user details in Firestore
            user_data = {
                "uid": user.uid,
                "name": name,
                "email": email
            }
            db.collection("users").document(user.uid).set(user_data)

            flash('Account created! Please login.', 'success')
            return redirect('/login')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    return render_template('signup.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if "user" not in session:
        return redirect(url_for("login"))  # Redirect if not logged in

    user_id = session["user"]["uid"]

    if request.method == "POST":
        # Get form data
        name = request.form.get("name")
        roll_no = request.form.get("roll_no")
        dob = request.form.get("dob")
        current_year = request.form.get("current_year")
        branch = request.form.get("branch")
        college = request.form.get("college")

        # Store/update in Firestore
        user_data = {
            "name": name,
            "roll_no": roll_no,
            "dob": dob,
            "current_year": current_year,
            "branch": branch,
            "college": college
        }

        db.collection("users").document(user_id).set(user_data, merge=True)
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))

    # Retrieve user data
    user_doc = db.collection("users").document(user_id).get()
    user_data = user_doc.to_dict() if user_doc.exists else {}

    return render_template("profile.html", user=user_data)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if "user" not in session:
        return redirect(url_for("login"))  # Redirect if not logged in

    user_id = session["user"]["uid"]

    if request.method == 'POST':
        # Get all form values
        year = request.form.get('year')
        subject = request.form.get('subject')
        unit = request.form.get('unit')
        
        # Store/update in Firestore
        user_data = {
            'current_year': year,  # Use the same key as in profile
            'subject': subject,
            'unit': unit
        }
        
        # Update Firebase
        db.collection("users").document(user_id).set(user_data, merge=True)
        
        # Update session data to maintain values
        if 'user' in session:
            session['user']['year'] = year
            session['user']['subject'] = subject
            session['user']['unit'] = unit
            
        flash("Selections saved successfully", "success")
        return redirect(url_for("chat"))

    # Retrieve user data
    user_doc = db.collection("users").document(user_id).get()
    user_data = user_doc.to_dict() if user_doc.exists else {}
    
    # Update session with subject and unit if available
    if 'user' in session and user_data:
        session['user']['subject'] = user_data.get('subject')
        session['user']['unit'] = user_data.get('unit')

    return render_template("chat.html", user=user_data)

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

@app.route('/get_youtube_url/<subject>/<unit>')
def get_youtube_url(subject, unit):
    from youtube.youtube import get_youtube_url
    year = session['user'].get('year', '1Y')  # Default to 1Y if not set
    subject_code = subject_codes(subject)
    print(f"year: {year}, subject_code: {subject_code}, unit: {unit}")  # Debugging line
    url = get_youtube_url(year,subject_code, unit)
    if url:
        # Extract video ID for embedding
        video_id = url.split('v=')[1] if 'v=' in url else None
        return jsonify({"url": url, "video_id": video_id})
    else:
        return jsonify({"error": "Video not found"}), 404

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

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully!', 'success')
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
