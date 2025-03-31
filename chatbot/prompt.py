import csv
import os
import Syllabus.sub as sub  # Use sub.py instead of subjects.py

from langchain.prompts import PromptTemplate
from langchain_core.messages import SystemMessage

# System message template
SYSTEM_TEMPLATE = """
You are an AI educational assistant helping students with {subject}, specifically about {unit}.

Here is the syllabus context for this unit:
{syllabus_content}

Use this information to provide accurate, educational responses to the student's questions.
Be concise but thorough, and use examples where appropriate.
Format your responses using markdown for better readability.
"""

def get_syllabus_content(subject, unit):
    """Get syllabus content for a specific subject and unit"""
    # Extract the subject code if it's in the format "Subject Name (Code)"
    subject_code = subject
    if isinstance(subject, str) and "(" in subject and ")" in subject:
        subject_code = subject.split("(")[1].split(")")[0]
    
    # Call the function from sub.py
    return sub.get_syllabus_content(subject_code, unit)

def create_system_message(subject, unit):
    """Create a system message with the appropriate context"""
    syllabus_content = get_syllabus_content(subject, unit)
    return SystemMessage(content=SYSTEM_TEMPLATE.format(
        subject=subject,
        unit=unit,
        syllabus_content=syllabus_content
    ))