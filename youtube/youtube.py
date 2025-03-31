import csv
import os

# Function to load links from CSV file by year
def load_links_by_year(subject_year):
    """
    Load YouTube links from CSV file filtered by year
    
    Args:
        year: The year number as a string (e.g., "3" or "4")
    
    Returns:
        Dictionary of links organized by subject and unit
    """
    links = {}
    csv_path = os.path.join(os.path.dirname(__file__), "2Y_link.csv")
    
    try:
        with open(csv_path, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row
            
            for row in reader:
                if len(row) >= 3:
                    subject, unit, link = row
                    
                    if subject not in links:
                        links[subject] = {}
                        
                    # Only add if there's a valid link
                    if link.strip():
                        links[subject][unit] = link
    except Exception as e:
        print(f"Error loading CSV: {e}")
    
    return links

# Helper function to get YouTube URL for a subject and unit
def get_youtube_url(year,subject, unit):
    """
    Get YouTube URL for the given subject and unit
    
    Args:
        subject: BCS301, BCS302, etc. (subject code)
        unit: Unit code (e.g., 'U1')
        
    Returns:
        YouTube URL as string or None if not found
    """

    # If not found, try loading from CSV by year
    if year:
        year_links = load_links_by_year(year)
        if subject in year_links and unit in year_links[subject]:
            return year_links[subject][unit]
    
    return None