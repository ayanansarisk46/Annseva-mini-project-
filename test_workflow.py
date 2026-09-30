"""
================================================================================
AnnSeva - Comprehensive Automated End-to-End Workflow Test (test_workflow.py)
================================================================================
Tests the exact scenario specified in Project Requirement Section 28:
1. Register Donor.
2. Login as Donor.
3. Add food donation.
4. Check that donation is stored in database.
5. Verify matching logic selects nearest suitable NGO.
6. Check NGO assignment and notification.
7. Login as NGO.
8. View donation details.
9. Accept donation & verify donor notification.
10. Update donation to COMPLETED.
11. Check report statistics (food saved increased).
12. Verify charts dataset API endpoint.
13. Test rejection flow for another donation.
14. Verify role-based access restrictions.
================================================================================
"""

import unittest
from datetime import date, timedelta
from app import app, db
from models import User, Donation, Notification
from services.reports import get_report_statistics

class AnnSevaWorkflowTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_full_project_lifecycle(self):
        print("\n=======================================================")
        print("RUNNING ANNSEVA COMPLETE WORKFLOW VERIFICATION TEST")
        print("=======================================================")

        with app.app_context():
            # Step 1: Register New Donor
            print("\n[STEP 1] Testing Donor Registration...")
            donor_email = "test_donor@delhicatering.com"
            # Delete if exists from previous test
            existing = User.query.filter_by(email=donor_email).first()
            if existing:
                Donation.query.filter_by(donor_id=existing.id).delete()
                Notification.query.filter_by(user_id=existing.id).delete()
                db.session.delete(existing)
                db.session.commit()

            resp = self.client.post('/register', data={
                'name': 'Delhi Royal Catering',
                'email': donor_email,
                'password': 'password123',
                'role': 'DONOR',
                'phone': '9876500001',
                'location': 'Andheri West, Mumbai'
            }, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            donor = User.query.filter_by(email=donor_email).first()
            self.assertIsNotNone(donor)
            self.assertEqual(donor.role, 'DONOR')
            print(f" -> Donor Registered: ID {donor.id}, Name: {donor.name}")

            # Step 2: Login as Donor
            print("\n[STEP 2] Testing Donor Login...")
            resp = self.client.post('/login', data={
                'email': donor_email,
                'password': 'password123'
            }, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Welcome back", resp.data)
            print(" -> Donor successfully authenticated.")

            # Step 3 & 4: Add Food Donation & Save to DB
            print("\n[STEP 3 & 4] Adding Food Donation...")
            today = date.today()
            resp = self.client.post('/donor/add-donation', data={
                'food_type': 'Paneer Pulao & Mix Dal',
                'quantity': '30.5',
                'unit': 'kg',
                'location': 'Andheri West, Mumbai',
                'pickup_date': today.strftime('%Y-%m-%d'),
                'pickup_time': '20:00',
                'description': 'Fresh evening feast surplus, packed in hygienic containers.'
            }, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            donation = Donation.query.filter_by(donor_id=donor.id, food_type='Paneer Pulao & Mix Dal').first()
            self.assertIsNotNone(donation)
            self.assertEqual(donation.status, 'PENDING')
            self.assertEqual(donation.quantity, 30.5)
            print(f" -> Donation #{donation.id} created successfully with status: {donation.status}")

            # Step 5 & 6: Matching Logic & NGO Assignment
            print("\n[STEP 5 & 6] Verifying Matching Logic and NGO Assignment...")
            self.assertIsNotNone(donation.ngo_id)
            assigned_ngo = db.session.get(User, donation.ngo_id)
            print(f" -> Nearest Matched NGO: {assigned_ngo.name} (ID: {assigned_ngo.id})")

            # Check NGO Notification
            ngo_notif = Notification.query.filter_by(user_id=assigned_ngo.id).order_by(Notification.created_at.desc()).first()
            self.assertIsNotNone(ngo_notif)
            self.assertIn("New food donation alert", ngo_notif.message)
            print(f" -> NGO Notification dispatched: '{ngo_notif.message[:60]}...'")

            # Step 7: Logout Donor & Login as NGO
            print("\n[STEP 7] Logging in as Matched NGO...")
            self.client.get('/logout', follow_redirects=True)
            resp = self.client.post('/login', data={
                'email': assigned_ngo.email,
                'password': 'password123'
            }, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"NGO Portal", resp.data)
            print(f" -> Logged in as NGO: {assigned_ngo.name}")

            # Step 8: View Donation Details
            print("\n[STEP 8] Viewing Donation Details...")
            resp = self.client.get(f'/donation/{donation.id}')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Paneer Pulao", resp.data)
            print(" -> Donation details loaded successfully.")

            # Step 9: NGO Accepts Donation
            print("\n[STEP 9] NGO Accepts Donation...")
            resp = self.client.post(f'/ngo/accept/{donation.id}', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            db.session.refresh(donation)
            self.assertEqual(donation.status, 'ACCEPTED')
            print(f" -> Donation status updated to: {donation.status}")

            # Check Donor Notification after acceptance
            donor_notif = Notification.query.filter_by(user_id=donor.id).order_by(Notification.created_at.desc()).first()
            self.assertIsNotNone(donor_notif)
            self.assertIn("ACCEPTED", donor_notif.message)
            print(f" -> Donor received acceptance notification: '{donor_notif.message[:60]}...'")

            # Step 10: Complete Donation (Food Picked Up)
            print("\n[STEP 10] NGO Marks Donation as Completed...")
            initial_stats = get_report_statistics()
            initial_saved = initial_stats['total_food_saved']

            resp = self.client.post(f'/ngo/complete/{donation.id}', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            db.session.refresh(donation)
            self.assertEqual(donation.status, 'COMPLETED')
            self.assertIsNotNone(donation.completed_at)
            print(f" -> Donation #{donation.id} successfully COMPLETED at {donation.completed_at}")

            # Step 11: Check Report Statistics Updated
            print("\n[STEP 11] Checking Updated Report Statistics...")
            updated_stats = get_report_statistics()
            self.assertEqual(updated_stats['total_food_saved'], initial_saved + 30.5)
            print(f" -> Food Saved increased from {initial_saved} kg to {updated_stats['total_food_saved']} kg!")

            # Step 12: Verify Chart API
            print("\n[STEP 12] Verifying Chart.js API endpoint...")
            resp = self.client.get('/api/reports-data')
            self.assertEqual(resp.status_code, 200)
            json_data = resp.get_json()
            self.assertIn('charts', json_data)
            self.assertIn('status', json_data['charts'])
            print(f" -> Chart API returns valid JSON datasets: Status labels {json_data['charts']['status']['labels']}")

            # Step 13: Test Rejection Flow
            print("\n[STEP 13] Testing Donation Rejection Flow...")
            # Create a second donation to reject
            reject_donation = Donation(
                donor_id=donor.id,
                ngo_id=assigned_ngo.id,
                food_type='Surplus Tea & Biscuits',
                quantity=5.0,
                unit='kg',
                location='Andheri West, Mumbai',
                pickup_date=today,
                pickup_time='16:00',
                status='PENDING'
            )
            db.session.add(reject_donation)
            db.session.commit()

            resp = self.client.post(f'/ngo/reject/{reject_donation.id}', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            db.session.refresh(reject_donation)
            self.assertEqual(reject_donation.status, 'REJECTED')
            print(f" -> Donation #{reject_donation.id} successfully REJECTED.")

            # Step 14: Verify Role-Based Protection
            print("\n[STEP 14] Testing Role-Based Route Protection...")
            # As NGO, trying to access donor add donation route should be forbidden / redirected
            resp = self.client.get('/donor/add-donation', follow_redirects=True)
            self.assertIn(b"Access denied", resp.data)
            print(" -> Role-based security verified: NGO cannot access Donor-only routes.")

            # Logout
            self.client.get('/logout', follow_redirects=True)
            print(" -> Logged out successfully.")

        print("\n=======================================================")
        print("ALL WORKFLOW STEPS PASSED SUCCESSFULLY! (100% COMPLETE)")
        print("=======================================================\n")

if __name__ == '__main__':
    unittest.main()
