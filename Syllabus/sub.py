import os
from dotenv import load_dotenv
from flask import current_app
from models import db
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables
load_dotenv()

# Comprehensive dictionary mapping course codes to subject names (keep as fallback)
course_codes = {
    "BAS101": "Engineering Physics",
    "BAS102": "Engineering Chemistry",
    "BEE101": "Fundamentals of Electrical Engineering",
    "BEC101": "Fundamentals of Electronics Engineering",
    "BCS101": "Programming for Problem Solving",
    "BME101": "Fundamentals of Mechanical Engineering",
    "BAS103": "Engineering Mathematics-I",
    "BAS203": "Engineering Mathematics-II",
    "BAS204": "Environment and Ecology",
    "BAS105": "Soft Skills",

    # 3rd Semester Courses (300 level)
    "BAS303": "Math IV",
    "BVE301": "Universal Human Value and Professional Ethics",
    "BAS301": "Technical Communication",
    "BCS301": "Data Structure",
    "BCS302": "Computer Organization and Architecture",
    "BCS303": "Discrete Structures & Theory of Logic",
    "BCC301": "Cyber Security",
    "BCC302": "Python Programming",
    
    # 4th Semester Courses (400 level)
    "BOE404": "Energy Science & Engineering",
    "BVE401": "Universal Human Value and Professional Ethics",
    "BCS401": "Operating System",
    "BCS402": "Theory of Automata and Formal Languages",
    "BCS403": "Object Oriented Programming with Java",
    
    # 5th Semester Courses (500 level)
    "BCS501": "Database Management System",
    "BCAI501": "Artificial Intelligence",
    "BCS503": "Design and Analysis of Algorithm",
    
    # 6th Semester Courses (600 level)
    "BCS601": "Software Engineering",
    "BCAI601": "Machine Learning Techniques",
    "BCS603": "Computer Networks",
    
    # Elective Courses
    "BCAM061": "Social Media Analytics and Data Analysis",
    "BCS056": "Application of Soft Computing",
    "BCS054": "Object Oriented System Design with C++",
    "BNC501": "Constitution of India",
    "BOE068": "Software Project Management",
    "BNC502": "ESSENCE OF INDIAN TRADITIONAL KNOWLEDGE"

}

# Reverse mapping (subject name to code)
subject_to_code = {v: k for k, v in course_codes.items()}

# Year mapping for display names
year_display = {
    "1": "1st Year",
    "2": "2nd Year",
    "3": "3rd Year",
    "4": "4th Year"
}

# Create SQLAlchemy models
class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(15), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    year = db.Column(db.String(10), nullable=False)
    
    units = db.relationship('Unit', backref='subject', cascade="all, delete-orphan")

class Unit(db.Model):
    __tablename__ = 'units'
    id = db.Column(db.Integer, primary_key=True)
    subject_code = db.Column(db.String(15), db.ForeignKey('subjects.code'), nullable=False)
    unit_code = db.Column(db.String(5), nullable=False)
    topic = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text)
    learning_objectives = db.Column(db.Text)
    
    # Resource links
    quantum_link = db.Column(db.String(255))
    detailed_notes_link = db.Column(db.String(255))
    pyq_link = db.Column(db.String(255))
    sessional_paper_link = db.Column(db.String(255))
    
    __table_args__ = (db.UniqueConstraint('subject_code', 'unit_code'),)

# Cache results to avoid frequent database queries
_subjects_by_year_cache = None
_units_by_subject_cache = None
# Initialize empty data structures - will be populated on first use
subjects_by_year = {}
units_by_subject = {}

def load_data_from_db():
    """
    Load all subject and unit data from database using SQLAlchemy
    
    Returns:
        subjects_by_year: Dictionary mapping year numbers to lists of subjects
        units_by_subject: Dictionary mapping subject codes to their units with topics
    """
    global _subjects_by_year_cache, _units_by_subject_cache
    
    # Return cached results if available
    if _subjects_by_year_cache and _units_by_subject_cache:
        return _subjects_by_year_cache, _units_by_subject_cache
    
    subjects_by_year = {"1": [], "2": [], "3": [], "4": []}
    units_by_subject = {}
    
    # Load subjects
    subjects = Subject.query.all()
    
    # Organize subjects by year
    for subject in subjects:
        # Handle different year formats safely
        year_val = subject.year
        
        # Convert to string if it's an integer
        if isinstance(year_val, int):
            year = str(year_val)
        elif isinstance(year_val, str):
            # Extract the first digit if it's a string like "1Y" or "Year 1"
            year = ''.join(filter(str.isdigit, year_val[:2]))
        else:
            # Default if the year is None or another type
            year = "1"
        
        # Add subject to the corresponding year
        if year in subjects_by_year:
            subjects_by_year[year].append(subject.code)
        else:
            # Default to year 1 if invalid
            subjects_by_year["1"].append(subject.code)
    
    try:
        # Use SQLAlchemy to query the database
        from flask import current_app
        with current_app.app_context():
            # Get all units
            units = Unit.query.all()
            
            # Organize units by subject
            for unit in units:
                subject_code = unit.subject_code
                if subject_code not in units_by_subject:
                    units_by_subject[subject_code] = {}
                    
                units_by_subject[subject_code][unit.unit_code] = {
                    'topic': unit.topic,
                    'content': unit.content,
                    'learning_objectives': unit.learning_objectives
                }
            
            # Cache results
            _subjects_by_year_cache = subjects_by_year
            _units_by_subject_cache = units_by_subject
            
            return subjects_by_year, units_by_subject
            
    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        # Fallback to empty structure
        return subjects_by_year, units_by_subject
    except RuntimeError as e:
        print(f"Flask error: {e}")
        # Fallback when app context is not available
        return subjects_by_year, units_by_subject

# Helper functions using SQLAlchemy instead of direct MySQL
def get_subject_name(code):
    """Get subject name from course code"""
    try:
        subject = Subject.query.filter_by(code=code).first()
        if subject:
            return subject.name
    except Exception as e:
        print(f"Error retrieving subject name: {e}")
        
    # Fallback to dictionary
    return course_codes.get(code, f"Unknown Subject ({code})")

def get_subject_code(name):
    """Get course code from subject name"""
    try:
        subject = Subject.query.filter_by(name=name).first()
        if subject:
            return subject.code
    except Exception as e:
        print(f"Error retrieving subject code: {e}")
    
    # Fallback to reverse lookup
    return subject_to_code.get(name, "Unknown")

def get_subjects_by_year(year):
    """
    Get list of subjects for a specific year
    
    Args:
        year: Year number (1, 2, 3, 4) or display name (1Y, 2Y, etc.)
    """
    # Make sure data is loaded
    global subjects_by_year, units_by_subject
    if not subjects_by_year:
        subjects_by_year, units_by_subject = load_data_from_db()
    
    # Normalize year input to just the number
    year_str = ''.join(filter(str.isdigit, str(year)[:2]))
    
    # Debug output to see what's being requested and what's available
    print(f"Requested year: {year}, normalized to {year_str}")
    print(f"Available years and subject counts: {[(y, len(s)) for y, s in subjects_by_year.items()]}")
    
    # Get subject codes for the given year
    subject_codes_list = subjects_by_year.get(year_str, [])
    
    # Convert codes to full names with code format
    subject_names_and_codes = []
    for code in subject_codes_list:
        name = get_subject_name(code)
        subject_names_and_codes.append(f"{name} ({code})")
    
    return subject_names_and_codes

def get_units_for_subject(subject):
    """
    Get all units for a specific subject with topics as display text
    
    Args:
        subject: Can be subject code, name, or "Name (Code)" format
    """
    # Make sure data is loaded
    global subjects_by_year, units_by_subject
    if not units_by_subject:
        subjects_by_year, units_by_subject = load_data_from_db()
        
    # Extract code if in "Subject Name (Code)" format
    if "(" in subject and ")" in subject:
        subject = subject.split("(")[1].split(")")[0]
    
    # Try direct lookup first (if it's already a code)
    if subject in units_by_subject:
        result = {}
        for unit_code, unit_data in units_by_subject[subject].items():
            result[unit_code] = unit_data['topic']
        return result
    
    # If not found and it might be a subject name, try to get the code
    code = get_subject_code(subject)
    if code in units_by_subject:
        result = {}
        for unit_code, unit_data in units_by_subject[code].items():
            result[unit_code] = unit_data['topic']
        return result
    
    return {}

def get_syllabus_content(subject, unit):
    """
    Get detailed syllabus content for a subject and unit
    """
    # Make sure data is loaded
    global subjects_by_year, units_by_subject
    if not units_by_subject:
        subjects_by_year, units_by_subject = load_data_from_db()
        
    # Strip any "Unit " prefix if it exists
    unit_code = unit
    if isinstance(unit, str) and unit.startswith("Unit "):
        unit_num = unit.split(" ")[1]
        unit_code = f"U{unit_num}"
    
    # Extract subject code if needed
    if "(" in subject and ")" in subject:
        subject = subject.split("(")[1].split(")")[0]
        
    # Get unit data
    if subject in units_by_subject and unit_code in units_by_subject[subject]:
        unit_data = units_by_subject[subject][unit_code]
        
        # Format the content
        content_parts = []
        
        if 'topic' in unit_data and unit_data['topic']:
            content_parts.append(f"**Topic:** {unit_data['topic']}")
            
        if 'content' in unit_data and unit_data['content']:
            content = unit_data['content'].replace(';', '\n- ')
            content_parts.append(f"**Content:**\n- {content}")
            
        if 'learning_objectives' in unit_data and unit_data['learning_objectives']:
            objectives = unit_data['learning_objectives'].split(';')
            obj_list = "\n".join([f"- {obj.strip()}" for obj in objectives if obj.strip()])
            content_parts.append(f"**Learning Objectives:**\n{obj_list}")
        
        return "\n\n".join(content_parts)
    
    return f"No syllabus content found for {subject} - {unit}"

def reload_data():
    """Force reload data from the database"""
    global _subjects_by_year_cache, _units_by_subject_cache, subjects_by_year, units_by_subject
    _subjects_by_year_cache = None
    _units_by_subject_cache = None
    subjects_by_year, units_by_subject = load_data_from_db()
    return subjects_by_year, units_by_subject
