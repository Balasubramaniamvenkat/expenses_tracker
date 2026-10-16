import asyncio
import unittest
from unittest.mock import patch

import pandas as pd

from api import categories_hierarchy as hierarchy


def _transactions():
    rows = [
        ('2025-01-31', 'NEFT CR-ICIC0099999-XFORMICS TECHNOLOGIES INDIA PVT LTD-HOLDER-IN1', 100000.0, 'Income', 'Salary'),
        ('2025-02-28', 'NEFT CR-ICIC0099999-XFORMICS TECHNOLOGIES INDIA PVT LTD-HOLDER-IN2', 100000.0, 'Income', 'Salary'),
        ('2025-02-10', 'ACH C- KRITI NUTRIENTS LTD-0000000000000', 3000.0, 'Income', 'Dividends'),
        ('2025-03-05', 'NEFT CR-YESB0000001-ZERODHA BROKING LTD-DSCNB A/C-HOLDER-YESBN1', 5000.0, 'Income', 'Investment Returns'),
        ('2025-03-31', 'INTEREST PAID TILL 31-MAR-2025', 8000.0, 'Income', 'Interest'),
        ('2025-03-07', 'REV-UPI-00771050024065-9886158576@PTAXIS-522107679973-SENT USING PAYTM UPI', 500.0, 'Income', 'Refunds'),
        ('2025-03-08', 'IMPS-533923441244-SRAMALAKSHMI-UTIB-XXXXXX1444-RAJI', 65000.0, 'Individual Transfers', 'IMPS Transfer'),
        ('2025-03-09', 'UPI-SWIGGY-SWIGGY@ICICI-ICIC0DC0099-1-ORDER', -400.0, 'Food & Dining', 'Food Delivery'),
    ]
    return pd.DataFrame(
        rows,
        columns=['Transaction Date', 'Description', 'Amount', 'Category', 'Subcategory'],
    ).assign(**{'Transaction Date': lambda df: pd.to_datetime(df['Transaction Date'])})


class IncomeSourceNameTests(unittest.TestCase):
    def test_names_the_paying_source(self):
        cases = {
            'NEFT CR-ICIC0099999-XFORMICS TECHNOLOGIES INDIA PVT LTD-HOLDER-IN1': 'Xformics Technologies India Pvt Ltd',
            'NEFT CR-YESB0000001-ZERODHA BROKING LTD-DSCNB A/C-HOLDER-YESBN1': 'Zerodha Broking Ltd',
            'ACH C- KRITI NUTRIENTS LTD-0000000000000': 'Kriti Nutrients Ltd',
            'ACH C- COLGATE2NDINTDIV2425-233717': 'Colgate',
            'ACH C- MRS BECT FIN 24 25-77443': 'Mrs Bect Fin',
            'INTEREST PAID TILL 31-DEC-2025': 'Bank Interest',
            'GALAXY SURF DIV24 2500000000000000009492': 'Galaxy Surf',
            'REV-UPI-00771050024065-9886158576@PTAXIS-522107679973-SENT USING PAYTM UPI': 'UPI Reversal',
        }
        for description, expected in cases.items():
            self.assertEqual(hierarchy.extract_income_source(description), expected, description)

    def test_expense_rows_keep_merchant_naming(self):
        description = 'UPI-SWIGGY-SWIGGY@ICICI-ICIC0DC0099-1-ORDER'

        self.assertEqual(
            hierarchy.extract_display_name(description, 'Food & Dining'),
            hierarchy.extract_merchant_name(description),
        )

    def test_income_subcategories_map_to_buckets(self):
        self.assertEqual(hierarchy.income_group_name('Salary'), 'Salary & Earnings')
        for subcategory in ('Dividends', 'Interest', 'Investment Returns'):
            self.assertEqual(hierarchy.income_group_name(subcategory), 'Investment Income')
        for subcategory in ('Refunds', 'Other Income', 'Something New', None):
            self.assertEqual(hierarchy.income_group_name(subcategory), 'Refunds & Other')


class IncomeHierarchyTests(unittest.TestCase):
    def _hierarchy(self, **kwargs):
        with patch.object(hierarchy, 'load_transaction_data', return_value=_transactions()):
            return asyncio.run(hierarchy.get_category_hierarchy(
                start_date=None, end_date=None, **kwargs
            ))

    def test_income_breakdown_groups_sources_and_excludes_transfers_and_expenses(self):
        result = self._hierarchy(transaction_type='income')

        buckets = {item['name']: item for item in result['hierarchy']}
        self.assertEqual(
            set(buckets),
            {'Salary & Earnings', 'Investment Income', 'Refunds & Other'},
        )
        self.assertEqual(buckets['Salary & Earnings']['amount'], 200000.0)
        self.assertEqual(buckets['Investment Income']['amount'], 16000.0)
        self.assertEqual(buckets['Refunds & Other']['amount'], 500.0)
        self.assertEqual(result['summary']['totalAmount'], 216500.0)

        investment_subcategories = {
            sub['name']: sub for sub in buckets['Investment Income']['subcategories']
        }
        self.assertEqual(
            set(investment_subcategories),
            {'Dividends', 'Interest', 'Investment Returns'},
        )
        zerodha = investment_subcategories['Investment Returns']['merchants']
        self.assertEqual(zerodha[0]['name'], 'Zerodha Broking Ltd')
        self.assertEqual(zerodha[0]['amount'], 5000.0)

    def test_expense_breakdown_is_unchanged_by_income_rows(self):
        result = self._hierarchy(transaction_type='expense')

        self.assertEqual([item['name'] for item in result['hierarchy']], ['Food & Dining'])
        self.assertEqual(result['summary']['totalAmount'], 400.0)


class IncomeDrawerTests(unittest.TestCase):
    def _drawer(self, **kwargs):
        params = dict(
            subcategory=None, merchant=None, start_date=None, end_date=None, limit=50, offset=0
        )
        params.update(kwargs)
        with patch.object(hierarchy, 'load_transaction_data', return_value=_transactions()):
            return asyncio.run(hierarchy.get_transactions_by_category(**params))

    def test_income_bucket_lists_only_its_credits(self):
        result = self._drawer(category='Investment Income')

        self.assertEqual(result['total'], 3)
        self.assertEqual(
            {item['subcategory'] for item in result['transactions']},
            {'Dividends', 'Interest', 'Investment Returns'},
        )
        self.assertTrue(all(item['amount'] > 0 for item in result['transactions']))

    def test_income_source_filter_matches_hierarchy_name(self):
        result = self._drawer(
            category='Investment Income',
            subcategory='Investment Returns',
            merchant='Zerodha Broking Ltd',
        )

        self.assertEqual(result['total'], 1)
        self.assertEqual(result['transactions'][0]['amount'], 5000.0)

    def test_drawer_no_longer_returns_account_balance(self):
        result = self._drawer(category='Salary & Earnings')

        self.assertEqual(result['total'], 2)
        self.assertNotIn('balance', result['transactions'][0])

    def test_expense_category_filter_still_works(self):
        result = self._drawer(category='Food & Dining', merchant=None)

        self.assertEqual(result['total'], 1)
        self.assertEqual(result['transactions'][0]['category'], 'Food & Dining')


if __name__ == '__main__':
    unittest.main()
