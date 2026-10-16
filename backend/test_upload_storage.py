import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import UploadFile

from api import upload
from SRC.data_extraction import get_account_name


class UploadStorageTests(unittest.TestCase):
    def test_identical_content_reuses_existing_source_file(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(upload, 'inputs_dir', directory):
                first = UploadFile(filename='statement.csv', file=io.BytesIO(b'date,amount\n'))
                first_path, first_duplicate = upload.save_uploaded_file(first)

                renamed_copy = UploadFile(
                    filename='statement_copy.csv',
                    file=io.BytesIO(b'date,amount\n'),
                )
                duplicate_path, is_duplicate = upload.save_uploaded_file(renamed_copy)

            self.assertFalse(first_duplicate)
            self.assertTrue(is_duplicate)
            self.assertEqual(duplicate_path, first_path)
            self.assertEqual(len(list(Path(directory).glob('*.csv'))), 1)

    def test_new_contents_overwrite_same_name_instead_of_creating_timestamp_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(upload, 'inputs_dir', directory):
                first = UploadFile(filename='statement.csv', file=io.BytesIO(b'first'))
                first_path, _ = upload.save_uploaded_file(first)
                updated = UploadFile(filename='statement.csv', file=io.BytesIO(b'second'))
                updated_path, is_duplicate = upload.save_uploaded_file(updated)

            self.assertFalse(is_duplicate)
            self.assertEqual(updated_path, first_path)
            self.assertEqual(Path(first_path).read_bytes(), b'second')
            self.assertEqual(len(list(Path(directory).glob('*.csv'))), 1)

    def test_distinct_same_named_files_in_one_batch_keep_account_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            reserved_names = set()
            with patch.object(upload, 'inputs_dir', directory):
                first = UploadFile(filename='Account_XX4065.csv', file=io.BytesIO(b'first'))
                second = UploadFile(filename='Account_XX4065.csv', file=io.BytesIO(b'second'))
                first_path, _ = upload.save_uploaded_file(first, reserved_names)
                second_path, _ = upload.save_uploaded_file(second, reserved_names)

            self.assertNotEqual(first_path, second_path)
            self.assertEqual(get_account_name('Account_XX4065.csv'), 'Account XX4065')
            self.assertEqual(get_account_name('Account_XX4065_2.csv'), 'Account XX4065')
            self.assertEqual(len(list(Path(directory).glob('*.csv'))), 2)


if __name__ == '__main__':
    unittest.main()
