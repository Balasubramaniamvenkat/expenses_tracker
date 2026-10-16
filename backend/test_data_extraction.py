import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from SRC import data_extraction
from SRC.data_extraction import extract_data_from_file


class DataExtractionTests(unittest.TestCase):
    def test_normalizes_split_debit_and_credit_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            statement_path = Path(directory) / 'acc1.csv'
            pd.DataFrame({
                'Tran Date': ['01-01-2026', '02-01-2026'],
                'PARTICULARS': ['Debit item', 'Credit item'],
                'DR': ['125.50', ' '],
                'CR': [' ', '800.00'],
                'BAL': ['900.00', '1700.00'],
            }).to_csv(statement_path, index=False)

            transactions = extract_data_from_file(str(statement_path))

        self.assertIsNotNone(transactions)
        self.assertEqual(
            list(transactions.columns),
            ['Transaction Date', 'Description', 'Amount', 'Balance', 'Account'],
        )
        self.assertEqual(transactions['Amount'].tolist(), [-125.5, 800.0])
        self.assertEqual(transactions['Account'].unique().tolist(), ['acc1'])

    def test_finds_excel_headers_after_preamble_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            statement_path = Path(directory) / 'bank.xlsx'
            rows = [
                ['Bank Statement'],
                ['Generated for local testing'],
                ['Tran Date', 'PARTICULARS', 'DR', 'CR', 'BAL'],
                ['03-01-2026', 'Excel debit', '250.00', '', '1450.00'],
            ]
            pd.DataFrame(rows).to_excel(statement_path, index=False, header=False)

            transactions = extract_data_from_file(str(statement_path))

        self.assertIsNotNone(transactions)
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions.loc[0, 'Description'], 'Excel debit')
        self.assertEqual(transactions.loc[0, 'Amount'], -250.0)
        self.assertEqual(transactions.loc[0, 'Balance'], 1450.0)

    def test_combines_statements_without_collapsing_distinct_accounts(self):
        with tempfile.TemporaryDirectory() as directory:
            project_root = Path(directory)
            (project_root / 'backend' / 'SRC').mkdir(parents=True)
            inputs = project_root / 'inputs'
            inputs.mkdir()

            statement = pd.DataFrame({
                'Tran Date': ['01-01-2026', '02-01-2026'],
                'PARTICULARS': ['Grocery', 'School fee'],
                'DR': ['500.00', '1000.00'],
                'CR': ['', ''],
                'BAL': ['9500.00', '8500.00'],
            })
            statement.to_csv(inputs / 'bank_account.csv', index=False)
            statement.to_csv(inputs / 'bank_account_copy.csv', index=False)
            statement.iloc[[0]].to_csv(inputs / 'second_account.csv', index=False)
            statement.to_csv(inputs / 'synthetic_test.csv', index=False)
            statement.to_csv(inputs / 'test_fixture.csv', index=False)
            statement.to_csv(inputs / 'test_20251221_132158.csv', index=False)

            masked_account_statement = pd.DataFrame({
                'Tran Date': ['03-01-2026'],
                'PARTICULARS': ['Masked account shared transaction'],
                'DR': ['200.00'],
                'CR': [''],
                'BAL': ['8000.00'],
            })
            extended_masked_account_statement = pd.concat([
                masked_account_statement,
                pd.DataFrame({
                    'Tran Date': ['04-01-2026'],
                    'PARTICULARS': ['Masked account new transaction'],
                    'DR': ['300.00'],
                    'CR': [''],
                    'BAL': ['7700.00'],
                }),
            ], ignore_index=True)
            masked_account_statement.to_csv(
                inputs / 'Acct_Statement_XX4065_2025.csv',
                index=False,
            )
            extended_masked_account_statement.to_csv(
                inputs / 'Acct_Statement_XXXXXXXX4065_2026.csv',
                index=False,
            )

            module_path = project_root / 'backend' / 'SRC' / 'data_extraction.py'
            with patch.object(data_extraction, '__file__', str(module_path)):
                transactions = data_extraction.get_all_transaction_data()

        self.assertEqual(len(transactions), 7)
        self.assertEqual(transactions['Account'].value_counts().to_dict(), {
            'bank_account': 2,
            'bank_account_copy': 2,
            'second_account': 1,
            'Account XX4065': 2,
        })
        self.assertEqual(set(transactions['Source_File']), {
            'bank_account.csv',
            'bank_account_copy.csv',
            'second_account.csv',
            'Acct_Statement_XX4065_2025.csv',
            'Acct_Statement_XXXXXXXX4065_2026.csv',
        })

    def test_active_manifest_replaces_prior_batch_files(self):
        with tempfile.TemporaryDirectory() as directory:
            project_root = Path(directory)
            inputs = project_root / 'inputs'
            inputs.mkdir()
            for file_name in ('previous.csv', 'new.csv'):
                (inputs / file_name).write_text('statement', encoding='utf-8')

            data_extraction.set_active_statement_files(['previous.csv'], str(inputs))
            data_extraction.set_active_statement_files(['new.csv'], str(inputs))
            manifest = data_extraction._get_active_statement_files(str(inputs))

        self.assertEqual(manifest, ['new.csv'])

    def test_replace_processed_data_drops_previous_rows_and_deduplicates_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            project_root = Path(directory)
            src_dir = project_root / 'backend' / 'SRC'
            src_dir.mkdir(parents=True)
            processed_data = project_root / 'processed_data.csv'
            pd.DataFrame({
                'Transaction Date': ['2025-12-31'],
                'Description': ['Previous dataset transaction'],
                'Amount': [-900.0],
                'Account': ['Account XX4065'],
            }).to_csv(processed_data, index=False)

            new_transactions = pd.DataFrame({
                'Transaction Date': ['2026-01-01', '2026-01-01'],
                'Description': ['Current batch transaction'] * 2,
                'Amount': [-250.0, -250.0],
                'Account': ['Account XX4065'] * 2,
            })
            module_path = src_dir / 'data_extraction.py'
            with patch.object(data_extraction, '__file__', str(module_path)):
                replaced = data_extraction.replace_processed_data(new_transactions)
                saved = pd.read_csv(processed_data)

        self.assertEqual(replaced['Description'].tolist(), ['Current batch transaction'])
        self.assertEqual(saved['Description'].tolist(), ['Current batch transaction'])

    def test_legacy_bootstrap_uses_only_files_in_active_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            project_root = Path(directory)
            src_dir = project_root / 'backend' / 'SRC'
            src_dir.mkdir(parents=True)
            inputs = project_root / 'inputs'
            inputs.mkdir()
            for file_name in ('previous.csv', 'current.csv'):
                (inputs / file_name).write_text('statement', encoding='utf-8')
            data_extraction.set_active_statement_files(['current.csv'], str(inputs))

            def extract_statement(path):
                return pd.DataFrame({
                    'Transaction Date': [pd.Timestamp('2026-01-01')],
                    'Description': [Path(path).name],
                    'Amount': [-100.0],
                    'Account': ['Account XX4065'],
                })

            module_path = src_dir / 'data_extraction.py'
            with patch.object(data_extraction, '__file__', str(module_path)):
                with patch.object(
                    data_extraction,
                    'extract_data_from_file',
                    side_effect=extract_statement,
                ) as extract:
                    transactions = data_extraction.get_all_transaction_data()

        self.assertEqual(extract.call_count, 1)
        self.assertEqual(transactions['Source_File'].tolist(), ['current.csv'])

    def test_get_all_transaction_data_loads_snapshot_without_reprocessing_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            project_root = Path(directory)
            src_dir = project_root / 'backend' / 'SRC'
            src_dir.mkdir(parents=True)
            inputs = project_root / 'inputs'
            inputs.mkdir()
            (inputs / 'not_reprocessed.csv').write_text('source data', encoding='utf-8')
            pd.DataFrame({
                'Transaction Date': ['2026-01-01'],
                'Description': ['Saved transaction'],
                'Amount': [-100.0],
                'Account': ['Account XX4065'],
            }).to_csv(project_root / 'processed_data.csv', index=False)

            module_path = src_dir / 'data_extraction.py'
            with patch.object(data_extraction, '__file__', str(module_path)):
                with patch.object(data_extraction, 'extract_data_from_file') as extract:
                    transactions = data_extraction.get_all_transaction_data()

        extract.assert_not_called()
        self.assertEqual(transactions['Description'].tolist(), ['Saved transaction'])


if __name__ == '__main__':
    unittest.main()