from flask import Blueprint, jsonify
from app.database.connection import get_db_connection
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('', methods=['GET'])
def get_dashboard_summary():
    """
    Returns calculated financial summary, charts data, and recent transactions.
    All data is aggregated in real-time from MySQL tables.
    """
    try:
        now = datetime.now()
        current_month = now.month
        current_year = now.year

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 1. Total All-time Balance (All Income - All Expenses)
            cursor.execute("""
                SELECT 
                    CAST(COALESCE(SUM(CASE WHEN type = 'Income' THEN amount ELSE -amount END), 0) AS DOUBLE) AS total_balance,
                    CAST(COALESCE(SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END), 0) AS DOUBLE) AS all_time_income,
                    CAST(COALESCE(SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END), 0) AS DOUBLE) AS all_time_expense
                FROM transactions
            """)
            balance_row = cursor.fetchone()
            total_balance = balance_row['total_balance']

            # 2. Current Month Income & Expenses
            cursor.execute("""
                SELECT 
                    CAST(COALESCE(SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END), 0) AS DOUBLE) AS monthly_income,
                    CAST(COALESCE(SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END), 0) AS DOUBLE) AS monthly_expense
                FROM transactions
                WHERE MONTH(transaction_date) = %s AND YEAR(transaction_date) = %s
            """, (current_month, current_year))
            monthly_row = cursor.fetchone()
            monthly_income = monthly_row['monthly_income']
            monthly_expense = monthly_row['monthly_expense']

            # Savings rate for current month
            savings_rate = 0.0
            if monthly_income > 0:
                savings_rate = round(max(0.0, (monthly_income - monthly_expense) / monthly_income) * 100, 1)

            # 3. Monthly Budget & Remaining
            cursor.execute("""
                SELECT CAST(monthly_limit AS DOUBLE) AS monthly_limit
                FROM budgets
                WHERE category = 'Overall' AND month = %s AND year = %s
            """, (current_month, current_year))
            overall_budget = cursor.fetchone()
            budget_limit = overall_budget['monthly_limit'] if overall_budget else 0.0
            remaining_budget = max(0.0, budget_limit - monthly_expense)
            budget_used_percentage = round((monthly_expense / budget_limit * 100), 1) if budget_limit > 0 else 0.0

            # 4. Recent Transactions (latest 5)
            cursor.execute("""
                SELECT id, title, type, CAST(amount AS DOUBLE) as amount, category, 
                       DATE_FORMAT(transaction_date, '%%Y-%%m-%%d') as transaction_date
                FROM transactions
                ORDER BY transaction_date DESC, id DESC
                LIMIT 5
            """)
            recent_transactions = cursor.fetchall()

            # 5. Monthly Trends (Last 6 months)
            cursor.execute("""
                SELECT 
                    DATE_FORMAT(transaction_date, '%%Y-%%m') AS ym,
                    DATE_FORMAT(transaction_date, '%%b %%Y') AS month_label,
                    CAST(COALESCE(SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END), 0) AS DOUBLE) AS income,
                    CAST(COALESCE(SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END), 0) AS DOUBLE) AS expense
                FROM transactions
                WHERE transaction_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH)
                GROUP BY ym, month_label
                ORDER BY ym ASC
            """)
            monthly_trends = cursor.fetchall()

            # 6. Current Month Spending by Category
            cursor.execute("""
                SELECT category, CAST(SUM(amount) AS DOUBLE) AS total
                FROM transactions
                WHERE type = 'Expense' AND MONTH(transaction_date) = %s AND YEAR(transaction_date) = %s
                GROUP BY category
                ORDER BY total DESC
            """, (current_month, current_year))
            category_spending = cursor.fetchall()

            # 7. Budget Health List for widget
            cursor.execute("""
                SELECT b.id, b.category, CAST(b.monthly_limit AS DOUBLE) as monthly_limit,
                       CAST(COALESCE(s.spent, 0) AS DOUBLE) as spent
                FROM budgets b
                LEFT JOIN (
                    SELECT category, SUM(amount) as spent
                    FROM transactions
                    WHERE type = 'Expense' AND MONTH(transaction_date) = %s AND YEAR(transaction_date) = %s
                    GROUP BY category
                ) s ON b.category = s.category
                WHERE b.month = %s AND b.year = %s AND b.category != 'Overall'
                ORDER BY spent DESC
                LIMIT 4
            """, (current_month, current_year, current_month, current_year))
            budget_health_raw = cursor.fetchall()

            budget_health = []
            for b in budget_health_raw:
                limit = b['monthly_limit']
                spent = b['spent']
                used_pct = round((spent / limit) * 100, 1) if limit > 0 else 0.0
                budget_health.append({
                    'category': b['category'],
                    'monthly_limit': limit,
                    'spent': spent,
                    'used_percentage': used_pct
                })

        conn.close()

        return jsonify({
            'summary': {
                'total_balance': total_balance,
                'monthly_income': monthly_income,
                'monthly_expense': monthly_expense,
                'remaining_budget': remaining_budget,
                'budget_limit': budget_limit,
                'budget_used_percentage': budget_used_percentage,
                'savings_rate': savings_rate
            },
            'recent_transactions': recent_transactions,
            'monthly_trends': monthly_trends,
            'category_spending': category_spending,
            'budget_health': budget_health
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
