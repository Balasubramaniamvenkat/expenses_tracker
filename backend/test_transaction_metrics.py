import asyncio
import unittest
from unittest.mock import patch

import pandas as pd

from api import transactions


class TransactionMetricsTests(unittest.TestCase):
    def test_empty_metrics_include_zero_planned_outflows(self):
        with patch.object(transactions, 'get_data_df', return_value=pd.DataFrame()):
            metrics = asyncio.run(transactions.get_transaction_metrics(
                start_date=None,
                end_date=None,
                account=None,
                category=None,
                search=None,
                min_amount=None,
                max_amount=None,
            ))

        self.assertEqual(metrics.total_planned, 0.0)
        self.assertEqual(metrics.monthly_averages['planned'], 0)
        self.assertEqual(metrics.yearly_averages['planned'], 0)

    def test_insurance_filter_reports_planned_outflows_and_averages(self):
        data = pd.DataFrame([
            {
                'Transaction Date': '2025-10-02',
                'Description': 'LIC PREMIUM',
                'Amount': -1200.0,
                'Category': 'Insurance',
            },
            {
                'Transaction Date': '2026-10-04',
                'Description': 'LIC PREMIUM',
                'Amount': -800.0,
                'Category': 'Insurance',
            },
            {
                'Transaction Date': '2026-10-05',
                'Description': 'GROCERY STORE',
                'Amount': -200.0,
                'Category': 'Food & Dining',
            },
        ])

        with patch.object(transactions, 'get_data_df', return_value=data):
            with patch('builtins.print'):
                metrics = asyncio.run(transactions.get_transaction_metrics(
                    start_date=None,
                    end_date=None,
                    account=None,
                    category='Insurance',
                    search=None,
                    min_amount=None,
                    max_amount=None,
                ))

        self.assertEqual(metrics.total_transactions, 2)
        self.assertEqual(metrics.total_income, 0.0)
        self.assertEqual(metrics.total_expenses, 0.0)
        self.assertEqual(metrics.total_planned, 2000.0)
        self.assertEqual(metrics.net_savings, 0.0)
        self.assertAlmostEqual(metrics.monthly_averages['planned'], 2000.0 / 13)
        self.assertEqual(metrics.yearly_averages['planned'], 2000.0)


if __name__ == '__main__':
    unittest.main()
