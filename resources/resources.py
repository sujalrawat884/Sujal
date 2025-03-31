import csv
import os

# Dictionary to store resources
resources = {}

# Base path for syllabus files
RESOURCE_BASE_PATH = ('./resources')

def load_resources_from_csv(file_path, resource_type):
    """
    Load data from a specific CSV file into the resources dictionary.
    :param file_path: Path to the CSV file.
    :param resource_type: Type of resource (e.g., 'Quantum', 'PYQ').
    """
    global resources
    if resource_type not in resources:
        resources[resource_type] = {}

    try:
        with open(file_path, mode='r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                subject = row.get('Subject')
                unit = row.get('Unit')
                drive_link = row.get('DriveLink')

                if not subject or not unit or not drive_link:
                    continue  # Skip rows with missing data

                if subject not in resources[resource_type]:
                    resources[resource_type][subject] = {}

                resources[resource_type][subject][unit] = drive_link
    except FileNotFoundError:
        print(f"Warning: File not found - {file_path}")
    except Exception as e:
        print(f"Error loading resources from {file_path}: {e}")

def load_all_resources():
    """
    Load all resource types from their respective CSV files.
    """
    resource_files = {
        'Quantum': 'Quantum.csv',
        'PYQ': 'PYQ.csv',
        'Sessional Paper': 'Sessional_Paper.csv',
        'Detailed Notes': 'Detailed_Notes.csv',
    }

    for resource_type, file_name in resource_files.items():
        file_path = os.path.join(RESOURCE_BASE_PATH, file_name)
        load_resources_from_csv(file_path, resource_type)

def get_drive_link(resource_type, subject, unit):
    """
    Retrieve the Google Drive link for the given resource type, subject, and unit.
    :param resource_type: Type of resource (e.g., 'Quantum', 'PYQ').
    :param subject: Subject code (e.g., 'BCS301').
    :param unit: Unit code (e.g., 'U1').
    :return: Google Drive link or None if not found.
    """
    print(f"Fetching link for {resource_type}, Subject: {subject}, Unit: {unit}")
    return resources.get(resource_type, {}).get(subject, {}).get(unit)

# Load all resources when the script is imported
load_all_resources()