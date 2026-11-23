from flask import Blueprint, request, jsonify
from app.database.connection import get_db_connection
from datetime import datetime

transactions_bp = Blueprint('transactions', __name__, url_prefix='/api/transactions')

EXPENSE_CATEGORIES = [
    'Food', 'Transport', 'Shopping', 'Bills', 'Education',
    'Health', 'Entertainment', 'Rent', 'Travel', 'Other'
]

INCOME_CATEGORIES = [
    'Salary', 'Freelance', 'Business', 'Allowance', 'Initial Balance', 'Other'
]

@transactions_bp.route('', methods=['GET'])
def get_transactions():
    """
    Fetch paginated, filtered, and sorted transactions.
    Supports query params: page, limit, search, type, category, start_date, end_date, sort
    """
    try:
        page = max(1, int(request.args.get('page', 1)))
        limit = max(1, min(100, int(request.args.get('limit', 10))))
        offset = (page - 1) * limit

        search = request.args.get('search', '').strip()
        tx_type = request.args.get('type', '').strip()
        category = request.args.get('category', '').strip()
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        sort_by = request.args.get('sort', 'date_desc').strip()

        # Build dynamic SQL query with parameterized values
        conditions = []
        params = []

        if search:
            conditions.append("(title LIKE %s OR description LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])

        if tx_type in ('Income', 'Expense'):
            conditions.append("type = %s")
            params.append(tx_type)

        if category:
            conditions.append("category = %s")
            params.append(category)

        if start_date:
            conditions.append("transaction_date >= %s")
            params.append(start_date)

        if end_date:
            conditions.append("transaction_date <= %s")
            params.append(end_date)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        # Sorting logic
        sort_map = {
            'date_desc': 'transaction_date DESC, id DESC',
            'date_asc': 'transaction_date ASC, id ASC',
            'amount_desc': 'amount DESC',
            'amount_asc': 'amount ASC'
        }
        order_clause = f" ORDER BY {sort_map.get(sort_by, 'transaction_date DESC, id DESC')}"

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 1. Total count query
            count_sql = f"SELECT COUNT(*) AS total FROM transactions{where_clause}"
            cursor.execute(count_sql, tuple(params))
            total = cursor.fetchone()['total']

            # 2. Paged transactions query
            data_sql = f"""
                SELECT id, title, type, CAST(amount AS DOUBLE) as amount, category, 
                       DATE_FORMAT(transaction_date, '%%Y-%%m-%%d') as transaction_date,
                       description, created_at, updated_at
                FROM transactions
                {where_clause}
                {order_clause}
                LIMIT %s OFFSET %s
            """
            cursor.execute(data_sql, tuple(params + [limit, offset]))
            transactions = cursor.fetchall()

        conn.close()

        total_pages = (total + limit - 1) // limit if total > 0 else 1

        return jsonify({
            'transactions': transactions,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'totalPages': total_pages
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transactions_bp.route('/<int:tx_id>', methods=['GET'])
def get_transaction(tx_id):
    """Retrieve a single transaction by ID"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT id, title, type, CAST(amount AS DOUBLE) as amount, category,
                       DATE_FORMAT(transaction_date, '%%Y-%%m-%%d') as transaction_date,
                       description, created_at, updated_at
                FROM transactions WHERE id = %s
            """
            cursor.execute(sql, (tx_id,))
            tx = cursor.fetchone()
        conn.close()

        if not tx:
            return jsonify({'error': 'Transaction not found'}), 404

        return jsonify(tx), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transactions_bp.route('', methods=['POST'])
def create_transaction():
    """Create a new transaction with strict validation"""
    try:
        data = request.get_json() or {}
        title = data.get('title', '').strip()
        tx_type = data.get('type', '').strip()
        amount = data.get('amount')
        category = data.get('category', '').strip()
        tx_date = data.get('transaction_date', '').strip()
        description = data.get('description', '').strip()

        # Validation
        if not title:
            return jsonify({'error': 'Title is required'}), 400

        if tx_type not in ('Income', 'Expense'):
            return jsonify({'error': 'Type must be either Income or Expense'}), 400

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError()
        except (TypeError, ValueError):
            return jsonify({'error': 'Amount must be a positive number'}), 400

        valid_categories = INCOME_CATEGORIES if tx_type == 'Income' else EXPENSE_CATEGORIES
        if category not in valid_categories:
            return jsonify({'error': f'Invalid category "{category}" for {tx_type}'}), 400

        try:
            datetime.strptime(tx_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Date must be formatted as YYYY-MM-DD'}), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO transactions (title, type, amount, category, transaction_date, description)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (title, tx_type, amount, category, tx_date, description or None))
            new_id = cursor.lastrowid
        conn.close()

        return jsonify({'message': 'Transaction created successfully', 'id': new_id}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transactions_bp.route('/<int:tx_id>', methods=['PUT'])
def update_transaction(tx_id):
    """Update an existing transaction"""
    try:
        data = request.get_json() or {}
        title = data.get('title', '').strip()
        tx_type = data.get('type', '').strip()
        amount = data.get('amount')
        category = data.get('category', '').strip()
        tx_date = data.get('transaction_date', '').strip()
        description = data.get('description', '').strip()

        # Validation
        if not title:
            return jsonify({'error': 'Title is required'}), 400

        if tx_type not in ('Income', 'Expense'):
            return jsonify({'error': 'Type must be either Income or Expense'}), 400

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError()
        except (TypeError, ValueError):
            return jsonify({'error': 'Amount must be a positive number'}), 400

        valid_categories = INCOME_CATEGORIES if tx_type == 'Income' else EXPENSE_CATEGORIES
        if category not in valid_categories:
            return jsonify({'error': f'Invalid category "{category}" for {tx_type}'}), 400

        try:
            datetime.strptime(tx_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Date must be formatted as YYYY-MM-DD'}), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Check existence
            cursor.execute("SELECT id FROM transactions WHERE id = %s", (tx_id,))
            if not cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Transaction not found'}), 404

            sql = """
                UPDATE transactions
                SET title = %s, type = %s, amount = %s, category = %s, transaction_date = %s, description = %s
                WHERE id = %s
            """
            cursor.execute(sql, (title, tx_type, amount, category, tx_date, description or None, tx_id))
        conn.close()

        return jsonify({'message': 'Transaction updated successfully', 'id': tx_id}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transactions_bp.route('/<int:tx_id>', methods=['DELETE'])
def delete_transaction(tx_id):
    """Delete a transaction by ID"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM transactions WHERE id = %s", (tx_id,))
            if not cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Transaction not found'}), 404

            cursor.execute("DELETE FROM transactions WHERE id = %s", (tx_id,))
        conn.close()

        return jsonify({'message': 'Transaction deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
