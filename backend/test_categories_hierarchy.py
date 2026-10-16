import unittest

from api.categories_hierarchy import extract_merchant_name


class CategoryHierarchyMerchantTests(unittest.TestCase):
    def test_uses_upi_payee_instead_of_bank_or_payment_provider(self):
        cases = [
            (
                'UPI/P2M/645339091669/BBNOW/Pay/HDFC BANK LTD',
                'BigBasket',
            ),
            (
                'UPI/P2M/645776677014/Innovative Retail Con/UPIInt/AIRTEL PAYMENTS BANK',
                'BigBasket',
            ),
            (
                'UPI-BIGBASKET-BIGBASKET1@PAYTM-YESB0PTMUPI-501959720729-PAY',
                'BigBasket',
            ),
            (
                'UPI/P2M/123456789/AIRTEL MOBILE BILL/RECHARGE/HDFC BANK',
                'Airtel',
            ),
            (
                'UPI-BUNDL TECHNOLOGIES P-BUNDLTECHNOLOGIESPVTLTDSWIGGYINSTAMART.RZP@AXISBANK-UTIB0000100-422418',
                'Swiggy Instamart',
            ),
            (
                'UPI-BUNDL TECHNOLOGIES P-BUNDLTECHNOLOGIESPVTLTDSWIGGY.RZP@SBI-SBIN0016209-424446',
                'Swiggy',
            ),
        ]

        for description, expected_merchant in cases:
            with self.subTest(description=description):
                self.assertEqual(extract_merchant_name(description), expected_merchant)

    def test_does_not_guess_a_bank_as_an_unparsed_upi_merchant(self):
        self.assertEqual(extract_merchant_name('UPI/UNKNOWN FORMAT/HDFC BANK'), 'UPI merchant')


if __name__ == '__main__':
    unittest.main()
