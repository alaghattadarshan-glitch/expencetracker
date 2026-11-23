from flask import Blueprint, request, jsonify
from app.database.connection import get_db_connection
from datetime import datetime

budgets_bp = Blueprint('budgets', __name__, url_prefix='/api/budgets')

@budgets_bp.route('', methods=['GET'])
def get_budgets():
    """
    Get budgets with actual spending aggregated from transactions for the given month and year.
    Defaults to current month and year.
    """
    try:
        now = datetime.now()
        month = int(request.args.get('month', now.month))
        year = int(request.args.get('year', now.year))

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 1. Fetch defined budgets for this month/year
            cursor.execute("""
                SELECT id, category, CAST(monthly_limit AS DOUBLE) as monthly_limit, month, year
                FROM budgets
                WHERE month = %s AND year = %s
                ORDER BY (category = 'Overall') DESC, category ASC
            """, (month, year))
            budgets = cursor.fetchall()

            # 2. Fetch actual spending per category for this month/year
            cursor.execute("""
                SELECT category, CAST(SUM(amount) AS DOUBLE) as spent
                FROM transactions
                WHERE type = 'Expense' 
                  AND MONTH(transaction_date) = %s 
                  AND YEAR(transaction_date) = %s
                GROUP BY category
            """, (month, year))
            category_spending = {row['category']: row['spent'] for row in cursor.fetchall()}

            # 3. Overall total spending this month
            cursor.execute("""
                SELECT CAST(COALESCE(SUM(amount), 0) AS DOUBLE) as total_spent
                FROM transactions
                WHERE type = 'Expense' 
                  AND MONTH(transaction_date) = %s 
                  AND YEAR(transaction_date) = %s
            """, (month, year))
            total_spent = cursor.fetchone()['total_spent']

        conn.close()

        # Combine budget limits with real spent calculations
        results = []
        for b in budgets:
            cat = b['category']
            spent = total_spent if cat == 'Overall' else category_spending.get(cat, 0.0)
            limit = b['monthly_limit']
            remaining = max(0.0, limit - spent)
            used_pct = round((spent / limit) * 100, 1) if limit > 0 else 0.0

            results.append({
                'id': b['id'],
                'category': cat,
                'monthly_limit': limit,
                'spent': spent,
                'remaining': remaining,
                'used_percentage': used_pct,
                'month': b['month'],
                'year': b['year']
            })

        return jsonify(results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@budgets_bp.route('', methods=['POST'])
def save_budget():
    """Create or update a budget limit (Upsert by category, month, year)"""
    try:
        data = request.get_json() or {}
        category = data.get('category', '').strip()
        monthly_limit = data.get('monthly_limit')
        now = datetime.now()
        month = int(data.get('month', now.month))
        year = int(data.get('year', now.year))

        if not category:
            return jsonify({'error': 'Category is required'}), 400

        try:
            monthly_limit = float(monthly_limit)
            if monthly_limit <= 0:
                raise ValueError()
        except (TypeError, ValueError):
            return jsonify({'error': 'Monthly limit must be a positive number'}), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Use ON DUPLICATE KEY UPDATE to elegantly handle both insert and edit
            sql = """
                INSERT INTO budgets (category, monthly_limit, month, year)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE monthly_limit = VALUES(monthly_limit)
            """
            cursor.execute(sql, (category, monthly_limit, month, year))
            bid = cursor.lastrowid
        conn.close()

        return jsonify({'message': 'Budget saved successfully', 'id': bid}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@budgets_bp.route('/<int:budget_id>', methods=['DELETE'])
def delete_budget(budget_id):
    """Delete a budget item by ID"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM budgets WHERE id = %s", (budget_id,))
            if not cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Budget not found'}), 404

            cursor.execute("DELETE FROM budgets WHERE id = %s", (budget_id,))
        conn.close()

        return jsonify({'message': 'Budget deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
