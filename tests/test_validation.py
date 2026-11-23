import unittest
import json
from unittest.mock import patch, MagicMock
from app import create_app

class ExpenseTrackerValidationTestCase(unittest.TestCase):
    """
    Tests input validations, HTTP error codes, and request parsing
    without relying on external live databases.
    """
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_health_check(self):
        """Test health check route"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data.get('status'), 'healthy')

    def test_create_transaction_missing_fields(self):
        """Test that validation fails when title or amount is missing"""
        # Missing title
        res = self.client.post('/api/transactions', json={
            'type': 'Expense',
            'amount': 150.0,
            'category': 'Food',
            'transaction_date': '2026-11-23'
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('Title is required', json.loads(res.data)['error'])

        # Invalid amount
        res = self.client.post('/api/transactions', json={
            'title': 'Coffee',
            'type': 'Expense',
            'amount': -10.0,
            'category': 'Food',
            'transaction_date': '2026-11-23'
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('Amount must be a positive number', json.loads(res.data)['error'])

    def test_create_transaction_invalid_category(self):
        """Test rejection of mismatched or unsupported categories"""
        res = self.client.post('/api/transactions', json={
            'title': 'Salary Check',
            'type': 'Income',
            'amount': 50000.0,
            'category': 'Food', # Food is an expense category, not income
            'transaction_date': '2026-11-23'
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('Invalid category', json.loads(res.data)['error'])

    def test_budget_validation(self):
        """Test budget input constraints"""
        res = self.client.post('/api/budgets', json={
            'category': 'Food',
            'monthly_limit': -500,
            'month': 11,
            'year': 2026
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('Monthly limit must be a positive number', json.loads(res.data)['error'])

    def test_settings_validation(self):
        """Test user display name cannot be empty"""
        res = self.client.put('/api/settings', json={
            'display_name': '',
            'currency': '₹'
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('Display name cannot be empty', json.loads(res.data)['error'])

if __name__ == '__main__':
    unittest.main()
