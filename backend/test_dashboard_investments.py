import asyncio
import unittest
from unittest.mock import patch

import pandas as pd

from api import categories_hierarchy, dashboard
from SRC.refined_categories import get_category_group


class DashboardInvestmentTests(unittest.TestCase):
    def setUp(self):
        self.transactions = pd.DataFrame([
            {
                'Transaction Date': '2026-01-10',
                'Description': 'ZERODHA BROKING LTD',
                'Amount': -1000.0,
                'Category': 'Investments',
                'Subcategory': 'Stocks & Trading',
            },
            {
                'Transaction Date': '2026-01-11',
                'Description': 'COLLEGE TUITION',
                'Amount': -500.0,
                'Category': 'Education',
                'Subcategory': 'College & University',
            },
            {
                'Transaction Date': '2026-01-12',
                'Description': 'GROCERY STORE',
                'Amount': -200.0,
                'Category': 'Food & Dining',
                'Subcategory': 'Groceries',
            },
            {
                'Transaction Date': '2026-01-13',
                'Description': 'MONTHLY SALARY',
                'Amount': 5000.0,
                'Category': 'Income',
                'Subcategory': 'Salary',
            },
        ])
        self.transactions['Transaction Date'] = pd.to_datetime(self.transactions['Transaction Date'])

    def test_education_is_grouped_with_investments_not_planned(self):
        self.assertEqual(get_category_group('Education'), 'Investment')

        with patch.object(dashboard, 'load_transaction_data', return_value=self.transactions):
            summary = asyncio.run(dashboard.get_dashboard_summary())

        self.assertEqual(summary['totalInvestments'], 1500.0)
        self.assertEqual(summary['totalPlanned'], 0.0)
        self.assertEqual(summary['monthlyTrend'][0]['investments'], 1500.0)

    def test_investment_hierarchy_includes_investments_and_education(self):
        with patch.object(categories_hierarchy, 'load_transaction_data', return_value=self.transactions):
            with patch('builtins.print'):
                result = asyncio.run(categories_hierarchy.get_category_hierarchy(
                    start_date=None,
                    end_date=None,
                    transaction_type='investment',
                ))

        categories = {category['name']: category for category in result['hierarchy']}
        self.assertEqual(set(categories), {'Investments', 'Education'})
        self.assertEqual(result['summary']['totalAmount'], 1500.0)


if __name__ == '__main__':
    unittest.main()
