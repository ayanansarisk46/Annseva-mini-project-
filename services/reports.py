"""
================================================================================
AnnSeva - Reports & Live Analytics Service (services/reports.py)
================================================================================
College Viva Note:
This service aggregates real-time data from the database to generate
live metrics, activity streams, and Chart.js datasets for the Reports page.
Calculates:
- Live total count of donations
- Live status distribution (Pending, Accepted, Rejected, Completed)
- Live total food saved (kg) for completed pickups
- Estimated number of people fed / meals served
- Distribution across food categories
- Live recent activity feed
================================================================================
"""

from datetime import datetime, timezone
from sqlalchemy import func
from models import db, Donation, User

def get_report_statistics():
    """
    Computes live summary metrics and Chart.js datasets from database tables.
    Returns:
        dict: High-level metrics, status counts, food category distributions, and recent stream.
    """
    # 1. Status Counts
    total_donations = Donation.query.count()
    pending_count = Donation.query.filter_by(status='PENDING').count()
    accepted_count = Donation.query.filter_by(status='ACCEPTED').count()
    picked_up_count = Donation.query.filter_by(status='PICKED UP').count()
    rejected_count = Donation.query.filter_by(status='REJECTED').count()
    completed_count = Donation.query.filter_by(status='COMPLETED').count()

    # 2. Food Saved (Only COMPLETED donations count as successfully saved food)
    completed_donations = Donation.query.filter_by(status='COMPLETED').all()
    total_food_saved = sum(d.quantity for d in completed_donations)

    # Food in progress (accepted or picked up, undergoing collection/transit)
    in_transit_donations = Donation.query.filter(Donation.status.in_(['ACCEPTED', 'PICKED UP'])).all()
    accepted_food = sum(d.quantity for d in in_transit_donations)

    # Approx 2.5 meals per 1 kg of saved food
    estimated_meals_served = int(total_food_saved * 2.5)

    # 3. Category / Food Type Distribution for Chart.js
    category_data = db.session.query(
        Donation.food_type, func.count(Donation.id), func.sum(Donation.quantity)
    ).group_by(Donation.food_type).all()

    category_labels = []
    category_counts = []
    category_weights = []

    for cat_name, count_val, weight_sum in category_data:
        category_labels.append(cat_name)
        category_counts.append(count_val)
        category_weights.append(round(weight_sum or 0, 1))

    # 4. User Stats
    total_donors = User.query.filter_by(role='DONOR').count()
    total_ngos = User.query.filter_by(role='NGO').count()

    # 5. Live Recent Activity Stream (last 6 transactions)
    recent_donations = Donation.query.order_by(Donation.created_at.desc()).limit(6).all()
    activity_stream = []
    for d in recent_donations:
        activity_stream.append({
            'id': d.id,
            'food_type': d.food_type,
            'quantity': d.quantity,
            'unit': d.unit,
            'status': d.status,
            'donor': d.donor.name if d.donor else "Anonymous Donor",
            'ngo': d.ngo.name if d.ngo else "Awaiting Match",
            'location': d.location,
            'created_at': d.created_at.strftime('%d %b, %H:%M') if d.created_at else ''
        })

    return {
        'total_donations': total_donations,
        'pending_count': pending_count,
        'accepted_count': accepted_count,
        'picked_up_count': picked_up_count,
        'rejected_count': rejected_count,
        'completed_count': completed_count,
        'total_food_saved': round(total_food_saved, 1),
        'accepted_food': round(accepted_food, 1),
        'estimated_meals_served': estimated_meals_served,
        'total_donors': total_donors,
        'total_ngos': total_ngos,
        'timestamp': datetime.now(timezone.utc).strftime('%H:%M:%S UTC'),
        'activity_stream': activity_stream,
        # Datasets formatted for Chart.js
        'charts': {
            'status': {
                'labels': ['Pending', 'Accepted', 'Picked Up', 'Completed', 'Rejected'],
                'data': [pending_count, accepted_count, picked_up_count, completed_count, rejected_count],
                'colors': ['#f59e0b', '#3b82f6', '#8b5cf6', '#10b981', '#ef4444']
            },
            'categories': {
                'labels': category_labels if category_labels else ['No Data'],
                'counts': category_counts if category_counts else [0],
                'weights': category_weights if category_weights else [0]
            }
        }
    }
