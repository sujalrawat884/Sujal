import csv
import os

# Comprehensive dictionary mapping course codes to subject names
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
# Note: If multiple codes map to the same subject, this will only keep the last one
subject_to_code = {v: k for k, v in course_codes.items()}

# Base path for syllabus files
SYLLABUS_BASE_PATH = ".\Syllabus"

# Year mapping for display names and file access
year_display = {
    "1": "1st Year",
    "2": "2nd Year",
    "3": "3rd Year",
    "4": "4th Year"
}

# File mapping (which CSV file to use for each year)
year_to_file = {
    "1": "1Y.csv",
    "2": "2Y.csv",
    "3": "3Y.csv",
    "4": "4Y.csv"
}

def load_data_from_csv():
    """
    Load all subject and unit data directly from CSV files
    
    Returns:
        subjects_by_year: Dictionary mapping year numbers to lists of subjects
        units_by_subject: Dictionary mapping subject names to their units with topics
    """
    subjects_by_year = {
        "1": set(),
        "2": set(),
        "3": set(),
        "4": set()
    }
    
    units_by_subject = {}  # Maps subject names to their units with topics
    
    # Process each year file
    for year, filename in year_to_file.items():
        csv_path = os.path.join(SYLLABUS_BASE_PATH, filename)
        if os.path.exists(csv_path):
            try:
                with open(csv_path, 'r', encoding='windows-1252') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        # Get subject name from the CSV
                        subject = row.get('Subject')
                        if not subject:
                            continue
                            
                        # Add to the year (use year from CSV or default to file's year)
                        csv_year = row.get('Year', year).replace('Y', '')  # Convert '2Y' to '2' if needed
                        if csv_year in subjects_by_year:
                            subjects_by_year[csv_year].add(subject)
                        
                        # Add unit information
                        unit_code = row.get('Unit')
                        if unit_code and subject:
                            if subject not in units_by_subject:
                                units_by_subject[subject] = {}
                                
                            topic = row.get('Topic', f"Topic for {unit_code}")
                            units_by_subject[subject][unit_code] = {
                                'topic': topic,
                                'content': row.get('Content', ''),
                                'learning_objectives': row.get('Learning_Objectives', '')
                            }
            except Exception as e:
                print(f"Error reading {csv_path}: {e}")
    
    # Convert sets to lists for JSON serialization
    for year in subjects_by_year:
        subjects_by_year[year] = list(subjects_by_year[year])
    
    return subjects_by_year, units_by_subject

# Load data from CSV files
subjects_by_year, units_by_subject = load_data_from_csv()

# Helper functions
def get_subject_name(code):
    """Get subject name from course code"""
    return course_codes.get(code, f"Unknown Subject ({code})")

def get_subject_code(name):
    """Get course code from subject name"""
    return subject_to_code.get(name, "Unknown")

def get_subjects_by_year(year):
    """
    Get list of subjects for a specific year
    
    Args:
        year: Year number (1, 2, 3, 4) or display name (1st Year, 2nd Year)
    """
    # Convert display name to number if needed
    if year in year_display.values():
        for num, name in year_display.items():
            if name == year:
                year = num
                break
    
    # Get subject codes for the given year
    subject_codes = subjects_by_year.get(str(year), [])
    
    # Convert codes to full names using the course_codes dictionary
    subject_names_and_codes = []
    for code in subject_codes:
        name = get_subject_name(code)
        # Add both name and code for display
        subject_names_and_codes.append(f"{name} ({code})")
    
    return subject_names_and_codes

def get_units_for_subject(subject):
    """
    Get all units for a specific subject with topics as display text
    
    Args:
        subject: Can be subject code, name, or "Name (Code)" format
        
    Returns dictionary with format: {"U1": "Topic name"}
    """
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
    if subject in subject_to_code:
        code = subject_to_code[subject]
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
    # Strip any "Unit " prefix if it exists
    unit_code = unit
    if isinstance(unit, str) and unit.startswith("Unit "):
        unit_num = unit.split(" ")[1]
        unit_code = f"U{unit_num}"
    
    # Get unit data
    if subject in units_by_subject and unit_code in units_by_subject[subject]:
        unit_data = units_by_subject[subject][unit_code]
        
        # Format the content
        content_parts = []
        
        if 'topic' in unit_data:
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
