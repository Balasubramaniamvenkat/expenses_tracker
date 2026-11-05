"""Regression tests for detailed, privacy-sanitized AI transaction context."""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

BACKEND_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(BACKEND_DIR, 'SRC'))
sys.path.insert(0, os.path.join(BACKEND_DIR, 'api'))

import ai_chat  # noqa: E402


class AIChatContextTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.csv_path = os.path.join(self.temp_dir.name, 'transactions.csv')
        pd.DataFrame({
            'Transaction Date': [
                '2026-09-10', '2026-09-25', '2026-08-01', '2025-12-15'
            ],
            'Description': [
                'POS APOLLO PHARMACY 9999999999',
                'UPI-TEST PERSON-test.user@example.invalid-TESTBANK-TESTREF-PAYMENT',
                'BUS CITYTRANSIT TESTREF',
                'POS LOCAL RESTAURANT',
            ],
            'Amount': [-1000, -300, -500, -250],
            'Category': ['Food & Dining', 'Food & Dining', 'Transport', 'Food & Dining'],
            'Account': [
                'PRIVATE_ACCOUNT_A', 'PRIVATE_ACCOUNT_B',
                'PRIVATE_ACCOUNT_C', 'PRIVATE_ACCOUNT_D',
            ],
        }).to_csv(self.csv_path, index=False)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_monthly_totals_and_sanitized_ledger_are_in_chat_context(self):
        with patch.object(ai_chat, 'get_processed_data_path', return_value=self.csv_path):
            context, _, _ = ai_chat.get_transaction_context()

        self.assertIn(
            '2026-09 | Food & Dining: 2 transactions; expenses ₹1,300.00; income ₹0.00',
            context
        )
        self.assertIn('FULL SANITIZED TRANSACTION LEDGER', context)
        self.assertIn('APOLLO PHARMACY', context)
        self.assertIn('CITYTRANSIT', context)
        self.assertIn('Transport', context)
        self.assertIn('XXXXX99999', context)
        self.assertIn('[PAYEE]', context)
        self.assertIn('t***@example.invalid', context)
        self.assertNotIn('9999999999', context)
        self.assertNotIn('TEST PERSON', context)
        self.assertNotIn('test.user@example.invalid', context)
        self.assertNotIn('PRIVATE_ACCOUNT_', context)

    def test_privacy_status_context_omits_detailed_ledger(self):
        with patch.object(ai_chat, 'get_processed_data_path', return_value=self.csv_path):
            context, summary, _ = ai_chat.get_transaction_context(
                include_detailed_transactions=False
            )

        self.assertIn('MONTHLY CATEGORY TOTALS', context)
        self.assertNotIn('FULL SANITIZED TRANSACTION LEDGER', context)
        self.assertGreater(summary['breakdown']['phone_numbers'], 0)

    def test_monthly_trend_query_uses_only_requested_year_aggregates(self):
        query = (
            'I would like to understand expenses on food and restaurant for the year '
            '2026 month wise. I want to know if it increases or decreases'
        )
        with patch.object(ai_chat, 'get_processed_data_path', return_value=self.csv_path):
            context, _, _ = ai_chat.get_transaction_context(user_message=query)

        self.assertIn(
            '2026-09 | Food & Dining: 2 transactions; expenses ₹1,300.00; income ₹0.00',
            context
        )
        self.assertNotIn('- 2025-12 |', context)
        self.assertNotIn('FULL SANITIZED TRANSACTION LEDGER', context)
        self.assertNotIn('TOP SPENDING MERCHANTS', context)
        self.assertNotIn('Total Transactions:', context)

        system_message = ai_chat.build_chat_messages(query, context)[0]
        self.assertIn('aggregate summaries only', system_message.content)
        self.assertIn('do not invent merchant or transaction details', system_message.content)

    def test_explicit_transaction_detail_query_keeps_sanitized_ledger(self):
        query = 'List the individual transactions for Food & Dining month wise in 2026'
        with patch.object(ai_chat, 'get_processed_data_path', return_value=self.csv_path):
            context, _, _ = ai_chat.get_transaction_context(user_message=query)

        self.assertIn('FULL SANITIZED TRANSACTION LEDGER', context)
        self.assertIn('APOLLO PHARMACY', context)
        self.assertIn('LOCAL RESTAURANT', context)

    def test_context_returns_chart_data_only_when_requested(self):
        with patch.object(ai_chat, 'get_processed_data_path', return_value=self.csv_path):
            _, _, chart = ai_chat.get_transaction_context(
                user_message='Show a monthly food chart for 2026'
            )

        self.assertIsNotNone(chart)
        self.assertEqual(chart['type'], 'line')
        self.assertEqual(chart['labels'], ['2026-09'])
        self.assertEqual(chart['datasets'][0]['data'], [1300])

    def test_chart_request_uses_backend_aggregates_for_selected_category(self):
        transactions = pd.DataFrame({
            'Transaction Date': ['2026-09-01', '2026-09-03', '2026-09-15', '2026-10-02'],
            'Amount': [-100, -50, -25, -40],
            'Category': ['Food & Dining', 'Transport', 'Food & Dining', 'Food & Dining'],
            'Description': ['Merchant A', 'Merchant B', 'Merchant A', 'Merchant A'],
        })

        chart = ai_chat.build_ai_chart(
            'Show a line chart of monthly food expenses',
            transactions
        )

        self.assertIsNotNone(chart)
        self.assertEqual(chart['type'], 'line')
        self.assertEqual(chart['labels'], ['2026-09', '2026-10'])
        self.assertEqual(chart['datasets'][0]['data'], [125, 40])

    def test_chart_is_not_returned_unless_requested(self):
        transactions = pd.DataFrame({
            'Transaction Date': ['2026-09-01'],
            'Amount': [-100],
            'Category': ['Food & Dining'],
            'Description': ['POS MERCHANT'],
        })

        self.assertIsNone(
            ai_chat.build_ai_chart('How much did I spend?', transactions)
        )

    def test_daily_chart_filters_explicit_date_range(self):
        transactions = pd.DataFrame({
            'Transaction Date': ['2026-09-01', '2026-09-03', '2026-09-15'],
            'Amount': [-100, -50, -25],
            'Category': ['Food & Dining', 'Transport', 'Food & Dining'],
            'Description': ['Merchant A', 'Merchant B', 'Merchant A'],
        })

        chart = ai_chat.build_ai_chart(
            'Show a daily chart of expenses from 2026-09-01 to 2026-09-03',
            transactions
        )

        self.assertIsNotNone(chart)
        self.assertEqual(chart['labels'], ['2026-09-01', '2026-09-03'])
        self.assertEqual(chart['datasets'][0]['data'], [100, 50])

    def test_weekly_chart_groups_by_monday_starting_weeks(self):
        transactions = pd.DataFrame({
            'Transaction Date': ['2026-09-01', '2026-09-03', '2026-09-15', '2026-10-02'],
            'Amount': [-100, -50, -25, -40],
            'Category': ['Food & Dining', 'Transport', 'Food & Dining', 'Food & Dining'],
            'Description': ['Merchant A', 'Merchant B', 'Merchant A', 'Merchant A'],
        })

        chart = ai_chat.build_ai_chart('Show a weekly expenses chart', transactions)

        self.assertIsNotNone(chart)
        self.assertEqual(chart['labels'], ['2026-08-31', '2026-09-14', '2026-09-28'])
        self.assertEqual(chart['datasets'][0]['data'], [150, 25, 40])

    def test_category_pie_request_creates_doughnut_payload(self):
        transactions = pd.DataFrame({
            'Transaction Date': ['2026-09-01', '2026-09-03', '2026-09-15'],
            'Amount': [-100, -50, -25],
            'Category': ['Food & Dining', 'Transport', 'Food & Dining'],
            'Description': ['Merchant A', 'Merchant B', 'Merchant A'],
        })

        chart = ai_chat.build_ai_chart('Show a pie chart by category', transactions)

        self.assertIsNotNone(chart)
        self.assertEqual(chart['type'], 'doughnut')
        self.assertEqual(chart['labels'], ['Food & Dining', 'Transport'])
        self.assertEqual(chart['datasets'][0]['data'], [125, 50])


if __name__ == '__main__':
    unittest.main()
