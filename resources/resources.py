import csv
import os
from flask import current_app
from models import db
from Syllabus.sub import Unit

# Dictionary to store resources
resources = {}

# Base path for syllabus files
RESOURCE_BASE_PATH = ('./resources')

# Cache the resources to avoid frequent database queries
_resources_cache = {}

def load_resources_from_db():
    """
    This is maintained for compatibility but doesn't need to do anything
    since the data is already loaded in the Unit model
    """
    print("Resources are now integrated with Unit model")
    return True

def get_drive_link(resource_type, subject, unit):
    """
    Retrieve the Google Drive link for the given resource type, subject, and unit.
    
    Args:
        resource_type: Type of resource (e.g., 'Quantum', 'PYQ')
        subject: Subject code (e.g., 'BCS301')
        unit: Unit code (e.g., 'U1')
    
    Returns:
        Google Drive link or None if not found
    """
    # Map resource type to column name
    column_mapping = {
        'Quantum': 'quantum_link',
        'Detailed Notes': 'detailed_notes_link',
        'PYQ': 'pyq_link',
        'Sessional Paper': 'sessional_paper_link'
    }
    
    # Get the correct column name
    column_name = column_mapping.get(resource_type)
    if not column_name:
        return None
    
    try:
        # Query the unit directly
        unit_record = Unit.query.filter_by(
            subject_code=subject,
            unit_code=unit
        ).first()
        
        if unit_record:
            # Get the value from the appropriate column
            return getattr(unit_record, column_name)
    except Exception as e:
        print(f"Error retrieving drive link: {e}")
        
    return None

# Try to load resources immediately if possible
try:
    from flask import current_app
    with current_app.app_context():
        load_resources_from_db()
except RuntimeError:
    print("App context not available, resources will be loaded on first request")
except Exception as e:
    print(f"Error pre-loading resources: {e}")