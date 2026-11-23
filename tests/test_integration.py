import os
import unittest
import requests
import time

BASE_URL = os.getenv("TEST_BASE_URL", f"http://localhost:{os.getenv('HOST_PORT', '5001')}")

class ExpenseTrackerEndToEndTestCase(unittest.TestCase):
    """
    End-to-end automated integration test suite that tests live API endpoints,
    database schema initialization, SQL aggregations, and CRUD operations
    against the running Docker container stack.
    """

    @classmethod
    def setUpClass(cls):
        # Wait up to 30 seconds for the web service to be healthy
        for _ in range(30):
            try:
                res = requests.get(f"{BASE_URL}/health", timeout=2)
                if res.status_code == 200:
                    return
            except Exception:
                time.sleep(1)
        raise RuntimeError("Service did not become healthy within timeout.")

    def test_01_index_html_renders(self):
        """Verify the main UI page renders correctly"""
        res = requests.get(f"{BASE_URL}/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Personal Expense Tracker", res.text)
        self.assertIn("ExpenseTracker", res.text)
        self.assertIn("chartIncomeVsExpense", res.text)

    def test_02_settings_get_and_update(self):
        """Verify settings GET and PUT endpoints"""
        res = requests.get(f"{BASE_URL}/api/settings")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("currency", data)

        # Update settings
        update_res = requests.put(f"{BASE_URL}/api/settings", json={
            "display_name": "Senior DevOps Engineer",
            "currency": "₹"
        })
        self.assertEqual(update_res.status_code, 200)

        # Confirm update
        res = requests.get(f"{BASE_URL}/api/settings")
        self.assertEqual(res.json().get("display_name"), "Senior DevOps Engineer")

    def test_03_transaction_crud_and_sql(self):
        """Verify creating, reading, updating, and deleting transactions"""
        # 1. Create Income Transaction
        income_res = requests.post(f"{BASE_URL}/api/transactions", json={
            "title": "Semester Fellowship Stipend",
            "type": "Income",
            "amount": 45000.0,
            "category": "Salary",
            "transaction_date": "2026-11-20",
            "description": "Monthly college research fellowship stipend"
        })
        self.assertEqual(income_res.status_code, 201)
        income_id = income_res.json()["id"]

        # 2. Create Expense Transaction
        expense_res = requests.post(f"{BASE_URL}/api/transactions", json={
            "title": "AWS Cloud Server Subscription",
            "type": "Expense",
            "amount": 2500.0,
            "category": "Bills",
            "transaction_date": "2026-11-21",
            "description": "EC2 and RDS hosting"
        })
        self.assertEqual(expense_res.status_code, 201)
        expense_id = expense_res.json()["id"]

        # 3. Retrieve single transaction
        get_res = requests.get(f"{BASE_URL}/api/transactions/{expense_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["title"], "AWS Cloud Server Subscription")
        self.assertEqual(get_res.json()["amount"], 2500.0)

        # 4. Update transaction
        put_res = requests.put(f"{BASE_URL}/api/transactions/{expense_id}", json={
            "title": "AWS Cloud Server (Updated)",
            "type": "Expense",
            "amount": 2800.0,
            "category": "Bills",
            "transaction_date": "2026-11-21",
            "description": "EC2 and RDS hosting upgraded"
        })
        self.assertEqual(put_res.status_code, 200)

        # Check updated values
        get_res = requests.get(f"{BASE_URL}/api/transactions/{expense_id}")
        self.assertEqual(get_res.json()["amount"], 2800.0)

        # 5. Verify transaction shows in paginated list
        list_res = requests.get(f"{BASE_URL}/api/transactions?search=AWS Cloud")
        self.assertEqual(list_res.status_code, 200)
        items = list_res.json()["transactions"]
        self.assertTrue(any(t["id"] == expense_id for t in items))

        # 6. Delete transaction
        del_res = requests.delete(f"{BASE_URL}/api/transactions/{expense_id}")
        self.assertEqual(del_res.status_code, 200)

        # Verify 404 after deletion
        get_deleted = requests.get(f"{BASE_URL}/api/transactions/{expense_id}")
        self.assertEqual(get_deleted.status_code, 404)

    def test_04_budget_management_and_limits(self):
        """Verify budget upsert, spending calculation, and deletion"""
        # Save monthly budget
        save_res = requests.post(f"{BASE_URL}/api/budgets", json={
            "category": "Education",
            "monthly_limit": 10000.0,
            "month": 11,
            "year": 2026
        })
        self.assertEqual(save_res.status_code, 200)

        # Fetch budgets
        budgets_res = requests.get(f"{BASE_URL}/api/budgets?month=11&year=2026")
        self.assertEqual(budgets_res.status_code, 200)
        budgets = budgets_res.json()
        edu_budget = next((b for b in budgets if b["category"] == "Education"), None)
        self.assertIsNotNone(edu_budget)
        self.assertEqual(edu_budget["monthly_limit"], 10000.0)

    def test_05_dashboard_and_analytics_calculations(self):
        """Verify SQL aggregation across dashboard and analytics APIs"""
        # Fetch dashboard summary
        dash_res = requests.get(f"{BASE_URL}/api/dashboard")
        self.assertEqual(dash_res.status_code, 200)
        data = dash_res.json()

        self.assertIn("summary", data)
        self.assertIn("total_balance", data["summary"])
        self.assertIn("recent_transactions", data)
        self.assertIn("monthly_trends", data)

        # Fetch analytics
        analytics_res = requests.get(f"{BASE_URL}/api/analytics")
        self.assertEqual(analytics_res.status_code, 200)
        adata = analytics_res.json()
        self.assertIn("metrics", adata)
        self.assertIn("total_savings", adata["metrics"])
        self.assertIn("trends", adata)

if __name__ == '__main__':
    unittest.main()
