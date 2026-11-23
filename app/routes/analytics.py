from flask import Blueprint, jsonify
from app.database.connection import get_db_connection

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('', methods=['GET'])
def get_analytics():
    """
    Returns deep financial analytics calculated from SQL:
    - Monthly trends (Income, Expense, Net Savings)
    - Spending by category
    - Total net savings
    - Highest spending category & amount
    - Average daily expenses
    - Total transaction count
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 1. Total counts and net savings
            cursor.execute("""
                SELECT 
                    COUNT(*) as tx_count,
                    CAST(COALESCE(SUM(CASE WHEN type = 'Income' THEN amount ELSE -amount END), 0) AS DOUBLE) AS total_savings,
                    CAST(COALESCE(SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END), 0) AS DOUBLE) AS total_income,
                    CAST(COALESCE(SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END), 0) AS DOUBLE) AS total_expense,
                    COUNT(DISTINCT CASE WHEN type = 'Expense' THEN transaction_date END) as active_expense_days
                FROM transactions
            """)
            stats = cursor.fetchone()
            tx_count = stats['tx_count']
            total_savings = stats['total_savings']
            total_income = stats['total_income']
            total_expense = stats['total_expense']
            active_days = max(1, stats['active_expense_days'])
            avg_daily_expense = round(total_expense / active_days, 2)

            savings_rate = round((total_savings / total_income * 100), 1) if total_income > 0 else 0.0

            # 2. Highest spending category
            cursor.execute("""
                SELECT category, CAST(SUM(amount) AS DOUBLE) as total
                FROM transactions
                WHERE type = 'Expense'
                GROUP BY category
                ORDER BY total DESC
                LIMIT 1
            """)
            top_cat_row = cursor.fetchone()
            highest_category = top_cat_row['category'] if top_cat_row else 'None'
            highest_amount = top_cat_row['total'] if top_cat_row else 0.0

            # 3. Monthly Trends (Income vs Expense vs Savings)
            cursor.execute("""
                SELECT 
                    DATE_FORMAT(transaction_date, '%%Y-%%m') AS ym,
                    DATE_FORMAT(transaction_date, '%%b %%Y') AS month_label,
                    CAST(COALESCE(SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END), 0) AS DOUBLE) AS income,
                    CAST(COALESCE(SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END), 0) AS DOUBLE) AS expense,
                    CAST(COALESCE(SUM(CASE WHEN type = 'Income' THEN amount ELSE -amount END), 0) AS DOUBLE) AS savings
                FROM transactions
                GROUP BY ym, month_label
                ORDER BY ym ASC
            """)
            trends = cursor.fetchall()

            # 4. Spending by category overall
            cursor.execute("""
                SELECT category, CAST(SUM(amount) AS DOUBLE) as total
                FROM transactions
                WHERE type = 'Expense'
                GROUP BY category
                ORDER BY total DESC
            """)
            category_spending = cursor.fetchall()

        conn.close()

        return jsonify({
            'metrics': {
                'total_savings': total_savings,
                'savings_rate': savings_rate,
                'highest_spending_category': highest_category,
                'highest_spending_amount': highest_amount,
                'average_daily_expense': avg_daily_expense,
                'total_transaction_count': tx_count
            },
            'trends': trends,
            'category_spending': category_spending
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
