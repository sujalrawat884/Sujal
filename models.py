from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    roll_no = db.Column(db.String(20))
    dob = db.Column(db.String(20))
    current_year = db.Column(db.String(10))
    branch = db.Column(db.String(100))
    college = db.Column(db.String(200))
    email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Store subject and unit preferences
    subject = db.Column(db.String(100))
    unit = db.Column(db.String(50))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_session_dict(self):
        """Convert user data to dictionary for session storage"""
        return {
            'uid': self.id,
            'email': self.email,
            'name': self.name,
            'year': self.current_year,
            'subject': self.subject,
            'unit': self.unit
        }