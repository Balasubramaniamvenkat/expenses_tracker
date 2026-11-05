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
            {
                'Transaction Date': '2026-01-14',
                'Description': 'INSURANCE PREMIUM',
                'Amount': -300.0,
                'Category': 'Insurance',
                'Subcategory': 'Life Insurance',
            },
            {
                'Transaction Date': '2026-01-15',
                'Description': 'TRANSFER SENT',
                'Amount': -100.0,
                'Category': 'Individual Transfers',
                'Subcategory': 'Personal Payment',
            },
            {
                'Transaction Date': '2026-01-16',
                'Description': 'TRANSFER RECEIVED',
                'Amount': 50.0,
                'Category': 'Individual Transfers',
                'Subcategory': 'Personal Payment',
            },
        ])
        self.transactions['Transaction Date'] = pd.to_datetime(self.transactions['Transaction Date'])

    def test_education_is_grouped_with_investments_not_planned(self):
        self.assertEqual(get_category_group('Education'), 'Investment')

        with patch.object(dashboard, 'load_transaction_data', return_value=self.transactions):
            summary = asyncio.run(dashboard.get_dashboard_summary())

        self.assertEqual(summary['totalInvestments'], 1500.0)
        self.assertEqual(summary['totalPlanned'], 300.0)
        self.assertEqual(summary['totalTransfers'], 150.0)
        self.assertEqual(summary['monthlyTrend'][0]['investments'], 1500.0)
        self.assertEqual(summary['monthlyTrend'][0]['planned'], 300.0)
        self.assertEqual(summary['monthlyTrend'][0]['transfers'], 150.0)

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

    def test_dashboard_analytics_can_be_filtered_to_one_account(self):
        data = self.transactions.copy()
        data['Account'] = [
            'Primary', 'Secondary', 'Primary', 'Primary',
            'Secondary', 'Secondary', 'Secondary',
        ]

        with patch.object(dashboard, 'load_transaction_data', return_value=data):
            summary = asyncio.run(dashboard.get_dashboard_summary(account='Primary'))
        self.assertEqual(summary['transactionCount'], 3)
        self.assertEqual(summary['totalIncome'], 5000.0)
        self.assertEqual(summary['totalExpenses'], 200.0)
        self.assertEqual(summary['totalInvestments'], 1000.0)

        with patch.object(categories_hierarchy, 'load_transaction_data', return_value=data):
            with patch('builtins.print'):
                hierarchy = asyncio.run(categories_hierarchy.get_category_hierarchy(
                    start_date=None,
                    end_date=None,
                    transaction_type='expense',
                    account='Primary',
                ))
            trends = asyncio.run(categories_hierarchy.get_trend_comparison(
                months=3,
                account='Primary',
            ))
            transactions = asyncio.run(categories_hierarchy.get_transactions_by_category(
                category='Food & Dining',
                subcategory=None,
                merchant=None,
                start_date=None,
                end_date=None,
                account='Primary',
                limit=50,
                offset=0,
            ))

        self.assertEqual(
            {category['name'] for category in hierarchy['hierarchy']},
            {'Food & Dining'},
        )
        self.assertEqual(hierarchy['summary']['totalAmount'], 200.0)
        self.assertEqual(trends['comparisons']['income']['current'], 5000.0)
        self.assertEqual(trends['comparisons']['expenses']['current'], 200.0)
        self.assertEqual(transactions['total'], 1)
        self.assertEqual(transactions['transactions'][0]['amount'], -200.0)

    def test_planned_and_transfer_groups_can_be_drilled_down(self):
        with patch.object(categories_hierarchy, 'load_transaction_data', return_value=self.transactions):
            with patch('builtins.print'):
                planned = asyncio.run(categories_hierarchy.get_category_hierarchy(
                    start_date=None,
                    end_date=None,
                    transaction_type='planned',
                ))
                transfers = asyncio.run(categories_hierarchy.get_category_hierarchy(
                    start_date=None,
                    end_date=None,
                    transaction_type='transfer',
                ))

        self.assertEqual({category['name'] for category in planned['hierarchy']}, {'Insurance'})
        self.assertEqual(planned['summary']['totalAmount'], 300.0)
        self.assertEqual(
            {category['name'] for category in transfers['hierarchy']},
            {'Individual Transfers'},
        )
        self.assertEqual(transfers['summary']['totalAmount'], 150.0)


if __name__ == '__main__':
    unittest.main()
