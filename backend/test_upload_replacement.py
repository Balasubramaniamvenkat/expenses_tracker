import io
import os
import unittest
from unittest.mock import patch

import pandas as pd
from fastapi import UploadFile

from api import upload


class UploadReplacementTests(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def _file(name):
        return UploadFile(filename=name, file=io.BytesIO(b"statement"))

    @staticmethod
    def _successful_result(name, description):
        return (
            upload.FileProcessingResult(
                filename=name,
                success=True,
                message="Processed",
                records_processed=1,
                file_size=9,
                summary={},
            ),
            pd.DataFrame({
                "Transaction Date": [pd.Timestamp("2026-01-01")],
                "Description": [description],
                "Amount": [-100.0],
                "Account": ["Account XX4065"],
            }),
        )

    async def test_single_upload_replaces_dataset_and_manifest(self):
        result, transactions = self._successful_result(
            "current.csv",
            "Current transaction",
        )
        file_path = os.path.join("C:\\uploads", "current.csv")

        with (
            patch.object(upload, "save_uploaded_file", return_value=(file_path, False)),
            patch.object(upload, "process_uploaded_file", return_value=(result, transactions)),
            patch.object(upload, "replace_processed_data", return_value=transactions) as replace,
            patch.object(upload, "set_active_statement_files") as set_active,
        ):
            response = await upload.upload_single_file(self._file("current.csv"))

        replace.assert_called_once()
        set_active.assert_called_once_with(["current.csv"])
        self.assertTrue(response.summary["dataset_replaced"])
        self.assertEqual(response.summary["processed_transactions"], 1)

    async def test_batch_replaces_dataset_with_all_uploaded_files_without_a_count_cap(self):
        file_count = 11
        files = [self._file(f"statement_{index}.csv") for index in range(file_count)]

        def process_file(file_path, filename, account_name):
            name = os.path.basename(file_path)
            result, transactions = self._successful_result(filename, name)
            return result, transactions

        def save_file(file, *_args):
            return os.path.join("C:\\uploads", file.filename), False

        def replace(transactions):
            self.assertEqual(len(transactions), file_count)
            return transactions

        with (
            patch.object(upload, "save_uploaded_file", side_effect=save_file),
            patch.object(upload, "process_uploaded_file", side_effect=process_file),
            patch.object(upload, "replace_processed_data", side_effect=replace) as replace_mock,
            patch.object(upload, "set_active_statement_files") as set_active,
        ):
            response = await upload.upload_batch_files(files)

        self.assertTrue(response.dataset_replaced)
        self.assertEqual(response.successful_uploads, file_count)
        self.assertEqual(response.overall_summary["processed_transactions"], file_count)
        replace_mock.assert_called_once()
        self.assertEqual(set_active.call_count, 1)
        self.assertEqual(len(set_active.call_args.args[0]), file_count)

    async def test_batch_with_a_failed_file_keeps_existing_dataset(self):
        files = [self._file("good.csv"), self._file("bad.csv")]
        good_result, good_transactions = self._successful_result(
            "good.csv",
            "Good transaction",
        )
        bad_result = upload.FileProcessingResult(
            filename="bad.csv",
            success=False,
            message="Could not parse statement",
            records_processed=0,
            file_size=9,
            errors=["Could not parse statement"],
        )

        with (
            patch.object(
                upload,
                "save_uploaded_file",
                side_effect=[
                    (os.path.join("C:\\uploads", "good.csv"), False),
                    (os.path.join("C:\\uploads", "bad.csv"), False),
                ],
            ),
            patch.object(
                upload,
                "process_uploaded_file",
                side_effect=[
                    (good_result, good_transactions),
                    (bad_result, None),
                ],
            ),
            patch.object(upload, "replace_processed_data") as replace,
            patch.object(upload, "set_active_statement_files") as set_active,
        ):
            response = await upload.upload_batch_files(files)

        self.assertFalse(response.dataset_replaced)
        self.assertEqual(response.failed_uploads, 1)
        self.assertIn("not replaced", response.overall_summary["dataset_replacement_message"])
        replace.assert_not_called()
        set_active.assert_not_called()


if __name__ == "__main__":
    unittest.main()
