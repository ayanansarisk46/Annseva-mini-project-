"""
================================================================================
AnnSeva - Food Donation and Management System
Main Application Controller (app.py)
================================================================================
College Viva Overview:
----------------------
This file is the core Flask application controller. It manages:
1. Application initialization, configuration, and live server endpoints.
2. User authentication (Flask-Login, Password Hashing, Session Management).
3. Role-Based Access Control (RBAC) separating DONOR and NGO roles.
4. Donation submission, status workflow, and NGO locality matching.
5. In-app notifications triggering on workflow events.
6. Live API routes for interactive Maps, live reports, and background polling.
================================================================================
"""

from datetime import datetime, date, timezone
from functools import wraps
from typing import Any
from flask import (
    Flask, render_template, request, redirect, url_for, flash, jsonify
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)

# Static type annotation for IDE analyzers (Pylance / Pyright)
current_user: Any = current_user

# Import local configurations, models, and services
from config import Config
from models import db, User, Donation, Notification
from services.matching import match_suitable_ngo
from services.geocoding import resolve_location_coordinates
from services.email_service import send_email_notification
from services.reports import get_report_statistics
from seed_data import seed_database, sync_database_schema

# ------------------------------------------------------------------------------
# 1. APPLICATION & EXTENSIONS INITIALIZATION
# ------------------------------------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = Config.get_database_uri()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database ORM
db.init_app(app)

# Initialize Flask-Login for Session Authentication
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = "Please login to access this page."
login_manager.login_message_category = "warning"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login helper: Loads the logged-in User object by user_id from session."""
    return db.session.get(User, int(user_id))


# ------------------------------------------------------------------------------
# 2. ROLE-BASED ACCESS CONTROL (RBAC) DECORATORS
# ------------------------------------------------------------------------------
def role_required(required_role):
    """
    Decorator to restrict route access by user role.
    Prevents unauthorized access across Donor, NGO, and Admin panels.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'success': False, 'error': 'Authentication required.'}), 401
                return login_manager.unauthorized()
            if current_user.role != required_role:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'success': False, 'error': f'Access denied! {required_role} role required.'}), 403
                if required_role == 'ADMIN':
                    return redirect(url_for('switch_to_admin'))
                flash(f"Access denied! This area is restricted to {required_role} users.", "danger")
                if current_user.role == 'DONOR':
                    return redirect(url_for('donor_dashboard'))
                elif current_user.role == 'NGO':
                    return redirect(url_for('ngo_dashboard'))
                elif current_user.role == 'ADMIN':
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ------------------------------------------------------------------------------
# 3. CONTEXT PROCESSOR (Injects notification count & maps key globally)
# ------------------------------------------------------------------------------
@app.context_processor
def inject_global_template_vars():
    """Injects unread notification counts, Google Maps key, and year into templates."""
    unread_count = 0
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(
            user_id=current_user.id, is_read=False
        ).count()
    return {
        'unread_notifications_count': unread_count,
        'google_maps_api_key': Config.GOOGLE_MAPS_API_KEY,
        'current_year': datetime.now(timezone.utc).year
    }


# ------------------------------------------------------------------------------
# 4. PUBLIC ROUTES
# ------------------------------------------------------------------------------
@app.route('/')
def index():
    """Home landing page with project mission, workflow overview, and quick stats."""
    stats = get_report_statistics()
    return render_template('index.html', stats=stats)


@app.route('/about')
def about():
    """About page explaining the AnnSeva mission, architecture, and technology stack."""
    return render_template('about.html')


# ------------------------------------------------------------------------------
# 5. AUTHENTICATION MODULE (REGISTER, LOGIN, LOGOUT, PROFILE)
# ------------------------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    User Registration:
    Supports registering as either 'DONOR' or 'NGO'.
    Validates form fields, hashes password with Werkzeug, and prevents duplicate emails.
    Clean address/location based (no GPS coordinates needed).
    """
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('donor_dashboard' if current_user.is_donor() else 'ngo_dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'DONOR').strip().upper()
        phone = request.form.get('phone', '').strip()
        location = request.form.get('location', '').strip()

        # Validation checks
        if not name or not email or not password or not role or not location or not phone:
            flash("All required fields must be filled.", "danger")
            return render_template('register.html')

        # Phone number validation: strictly digits only, exactly 10 digits
        if not phone.isdigit() or len(phone) != 10:
            flash("Invalid phone number! Phone number must be exactly 10 digits (numbers only) and cannot contain letters, variables, or symbols.", "danger")
            return render_template('register.html')

        if role not in ['DONOR', 'NGO']:
            flash("Invalid role selected. Must be DONOR or NGO.", "danger")
            return render_template('register.html')

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template('register.html')

        # Check if email is already registered
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("An account with this email already exists. Please login instead.", "warning")
            return render_template('register.html')

        # Create new user and hash password
        new_user = User(
            name=name,
            email=email,
            role=role,
            phone=phone,
            location=location
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        # Send welcome notification in-app
        welcome_msg = f"Welcome to AnnSeva, {name}! Your account as {role} is successfully created."
        notif = Notification(user_id=new_user.id, message=welcome_msg)
        db.session.add(notif)
        db.session.commit()

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    User Login:
    Verifies credentials using password hash verification.
    Redirects user automatically to their corresponding role dashboard.
    """
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('donor_dashboard' if current_user.is_donor() else 'ngo_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template('login.html')

        user = User.query.filter_by(email=email).first()

        # Verify user existence and password hash
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f"Welcome back, {user.name}!", "success")

            # Role-based redirection
            if user.role == 'DONOR':
                return redirect(url_for('donor_dashboard'))
            elif user.role == 'NGO':
                return redirect(url_for('ngo_dashboard'))
            elif user.role == 'ADMIN':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
        else:
            flash("Invalid email or password. Please try again.", "danger")

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logs out the active user session and redirects to login page."""
    logout_user()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('login'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """View and update profile information (name, phone, address, password)."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        location = request.form.get('location', '').strip()
        new_password = request.form.get('new_password', '').strip()

        if not name or not location or not phone:
            flash("Name, Phone number, and Location cannot be empty.", "danger")
            return render_template('profile.html', user=current_user)

        # Phone number validation: strictly digits only, exactly 10 digits
        if not phone.isdigit() or len(phone) != 10:
            flash("Invalid phone number! Phone number must be exactly 10 digits (numbers only) and cannot contain letters, variables, or symbols.", "danger")
            return render_template('profile.html', user=current_user)

        current_user.name = name
        current_user.phone = phone
        current_user.location = location

        if new_password:
            if len(new_password) < 6:
                flash("New password must be at least 6 characters.", "warning")
                return render_template('profile.html', user=current_user)
            current_user.set_password(new_password)
            flash("Password updated successfully.", "info")

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile'))

    return render_template('profile.html', user=current_user)


# ------------------------------------------------------------------------------
# 6. DONOR MODULE
# ------------------------------------------------------------------------------
@app.route('/donor/dashboard')
@login_required
@role_required('DONOR')
def donor_dashboard():
    """
    Donor Dashboard:
    Displays status summary cards (Total, Pending, Accepted, Completed),
    recent donation requests, and quick notification snippets.
    """
    my_donations = Donation.query.filter_by(donor_id=current_user.id).order_by(Donation.created_at.desc()).all()

    total_count = len(my_donations)
    pending_count = sum(1 for d in my_donations if d.status == 'PENDING')
    accepted_count = sum(1 for d in my_donations if d.status == 'ACCEPTED')
    completed_count = sum(1 for d in my_donations if d.status == 'COMPLETED')

    recent_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all()

    return render_template(
        'donor_dashboard.html',
        donations=my_donations[:5],
        total_count=total_count,
        pending_count=pending_count,
        accepted_count=accepted_count,
        completed_count=completed_count,
        notifications=recent_notifications
    )


@app.route('/donor/add-donation', methods=['GET', 'POST'])
@login_required
@role_required('DONOR')
def add_donation():
    """
    Add Food Donation:
    1. Validates food details (type, quantity, pickup date/time, physical address).
    2. Stores donation in database with 'PENDING' status.
    3. Runs Matching Engine (services/matching.py) to find nearest suitable NGO by locality/city.
    4. Assigns the selected NGO to the donation.
    5. Dispatches in-app and email notifications.
    """
    if request.method == 'POST':
        food_type = request.form.get('food_type', '').strip()
        quantity_raw = request.form.get('quantity', '').strip()
        unit = request.form.get('unit', 'kg').strip()
        location = request.form.get('location', '').strip()
        pickup_date_raw = request.form.get('pickup_date', '').strip()
        pickup_time = request.form.get('pickup_time', '').strip()
        description = request.form.get('description', '').strip()

        # Validation
        if not food_type or not quantity_raw or not location or not pickup_date_raw or not pickup_time:
            flash("Please fill in all required food donation details.", "danger")
            return render_template('add_donation.html')

        try:
            quantity = float(quantity_raw)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            flash("Quantity must be a positive number.", "danger")
            return render_template('add_donation.html')

        try:
            pickup_date_obj = datetime.strptime(pickup_date_raw, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
            return render_template('add_donation.html')

        # 1. Create Donation Record
        donation = Donation(
            donor_id=current_user.id,
            food_type=food_type,
            quantity=quantity,
            unit=unit,
            location=location,
            pickup_date=pickup_date_obj,
            pickup_time=pickup_time,
            description=description,
            status='PENDING'
        )

        # 2. Run Locality/City Matching Logic to find nearest suitable NGO
        matched_ngo, match_reason = match_suitable_ngo(donation_location=location)

        if matched_ngo:
            donation.ngo_id = matched_ngo.id

        db.session.add(donation)
        db.session.commit()

        # 3. Create Notification for the assigned NGO
        if matched_ngo:
            ngo_alert_msg = (
                f"New food donation alert: '{food_type}' ({quantity} {unit}) from {current_user.name}. "
                f"Pickup Location: {location}. {match_reason}"
            )
            ngo_notif = Notification(user_id=matched_ngo.id, message=ngo_alert_msg)
            db.session.add(ngo_notif)

            # Trigger email notification structure
            send_email_notification(
                recipient_email=matched_ngo.email,
                subject="AnnSeva - New Food Donation Assigned to Your NGO",
                body_text=f"Dear {matched_ngo.name},\n\n{ngo_alert_msg}\n\nPlease login to AnnSeva to view details and accept the pickup."
            )

        # 4. Create Notification for the Donor confirming submission
        donor_alert_msg = f"Your food donation for '{food_type}' was submitted successfully."
        if matched_ngo:
            donor_alert_msg += f" Assigned to: {matched_ngo.name} ({match_reason})."
        donor_notif = Notification(user_id=current_user.id, message=donor_alert_msg)
        db.session.add(donor_notif)
        db.session.commit()

        flash(f"Donation posted successfully! {match_reason if matched_ngo else ''}", "success")
        return redirect(url_for('donation_details', donation_id=donation.id))

    return render_template('add_donation.html')


@app.route('/donor/donations')
@login_required
@role_required('DONOR')
def my_donations():
    """List of all donations created by the logged-in Donor."""
    status_filter = request.args.get('status', '').upper()
    query = Donation.query.filter_by(donor_id=current_user.id)

    if status_filter in ['PENDING', 'ACCEPTED', 'PICKED UP', 'REJECTED', 'COMPLETED']:
        query = query.filter_by(status=status_filter)

    donations = query.order_by(Donation.created_at.desc()).all()
    return render_template('donations.html', donations=donations, current_filter=status_filter, user_role='DONOR')


# ------------------------------------------------------------------------------
# 7. NGO MODULE
# ------------------------------------------------------------------------------
@app.route('/ngo/dashboard')
@login_required
@role_required('NGO')
def ngo_dashboard():
    """
    NGO Dashboard:
    Shows summary metrics (Available Requests, Accepted, Completed pickups),
    list of pending donation requests available for acceptance, and notifications.
    """
    available_donations = Donation.query.filter_by(status='PENDING').order_by(Donation.created_at.desc()).all()
    accepted_donations = Donation.query.filter(
        Donation.ngo_id == current_user.id,
        Donation.status.in_(['ACCEPTED', 'PICKED UP'])
    ).all()
    completed_donations = Donation.query.filter_by(ngo_id=current_user.id, status='COMPLETED').all()

    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all()

    return render_template(
        'ngo_dashboard.html',
        available_donations=available_donations,
        available_count=len(available_donations),
        accepted_donations=accepted_donations,
        accepted_count=len(accepted_donations),
        completed_count=len(completed_donations),
        notifications=notifications
    )


@app.route('/ngo/available')
@login_required
@role_required('NGO')
def available_donations():
    """List of all available pending food donations that this NGO can accept."""
    donations = Donation.query.filter_by(status='PENDING').order_by(Donation.created_at.desc()).all()
    return render_template('donations.html', donations=donations, current_filter='PENDING', user_role='NGO', page_title="Available Food Donations")


@app.route('/ngo/accepted')
@login_required
@role_required('NGO')
def accepted_donations():
    """List of donations accepted or in pickup by this NGO awaiting completion."""
    donations = Donation.query.filter(
        Donation.ngo_id == current_user.id,
        Donation.status.in_(['ACCEPTED', 'PICKED UP'])
    ).order_by(Donation.created_at.desc()).all()
    return render_template('donations.html', donations=donations, current_filter='ACCEPTED', user_role='NGO', page_title="Accepted Food Pickups")


@app.route('/ngo/accept/<int:donation_id>', methods=['GET', 'POST'])
@login_required
@role_required('NGO')
def accept_donation(donation_id):
    """
    NGO Accepts Donation:
    1. Changes status to 'ACCEPTED'.
    2. Assigns current NGO.
    3. Creates notification for Donor.
    4. Sends confirmation email to Donor.
    """
    donation = db.get_or_404(Donation, donation_id)

    if donation.status != 'PENDING':
        flash(f"Donation #{donation.id} is already {donation.status}.", "warning")
        return redirect(url_for('ngo_dashboard'))

    donation.status = 'ACCEPTED'
    donation.ngo_id = current_user.id
    db.session.commit()

    # Notify Donor
    donor_msg = (
        f"Great news! Your food donation #{donation.id} ({donation.food_type}) "
        f"has been ACCEPTED by NGO: {current_user.name}. Contact: {current_user.phone or 'N/A'}."
    )
    donor_notif = Notification(user_id=donation.donor_id, message=donor_msg)
    db.session.add(donor_notif)
    db.session.commit()

    # Email notification
    if donation.donor and donation.donor.email:
        send_email_notification(
            recipient_email=donation.donor.email,
            subject="AnnSeva - Your Food Donation Has Been Accepted!",
            body_text=f"Dear {donation.donor.name},\n\n{donor_msg}\n\nThe NGO will arrive at the scheduled pickup time: {donation.pickup_time} on {donation.pickup_date}."
        )

    flash(f"You have accepted donation #{donation.id}. The donor has been notified.", "success")
    return redirect(url_for('accepted_donations'))


@app.route('/ngo/reject/<int:donation_id>', methods=['GET', 'POST'])
@login_required
@role_required('NGO')
def reject_donation(donation_id):
    """
    NGO Rejects Donation:
    1. Changes status to 'REJECTED'.
    2. Creates notification for Donor.
    """
    donation = db.get_or_404(Donation, donation_id)

    if donation.status != 'PENDING':
        flash(f"Cannot reject donation #{donation.id} as it is already {donation.status}.", "warning")
        return redirect(url_for('ngo_dashboard'))

    donation.status = 'REJECTED'
    db.session.commit()

    # Notify Donor
    donor_msg = (
        f"Update: Your food donation #{donation.id} ({donation.food_type}) "
        f"could not be accepted at this time by {current_user.name}."
    )
    donor_notif = Notification(user_id=donation.donor_id, message=donor_msg)
    db.session.add(donor_notif)
    db.session.commit()

    flash(f"Donation #{donation.id} was marked as rejected.", "info")
    return redirect(url_for('ngo_dashboard'))


@app.route('/ngo/pickup/<int:donation_id>', methods=['GET', 'POST'])
@login_required
@role_required('NGO')
def pickup_donation(donation_id):
    """
    NGO Marks Food as Picked Up:
    1. Changes status to 'PICKED UP'.
    2. Notifies Donor.
    """
    donation = db.get_or_404(Donation, donation_id)

    if donation.ngo_id and donation.ngo_id != current_user.id:
        flash("You are not authorized to update pickup status for this donation.", "danger")
        return redirect(url_for('ngo_dashboard'))

    if donation.status not in ['ACCEPTED', 'PICKED UP']:
        flash(f"Donation must be in ACCEPTED status before marking as picked up. Current: {donation.status}.", "warning")
        return redirect(url_for('accepted_donations'))

    donation.ngo_id = current_user.id
    donation.status = 'PICKED UP'
    db.session.commit()

    # Notify Donor
    donor_msg = (
        f"Update: NGO {current_user.name} has arrived and marked donation #{donation.id} "
        f"({donation.food_type}) as PICKED UP. Food transportation and distribution is now underway!"
    )
    donor_notif = Notification(user_id=donation.donor_id, message=donor_msg)
    db.session.add(donor_notif)
    db.session.commit()

    # Email notification
    if donation.donor and donation.donor.email:
        send_email_notification(
            recipient_email=donation.donor.email,
            subject=f"AnnSeva - Donation #{donation.id} Picked Up",
            body_text=f"Dear {donation.donor.name},\n\n{donor_msg}"
        )

    flash(f"Donation #{donation.id} marked as PICKED UP! Transportation/distribution underway.", "success")
    return redirect(url_for('accepted_donations'))


@app.route('/ngo/complete/<int:donation_id>', methods=['GET', 'POST'])
@login_required
@role_required('NGO')
def complete_donation(donation_id):
    """
    NGO Marks Donation as Completed (Picked Up & Distributed):
    1. Updates status to 'COMPLETED'.
    2. Sets completed_at timestamp.
    3. Notifies Donor and increments food saved metrics.
    """
    donation = db.get_or_404(Donation, donation_id)

    if donation.ngo_id and donation.ngo_id != current_user.id:
        flash("You are not authorized to complete this donation.", "danger")
        return redirect(url_for('ngo_dashboard'))

    if donation.status not in ['ACCEPTED', 'PICKED UP']:
        flash(f"Donation must be in ACCEPTED or PICKED UP status before completing. Current: {donation.status}.", "warning")
        return redirect(url_for('accepted_donations'))

    donation.ngo_id = current_user.id
    donation.status = 'COMPLETED'
    donation.completed_at = datetime.now(timezone.utc)
    db.session.commit()

    # Notify Donor
    donor_msg = (
        f"Success! Your food donation #{donation.id} ({donation.quantity} {donation.unit} of {donation.food_type}) "
        f"has been successfully collected and distributed by {current_user.name}. Thank you for preventing food waste!"
    )
    donor_notif = Notification(user_id=donation.donor_id, message=donor_msg)
    db.session.add(donor_notif)
    db.session.commit()

    # Email notification
    if donation.donor and donation.donor.email:
        send_email_notification(
            recipient_email=donation.donor.email,
            subject="AnnSeva - Food Donation Completed & Distributed!",
            body_text=f"Dear {donation.donor.name},\n\n{donor_msg}\n\nYour contribution directly helped prevent hunger in the local community."
        )

    flash(f"Great job! Donation #{donation.id} has been marked as COMPLETED. Food saved: {donation.quantity} {donation.unit}.", "success")
    return redirect(url_for('accepted_donations'))


# ------------------------------------------------------------------------------
# 7B. ADMIN CONTROL PANEL MODULE
# ------------------------------------------------------------------------------
@app.route('/switch-to-admin')
@app.route('/admin/switch')
def switch_to_admin():
    """
    1-Click Switch to Admin Mode:
    Switches active session to the Administrator account (admin@annseva.org)
    and redirects straight to the Admin Control Center.
    """
    admin_user = User.query.filter_by(role='ADMIN').first()
    if not admin_user:
        admin_user = User(
            name="AnnSeva Administrator",
            email="admin@annseva.org",
            role="ADMIN",
            phone="9876543200",
            location="Headquarters, Mumbai"
        )
        admin_user.set_password("admin123")
        db.session.add(admin_user)
        db.session.commit()

    logout_user()
    login_user(admin_user, remember=True)
    flash("👑 Welcome to the AnnSeva Admin Control Center! Switched to Administrator account.", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin')
@app.route('/admin/dashboard')
def admin_dashboard():
    """
    Administrative Control Center:
    Provides system-wide overview of Donors, NGOs, and food donations.
    Enables user management, donation audits, and real-time operational monitoring.
    """
    if not current_user.is_authenticated or current_user.role != 'ADMIN':
        return redirect(url_for('switch_to_admin'))
    total_users = User.query.count()
    total_donors = User.query.filter_by(role='DONOR').count()
    total_ngos = User.query.filter_by(role='NGO').count()
    total_admins = User.query.filter_by(role='ADMIN').count()

    total_donations = Donation.query.count()
    pending_count = Donation.query.filter_by(status='PENDING').count()
    accepted_count = Donation.query.filter_by(status='ACCEPTED').count()
    picked_up_count = Donation.query.filter_by(status='PICKED UP').count()
    completed_donations = Donation.query.filter_by(status='COMPLETED').all()
    completed_count = len(completed_donations)
    rejected_count = Donation.query.filter_by(status='REJECTED').count()

    total_food_saved = sum(d.quantity for d in completed_donations)
    meals_served = int(total_food_saved * 2.5)

    recent_donations = Donation.query.order_by(Donation.created_at.desc()).limit(8).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(8).all()
    stats = get_report_statistics()

    return render_template(
        'admin_dashboard.html',
        total_users=total_users,
        total_donors=total_donors,
        total_ngos=total_ngos,
        total_admins=total_admins,
        total_donations=total_donations,
        pending_count=pending_count,
        accepted_count=accepted_count,
        picked_up_count=picked_up_count,
        completed_count=completed_count,
        rejected_count=rejected_count,
        total_food_saved=round(total_food_saved, 1),
        meals_served=meals_served,
        recent_donations=recent_donations,
        recent_users=recent_users,
        stats=stats
    )


@app.route('/admin/users')
@login_required
@role_required('ADMIN')
def admin_users():
    """
    Admin User Management:
    Lists all registered users (Donors, NGOs, Admins) with role filtering and search.
    """
    role_filter = request.args.get('role', 'ALL').strip().upper()
    search_query = request.args.get('q', '').strip()

    query = User.query
    if role_filter in ['DONOR', 'NGO', 'ADMIN']:
        query = query.filter_by(role=role_filter)
    if search_query:
        query = query.filter(
            (User.name.ilike(f"%{search_query}%")) |
            (User.email.ilike(f"%{search_query}%")) |
            (User.location.ilike(f"%{search_query}%"))
        )

    users = query.order_by(User.created_at.desc()).all()
    return render_template(
        'admin_users.html',
        users=users,
        role_filter=role_filter,
        search_query=search_query
    )


@app.route('/admin/donations')
@login_required
@role_required('ADMIN')
def admin_donations():
    """
    Admin Donations Management:
    Lists all food donations across all 5 statuses with filtering and search.
    """
    status_filter = request.args.get('status', 'ALL').strip().upper()
    search_query = request.args.get('q', '').strip()

    query = Donation.query
    if status_filter in ['PENDING', 'ACCEPTED', 'PICKED UP', 'COMPLETED', 'REJECTED']:
        query = query.filter_by(status=status_filter)
    if search_query:
        query = query.filter(
            (Donation.food_type.ilike(f"%{search_query}%")) |
            (Donation.location.ilike(f"%{search_query}%")) |
            (Donation.description.ilike(f"%{search_query}%"))
        )

    donations = query.order_by(Donation.created_at.desc()).all()
    return render_template(
        'admin_donations.html',
        donations=donations,
        status_filter=status_filter,
        search_query=search_query
    )


@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
@role_required('ADMIN')
def admin_delete_user(user_id):
    """
    Admin Deletes a User:
    Removes user account. If user is an NGO, resets accepted donations to PENDING.
    Prevents deleting the active session user.
    """
    if current_user.id == user_id:
        flash("You cannot delete your own admin account while logged in!", "danger")
        return redirect(url_for('admin_users'))

    user = db.get_or_404(User, user_id)
    user_name = user.name
    user_role = user.role

    if user.role == 'NGO':
        active_donations = Donation.query.filter_by(ngo_id=user.id).all()
        for d in active_donations:
            d.ngo_id = None
            if d.status in ['ACCEPTED', 'PICKED UP']:
                d.status = 'PENDING'

    db.session.delete(user)
    db.session.commit()
    flash(f"User '{user_name}' ({user_role}) was successfully deleted.", "success")
    return redirect(url_for('admin_users'))


@app.route('/admin/delete-donation/<int:donation_id>', methods=['POST'])
@login_required
@role_required('ADMIN')
def admin_delete_donation(donation_id):
    """
    Admin Deletes a Food Donation:
    Purges a specific donation request from the system.
    """
    donation = db.get_or_404(Donation, donation_id)
    food_info = f"#{donation.id} ({donation.food_type})"
    db.session.delete(donation)
    db.session.commit()
    flash(f"Donation {food_info} was successfully deleted.", "success")
    return redirect(url_for('admin_donations'))


# ------------------------------------------------------------------------------
# 8. COMMON DONATION DETAILS & TIMELINE VIEW
# ------------------------------------------------------------------------------
@app.route('/donation/<int:donation_id>')
@login_required
def donation_details(donation_id):
    """
    Shared donation detail view:
    Shows food details, pickup date/time, location, donor details, assigned NGO,
    status timeline badge, and role-specific action buttons.
    """
    donation = db.get_or_404(Donation, donation_id)

    # Security check: User must be either the Donor, or an NGO
    if current_user.is_donor() and donation.donor_id != current_user.id:
        flash("You are not authorized to view this donation.", "danger")
        return redirect(url_for('donor_dashboard'))

    return render_template('donation_details.html', donation=donation)


# ------------------------------------------------------------------------------
# 9. IN-APP NOTIFICATION MODULE
# ------------------------------------------------------------------------------
@app.route('/notifications')
@login_required
def notifications():
    """Displays all notifications for the logged-in user in chronological order."""
    all_notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('notifications.html', notifications=all_notifs)


@app.route('/notifications/mark-read/<int:notif_id>', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    """Marks a single notification as read."""
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first_or_404()
    notif.is_read = True
    db.session.commit()
    return redirect(url_for('notifications'))


@app.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Marks all notifications of current user as read."""
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    flash("All notifications marked as read.", "success")
    return redirect(url_for('notifications'))


# ------------------------------------------------------------------------------
# 10. MAP / LOCATION MODULE (AUTOMATIC RESOLUTION)
# ------------------------------------------------------------------------------
@app.route('/map')
def map_view():
    """
    Location & Map View:
    Displays interactive map with food donation points and NGO operational centers.
    Uses Google Maps API if configured, with built-in Leaflet/OpenStreetMap fallback.
    """
    return render_template('map.html', google_maps_api_key=Config.GOOGLE_MAPS_API_KEY)


@app.route('/api/map-data')
def api_map_data():
    """
    JSON API endpoint for Map markers:
    Dynamically resolves physical addresses into coordinates for map pins.
    """
    # 1. Active Donations (Pending, Accepted, or Picked Up)
    donations = Donation.query.filter(Donation.status.in_(['PENDING', 'ACCEPTED', 'PICKED UP'])).all()
    donation_markers = []
    for d in donations:
        lat, lng = resolve_location_coordinates(d.location, d.id)
        donation_markers.append({
            'id': d.id,
            'title': f"{d.food_type} ({d.quantity} {d.unit})",
            'type': 'donation',
            'status': d.status,
            'lat': lat,
            'lng': lng,
            'location': d.location,
            'donor': d.donor.name if d.donor else "Unknown",
            'time': f"{d.pickup_date} at {d.pickup_time}"
        })

    # 2. Registered NGOs
    ngos = User.query.filter_by(role='NGO').all()
    ngo_markers = []
    for n in ngos:
        lat, lng = resolve_location_coordinates(n.location, n.id + 1000)
        ngo_markers.append({
            'id': n.id,
            'name': n.name,
            'type': 'ngo',
            'lat': lat,
            'lng': lng,
            'location': n.location,
            'phone': n.phone or "N/A"
        })

    return jsonify({
        'donations': donation_markers,
        'ngos': ngo_markers
    })


# ------------------------------------------------------------------------------
# 11. LIVE REPORTS & LIVE STATUS API
# ------------------------------------------------------------------------------
@app.route('/reports')
def reports():
    """
    Reports Page:
    Shows summary KPI cards (Total Donations, Pending, Accepted, Rejected, Completed, Food Saved),
    along with interactive live Chart.js visualizations and auto-refresh stream.
    """
    stats = get_report_statistics()
    return render_template('reports.html', stats=stats)


@app.route('/api/reports-data')
def api_reports_data():
    """JSON API endpoint returning live statistical data for Chart.js and live metrics."""
    stats = get_report_statistics()
    return jsonify(stats)


@app.route('/api/live-status')
def api_live_status():
    """
    Lightweight live heartbeat endpoint:
    Returns unread alerts count and key metrics for real-time dashboard polling.
    """
    unread_count = 0
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

    total_donations = Donation.query.count()
    completed_donations = Donation.query.filter_by(status='COMPLETED').all()
    total_food_saved = sum(d.quantity for d in completed_donations)

    return jsonify({
        'unread_notifications': unread_count,
        'total_donations': total_donations,
        'total_food_saved': round(total_food_saved, 1),
        'timestamp': datetime.now(timezone.utc).strftime('%H:%M:%S')
    })


@app.route('/api/reports/reset', methods=['POST'])
@login_required
@role_required('ADMIN')
def api_reports_reset():
    """
    Live Reset Endpoint for Report Counters:
    Clears all donation records and transaction logs so that all report counters
    (Total Donations, Food Saved, Meals, Status counts) immediately reset to 0.
    Retains donor and NGO user accounts so users can log in and test fresh donations.
    Restricted to ADMIN role.
    """
    try:
        Donation.query.delete()
        Notification.query.delete()
        db.session.commit()
        stats = get_report_statistics()
        return jsonify({
            'success': True,
            'message': 'All report counters have been reset to 0!',
            'stats': stats
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/reports/restore-demo', methods=['POST'])
@login_required
@role_required('ADMIN')
def api_reports_restore_demo():
    """
    Restores initial sample donations and records for testing/viva demonstration.
    Restricted to ADMIN role.
    """
    try:
        seed_database(app, force_reseed=True, start_at_zero=False)
        stats = get_report_statistics()
        return jsonify({
            'success': True,
            'message': 'Sample demo records restored successfully!',
            'stats': stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/health')
def api_health():
    """
    System Health & Database Verification API:
    Returns real-time backend operational status, active database dialect,
    registered users breakdown, and matching engine status.
    """
    try:
        db_engine = db.engine.name
        total_donors = User.query.filter_by(role='DONOR').count()
        total_ngos = User.query.filter_by(role='NGO').count()
        total_donations = Donation.query.count()
        return jsonify({
            'status': 'healthy',
            'server': 'AnnSeva Backend 2.0 (Live)',
            'database': {
                'status': 'connected',
                'engine': db_engine,
                'total_users': total_donors + total_ngos,
                'donors': total_donors,
                'ngos': total_ngos,
                'donations': total_donations
            },
            'matching_engine': 'Address & Locality Keyword Matching (services/matching.py)',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'degraded',
            'database': {'status': 'error', 'error': str(e)},
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500


# ------------------------------------------------------------------------------
# 12. DATABASE AUTO-INIT & AUTO-MIGRATION (ADDRESS-BASED SCHEMA SYNC)
# ------------------------------------------------------------------------------
sync_database_schema(app)


# ------------------------------------------------------------------------------
# 13. ERROR HANDLERS
# ------------------------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', error_code=404, error_message="Page Not Found"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('base.html', error_code=500, error_message="Internal Server Error"), 500


# ------------------------------------------------------------------------------
# 14. APPLICATION ENTRY POINT (LIVE HOST 0.0.0.0)
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    print("\n=======================================================")
    print("AnnSeva Web Application Running Live!")
    print("Local URL:    http://127.0.0.1:5000")
    print("Network URL:  http://0.0.0.0:5000")
    print("Mode:         Live Reporting & Address-Based Matching")
    print("=======================================================\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
