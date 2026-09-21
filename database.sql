-- ====================================================================
-- AnnSeva - Food Donation and Management System
-- Database Schema Script (database.sql)
-- Target RDBMS: MySQL 8.0+ / MariaDB
-- College Project: TY Computer Science Mini Project
-- ====================================================================

-- 1. Create Database
CREATE DATABASE IF NOT EXISTS annseva_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE annseva_db;

-- 2. Drop existing tables if needed (in reverse foreign key order)
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS donations;
DROP TABLE IF EXISTS users;

-- ====================================================================
-- Table: users
-- Holds authentication & profile data for Donors and NGOs
-- ====================================================================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('DONOR', 'NGO', 'ADMIN') NOT NULL,
    phone VARCHAR(20) NULL,
    location VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_email (email),
    INDEX idx_user_role (role)
) ENGINE=InnoDB;

-- ====================================================================
-- Table: donations
-- Holds food donation listings and status lifecycle
-- ====================================================================
CREATE TABLE donations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    donor_id INT NOT NULL,
    ngo_id INT NULL,
    food_type VARCHAR(100) NOT NULL,
    quantity FLOAT NOT NULL,
    unit VARCHAR(20) DEFAULT 'kg',
    location VARCHAR(255) NOT NULL,
    pickup_date DATE NOT NULL,
    pickup_time VARCHAR(30) NOT NULL,
    description TEXT NULL,
    status ENUM('PENDING', 'ACCEPTED', 'PICKED UP', 'COMPLETED', 'REJECTED') DEFAULT 'PENDING' NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME NULL,
    INDEX idx_donation_status (status),
    INDEX idx_donation_donor (donor_id),
    INDEX idx_donation_ngo (ngo_id),
    CONSTRAINT fk_donations_donor FOREIGN KEY (donor_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_donations_ngo FOREIGN KEY (ngo_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ====================================================================
-- Table: notifications
-- In-app alert messages for Donors and NGOs
-- ====================================================================
CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    message VARCHAR(500) NOT NULL,
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_notification_user (user_id),
    CONSTRAINT fk_notifications_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ====================================================================
-- Sample Seed Data (For Demonstration & Testing)
-- Default Password for all demo accounts: password123
-- (Hashed with Werkzeug pbkdf2:sha256)
-- ====================================================================

-- 1. Insert 2 Donors and 2 NGOs
INSERT INTO users (id, name, email, password, role, phone, location) VALUES
(1, 'Green Valley Hotel', 'donor1@hotel.com', 'scrypt:32768:8:1$uH3W7aN0sU1gZq$23cf3eb34cb50306be1ffeb8f05786f91f3aefabefcb7f0cba1e78550dd7f1bfa98d249f056f7ef5eb6ec4f94080ca33cce4f25fa414a9ecae3fbbe67f1b77f9', 'DONOR', '9876543210', 'Andheri West, Mumbai'),
(2, 'Royal Caterers & Banquet', 'donor2@caterer.com', 'scrypt:32768:8:1$uH3W7aN0sU1gZq$23cf3eb34cb50306be1ffeb8f05786f91f3aefabefcb7f0cba1e78550dd7f1bfa98d249f056f7ef5eb6ec4f94080ca33cce4f25fa414a9ecae3fbbe67f1b77f9', 'DONOR', '9876543211', 'Bandra Kurla Complex, Mumbai'),
(3, 'Roti Bank Foundation', 'ngo1@rotibank.org', 'scrypt:32768:8:1$uH3W7aN0sU1gZq$23cf3eb34cb50306be1ffeb8f05786f91f3aefabefcb7f0cba1e78550dd7f1bfa98d249f056f7ef5eb6ec4f94080ca33cce4f25fa414a9ecae3fbbe67f1b77f9', 'NGO', '9876543212', 'Andheri East, Mumbai'),
(4, 'FeedTheNeedy Trust', 'ngo2@feedthechildren.org', 'scrypt:32768:8:1$uH3W7aN0sU1gZq$23cf3eb34cb50306be1ffeb8f05786f91f3aefabefcb7f0cba1e78550dd7f1bfa98d249f056f7ef5eb6ec4f94080ca33cce4f25fa414a9ecae3fbbe67f1b77f9', 'NGO', '9876543213', 'Kurla West, Mumbai'),
(5, 'AnnSeva Administrator', 'admin@annseva.org', 'scrypt:32768:8:1$uH3W7aN0sU1gZq$23cf3eb34cb50306be1ffeb8f05786f91f3aefabefcb7f0cba1e78550dd7f1bfa98d249f056f7ef5eb6ec4f94080ca33cce4f25fa414a9ecae3fbbe67f1b77f9', 'ADMIN', '9876543200', 'Headquarters, Mumbai');

-- 2. Insert Sample Donations across different statuses
INSERT INTO donations (id, donor_id, ngo_id, food_type, quantity, unit, location, pickup_date, pickup_time, description, status, created_at, completed_at) VALUES
(1, 1, 3, 'Cooked Meals (Rice, Dal, Rotis)', 45.0, 'kg', 'Andheri West, Mumbai', '2026-09-24', '18:30', 'Freshly prepared wedding lunch surplus. Clean and properly packaged in foil containers.', 'PENDING', NOW() - INTERVAL 2 HOUR, NULL),
(2, 2, 4, 'Assorted Breads and Pastries', 20.0, 'kg', 'Bandra Kurla Complex, Mumbai', '2026-09-24', '19:00', 'Bakery items surplus from corporate event. Packed in dry hygienic boxes.', 'ACCEPTED', NOW() - INTERVAL 5 HOUR, NULL),
(3, 1, 3, 'Vegetable Biryani & Curry', 35.0, 'kg', 'Andheri West, Mumbai', '2026-09-23', '14:00', 'Buffet leftovers from corporate seminar, kept hot and fresh.', 'COMPLETED', NOW() - INTERVAL 1 DAY, NOW() - INTERVAL 22 HOUR),
(4, 2, 3, 'Fruit Baskets & Salad Packs', 15.0, 'kg', 'Bandra Kurla Complex, Mumbai', '2026-09-22', '11:00', 'Fresh whole fruits and unopened salads.', 'REJECTED', NOW() - INTERVAL 2 DAY, NULL),
(5, 1, 4, 'Steamed Idlis & Sambar Pots', 25.0, 'kg', 'Andheri West, Mumbai', '2026-09-24', '17:00', 'Morning breakfast buffet extras, packed hot in insulated containers.', 'PICKED UP', NOW() - INTERVAL 3 HOUR, NULL);

-- 3. Insert Initial Notifications
INSERT INTO notifications (user_id, message, is_read, created_at) VALUES
(3, 'New food donation is available from Green Valley Hotel.', FALSE, NOW() - INTERVAL 2 HOUR),
(4, 'You have received a new food donation request: Assorted Breads.', TRUE, NOW() - INTERVAL 5 HOUR),
(2, 'Your food donation has been accepted by FeedTheNeedy Trust.', TRUE, NOW() - INTERVAL 4 HOUR),
(1, 'Your food donation (Vegetable Biryani) has been marked as Completed. Thank you for reducing food waste!', TRUE, NOW() - INTERVAL 22 HOUR);
