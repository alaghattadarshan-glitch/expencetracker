from flask import Blueprint, request, jsonify
from app.database.connection import get_db_connection
from datetime import datetime, timedelta

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

@settings_bp.route('', methods=['GET'])
def get_settings():
    """Retrieve user settings and preferences"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, display_name, currency FROM settings WHERE id = 1")
            settings = cursor.fetchone()
            if not settings:
                settings = {'id': 1, 'display_name': 'User', 'currency': '₹'}
        conn.close()
        return jsonify(settings), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('', methods=['PUT'])
def update_settings():
    """Update user settings"""
    try:
        data = request.get_json() or {}
        display_name = data.get('display_name', 'User').strip()
        currency = data.get('currency', '₹').strip()

        if not display_name:
            return jsonify({'error': 'Display name cannot be empty'}), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO settings (id, display_name, currency)
                VALUES (1, %s, %s)
                ON DUPLICATE KEY UPDATE display_name = VALUES(display_name), currency = VALUES(currency)
            """, (display_name, currency))
        conn.close()

        return jsonify({'message': 'Settings updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/seed-demo', methods=['POST'])
def seed_demo_data():
    """
    Populates realistic demo financial data (transactions and budgets)
    across the current and past 3 months. Perfect for presentations!
    """
    try:
        now = datetime.now()
        cur_year = now.year
        cur_month = now.month

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 1. Add demo budgets
            budgets_data = [
                ('Overall', 50000.00, cur_month, cur_year),
                ('Food', 12000.00, cur_month, cur_year),
                ('Shopping', 8000.00, cur_month, cur_year),
                ('Bills', 7000.00, cur_month, cur_year),
                ('Transport', 4000.00, cur_month, cur_year),
                ('Entertainment', 3500.00, cur_month, cur_year)
            ]
            for cat, limit, m, y in budgets_data:
                cursor.execute("""
                    INSERT INTO budgets (category, monthly_limit, month, year)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE monthly_limit = VALUES(monthly_limit)
                """, (cat, limit, m, y))

            # 2. Add realistic transactions across current and previous 2 months
            d0 = now.strftime('%Y-%m-%d')
            d1 = (now - timedelta(days=2)).strftime('%Y-%m-%d')
            d2 = (now - timedelta(days=5)).strftime('%Y-%m-%d')
            d3 = (now - timedelta(days=8)).strftime('%Y-%m-%d')
            d4 = (now - timedelta(days=12)).strftime('%Y-%m-%d')
            d5 = (now - timedelta(days=20)).strftime('%Y-%m-%d')
            
            # Prior months
            d_prev1 = (now - timedelta(days=35)).strftime('%Y-%m-%d')
            d_prev2 = (now - timedelta(days=40)).strftime('%Y-%m-%d')
            d_prev3 = (now - timedelta(days=65)).strftime('%Y-%m-%d')

            sample_txs = [
                # Current month
                ('Monthly Software Engineer Salary', 'Income', 75000.00, 'Salary', d5, 'Direct deposit bank transfer'),
                ('Freelance DevOps Consulting', 'Income', 18500.00, 'Freelance', d3, 'Docker and CI/CD pipeline setup project'),
                ('House Rent Payment', 'Expense', 16000.00, 'Rent', d4, 'Monthly apartment rent via UPI'),
                ('Electricity and Internet Bills', 'Expense', 3200.00, 'Bills', d2, 'Fiber broadband + Bescom utility'),
                ('Supermarket Groceries', 'Expense', 4250.00, 'Food', d1, 'Weekly vegetables, dairy and essentials'),
                ('Swiggy Gourmet Dinner', 'Expense', 950.00, 'Food', d0, 'Weekend celebration dinner'),
                ('Metro & Cab Fuel Allowance', 'Expense', 1450.00, 'Transport', d2, 'Metro smart card recharge & petrol'),
                ('Udemy DevOps Certification Course', 'Expense', 649.00, 'Education', d3, 'Docker & Kubernetes Deep Dive course'),
                ('Movie Tickets & Popcorn', 'Expense', 850.00, 'Entertainment', d1, 'Weekend cinema booking'),
                ('Quarterly Health Checkup', 'Expense', 1800.00, 'Health', d4, 'Routine lab tests'),

                # Previous Month
                ('Monthly Salary (Last Month)', 'Income', 75000.00, 'Salary', d_prev1, 'Monthly salary credit'),
                ('House Rent (Last Month)', 'Expense', 16000.00, 'Rent', d_prev1, 'Rent paid to landlord'),
                ('Grocery & Food (Last Month)', 'Expense', 9800.00, 'Food', d_prev2, 'Monthly grocery total'),
                ('Online Shopping Festival', 'Expense', 6500.00, 'Shopping', d_prev2, 'Clothing & headphones'),

                # Two months ago
                ('Monthly Salary (2 Months Ago)', 'Income', 72000.00, 'Salary', d_prev3, 'Monthly salary credit'),
                ('House Rent (2 Months Ago)', 'Expense', 16000.00, 'Rent', d_prev3, 'Rent paid to landlord'),
                ('Flight Tickets for Vacation', 'Expense', 8200.00, 'Travel', d_prev3, 'Domestic flight tickets')
            ]

            for title, tx_type, amount, cat, tx_date, desc in sample_txs:
                cursor.execute("""
                    INSERT INTO transactions (title, type, amount, category, transaction_date, description)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (title, tx_type, amount, cat, tx_date, desc))

        conn.close()

        return jsonify({'message': 'Demo financial dataset loaded successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
