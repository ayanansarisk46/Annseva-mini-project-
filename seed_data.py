"""
================================================================================
AnnSeva - Demo Data Seeder (seed_data.py)
================================================================================
College Viva Note:
This script populates the database with 2 Donors, 2 NGOs, and realistic
sample donations across all statuses (Pending, Accepted, Rejected, Completed)
using clean city/area addresses (no latitude/longitude required).

Run standalone via: python seed_data.py [--reset]
================================================================================
"""

from datetime import datetime, date, timedelta, timezone
from sqlalchemy import inspect
from models import db, User, Donation, Notification
from config import Config

def seed_database(app, force_reseed=False, start_at_zero=False):
    """Populates demo data inside Flask application context."""
    with app.app_context():
        if force_reseed:
            print("[INFO] Resetting existing tables...")
            db.drop_all()

        # Create all tables first
        db.create_all()

        # 1. Seed Users if not present
        if User.query.count() == 0 or force_reseed:
            print("[INFO] Seeding initial demo users...")

            donor1 = User(
                name="Green Valley Hotel",
                email="donor1@hotel.com",
                role="DONOR",
                phone="9876543210",
                location="Andheri West, Mumbai"
            )
            donor1.set_password("password123")

            donor2 = User(
                name="Royal Caterers & Banquet",
                email="donor2@caterer.com",
                role="DONOR",
                phone="9876543211",
                location="Bandra Kurla Complex, Mumbai"
            )
            donor2.set_password("password123")

            ngo1 = User(
                name="Roti Bank Foundation",
                email="ngo1@rotibank.org",
                role="NGO",
                phone="9876543212",
                location="Andheri East, Mumbai"
            )
            ngo1.set_password("password123")

            ngo2 = User(
                name="FeedTheNeedy Trust",
                email="ngo2@feedthechildren.org",
                role="NGO",
                phone="9876543213",
                location="Kurla West, Mumbai"
            )
            ngo2.set_password("password123")

            admin = User(
                name="AnnSeva Administrator",
                email="admin@annseva.org",
                role="ADMIN",
                phone="9876543200",
                location="Headquarters, Mumbai"
            )
            admin.set_password("admin123")

            db.session.add_all([donor1, donor2, ngo1, ngo2, admin])
            db.session.commit()
            print("[INFO] Demo users (Donors, NGOs, Admin) initialized successfully.")

        if start_at_zero:
            Donation.query.delete()
            Notification.query.delete()
            db.session.commit()
            print("[SUCCESS] Report counters initialized to 0 (Zero-State Demo Mode).")
            return

        # 2. Seed Donations if table is empty or if force_reseed
        if Donation.query.count() == 0 or force_reseed:
            donor1 = User.query.filter_by(email="donor1@hotel.com").first()
            donor2 = User.query.filter_by(email="donor2@caterer.com").first()
            ngo1 = User.query.filter_by(email="ngo1@rotibank.org").first()
            ngo2 = User.query.filter_by(email="ngo2@feedthechildren.org").first()

            if not (donor1 and donor2 and ngo1 and ngo2):
                print("[WARN] Required demo users not found for sample donations.")
                return

            today = date.today()
            now = datetime.now(timezone.utc)

            d1 = Donation(
                donor_id=donor1.id,
                ngo_id=ngo1.id,
                food_type="Cooked Meals (Rice, Dal, Rotis)",
                quantity=45.0,
                unit="kg",
                location="Andheri West, Mumbai",
                pickup_date=today,
                pickup_time="18:30",
                description="Freshly prepared wedding lunch surplus. Clean and properly packaged in foil containers.",
                status="PENDING",
                created_at=now - timedelta(hours=2)
            )

            d2 = Donation(
                donor_id=donor2.id,
                ngo_id=ngo2.id,
                food_type="Assorted Breads and Pastries",
                quantity=20.0,
                unit="kg",
                location="Bandra Kurla Complex, Mumbai",
                pickup_date=today,
                pickup_time="19:00",
                description="Bakery items surplus from corporate event. Packed in dry hygienic boxes.",
                status="ACCEPTED",
                created_at=now - timedelta(hours=5)
            )

            d3 = Donation(
                donor_id=donor1.id,
                ngo_id=ngo1.id,
                food_type="Vegetable Biryani & Curry",
                quantity=35.0,
                unit="kg",
                location="Andheri West, Mumbai",
                pickup_date=today - timedelta(days=1),
                pickup_time="14:00",
                description="Buffet leftovers from corporate seminar, kept hot and fresh.",
                status="COMPLETED",
                created_at=now - timedelta(days=1),
                completed_at=now - timedelta(hours=20)
            )

            d4 = Donation(
                donor_id=donor2.id,
                ngo_id=ngo1.id,
                food_type="Fruit Baskets & Salad Packs",
                quantity=15.0,
                unit="kg",
                location="Bandra Kurla Complex, Mumbai",
                pickup_date=today - timedelta(days=2),
                pickup_time="11:00",
                description="Fresh whole fruits and unopened salads.",
                status="REJECTED",
                created_at=now - timedelta(days=2)
            )

            d5 = Donation(
                donor_id=donor1.id,
                ngo_id=ngo2.id,
                food_type="Steamed Idlis & Sambar Pots",
                quantity=25.0,
                unit="kg",
                location="Andheri West, Mumbai",
                pickup_date=today,
                pickup_time="17:00",
                description="Morning breakfast buffet extras, packed hot in insulated containers.",
                status="PICKED UP",
                created_at=now - timedelta(hours=3)
            )

            db.session.add_all([d1, d2, d3, d4, d5])
            db.session.commit()

            # 4. Create Initial Notifications
            notif1 = Notification(
                user_id=ngo1.id,
                message="New food donation is available from Green Valley Hotel in Andheri West.",
                is_read=False,
                created_at=now - timedelta(hours=2)
            )
            notif2 = Notification(
                user_id=ngo2.id,
                message="You have received a new food donation request: Assorted Breads in BKC.",
                is_read=True,
                created_at=now - timedelta(hours=5)
            )
            notif3 = Notification(
                user_id=donor2.id,
                message="Your food donation has been accepted by FeedTheNeedy Trust.",
                is_read=True,
                created_at=now - timedelta(hours=4)
            )
            notif4 = Notification(
                user_id=donor1.id,
                message="Your food donation (Vegetable Biryani) has been completed. Thank you for helping!",
                is_read=True,
                created_at=now - timedelta(hours=20)
            )

            db.session.add_all([notif1, notif2, notif3, notif4])
            db.session.commit()
            print("[SUCCESS] Database seeded successfully with Donors, NGOs, and Donations (Clean Address Mode)!")


def sync_database_schema(app):
    """
    Auto-Migration & Database Sync Engine:
    1. Inspects existing tables and columns.
    2. Detects any legacy columns (like latitude / longitude).
    3. If legacy schema is found, safely drops and rebuilds tables with the clean schema.
    4. Ensures all tables exist (db.create_all()).
    5. Seeds initial demo accounts and realistic sample donations if empty.
    """
    with app.app_context():
        db.create_all()
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        needs_rebuild = False
        for tbl in ['users', 'donations']:
            if tbl in tables:
                col_names = [col['name'] for col in inspector.get_columns(tbl)]
                if 'latitude' in col_names or 'longitude' in col_names:
                    print(f"[INFO] Detected legacy coordinates column in '{tbl}' table. Upgrading database schema...")
                    needs_rebuild = True
                    break

        if needs_rebuild:
            db.drop_all()
            db.create_all()
            seed_database(app, force_reseed=True, start_at_zero=False)
            print("[SUCCESS] Database schema successfully upgraded to clean Address-Based architecture!")
        elif User.query.count() == 0 or Donation.query.count() == 0:
            seed_database(app, force_reseed=False, start_at_zero=False)
        else:
            print("[INFO] Database schema verified and up-to-date.")

        # Ensure Admin account always exists
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
            print("[INFO] Admin user initialized: admin@annseva.org / admin123")


if __name__ == "__main__":
    import sys
    from flask import Flask
    app = Flask(__name__)
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.get_database_uri()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    reset_flag = ('--reset' in sys.argv) or ('--zero' in sys.argv)
    zero_flag = ('--zero' in sys.argv)
    seed_database(app, force_reseed=reset_flag, start_at_zero=zero_flag)
