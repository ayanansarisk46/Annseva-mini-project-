"""
================================================================================
AnnSeva - Database Models (models.py)
================================================================================
College Viva Note:
This file defines the Database Schema using Flask-SQLAlchemy (ORM).
Object-Relational Mapping (ORM) maps Python classes to database tables:
1. User: Stores registered Donors and NGOs with clean physical location/city.
2. Donation: Stores food donation requests and tracks status lifecycle.
3. Notification: Stores in-app alerts for Donors and NGOs.

Security: Passwords are encrypted using werkzeug.security (pbkdf2:sha256).
Location: Address/City based (no raw GPS coordinates required).
================================================================================
"""

from datetime import datetime, timezone
from typing import Any
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize SQLAlchemy instance (typed as Any to satisfy static analyzers)
db: Any = SQLAlchemy()

def get_utc_now():
    """Returns current UTC timestamp (Python 3.13+ compatible)."""
    return datetime.now(timezone.utc)

class User(db.Model, UserMixin):
    """
    User Table: Stores both Donors and NGOs.
    The 'role' column differentiates between 'DONOR' and 'NGO'.
    """
    __tablename__ = 'users'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'DONOR' or 'NGO'
    phone = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(255), nullable=False) # City / Area Address
    created_at = db.Column(db.DateTime, default=get_utc_now)

    # Relationships
    donations_made = db.relationship('Donation', backref='donor', lazy=True, foreign_keys='Donation.donor_id', cascade="all, delete-orphan", passive_deletes=True)
    donations_accepted = db.relationship('Donation', backref='ngo', lazy=True, foreign_keys='Donation.ngo_id')
    notifications = db.relationship('Notification', backref='recipient', lazy=True, cascade="all, delete-orphan", passive_deletes=True)

    def set_password(self, raw_password):
        """Hashes the plain password before saving in database."""
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        """Validates a submitted password against stored hash."""
        return check_password_hash(self.password, raw_password)

    def is_donor(self):
        return self.role == 'DONOR'

    def is_ngo(self):
        return self.role == 'NGO'

    def is_admin(self):
        return self.role == 'ADMIN'

    def to_dict(self):
        """Returns dictionary representation for JSON/API."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'phone': self.phone,
            'location': self.location
        }

    def __repr__(self):
        return f"<User {self.id}: {self.name} ({self.role})>"


class Donation(db.Model):
    """
    Donation Table: Represents a food donation request.
    Tracks lifecycle: PENDING -> ACCEPTED -> COMPLETED (or REJECTED).
    """
    __tablename__ = 'donations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    ngo_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    food_type = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), default='kg') # 'kg', 'meals', 'packets'
    location = db.Column(db.String(255), nullable=False) # Pickup Address / Locality

    pickup_date = db.Column(db.Date, nullable=False)
    pickup_time = db.Column(db.String(30), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Donation lifecycle: 'PENDING', 'ACCEPTED', 'PICKED UP', 'COMPLETED', 'REJECTED'
    status = db.Column(db.String(20), default='PENDING', nullable=False, index=True)

    created_at = db.Column(db.DateTime, default=get_utc_now)
    completed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        """Returns JSON-compatible dictionary for frontend and live reports."""
        return {
            'id': self.id,
            'donor_id': self.donor_id,
            'donor_name': self.donor.name if self.donor else "Unknown",
            'ngo_id': self.ngo_id,
            'ngo_name': self.ngo.name if self.ngo else "Not Assigned",
            'food_type': self.food_type,
            'quantity': self.quantity,
            'unit': self.unit,
            'location': self.location,
            'pickup_date': self.pickup_date.strftime('%Y-%m-%d') if self.pickup_date else '',
            'pickup_time': self.pickup_time,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else '',
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M') if self.completed_at else ''
        }

    def __repr__(self):
        return f"<Donation {self.id}: {self.food_type} - {self.quantity}{self.unit} ({self.status})>"


class Notification(db.Model):
    """
    Notification Table: Stores in-app alerts for users.
    Triggers when food is submitted, assigned, accepted, rejected, or completed.
    """
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=get_utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%d %b %Y, %I:%M %p') if self.created_at else ''
        }

    def __repr__(self):
        return f"<Notification {self.id} for User {self.user_id}: {self.message[:20]}>"
