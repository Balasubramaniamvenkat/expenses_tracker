import unittest

from SRC.refined_categories import RefinedCategorizer, get_category_group


class RefinedCategoryTests(unittest.TestCase):
    def setUp(self):
        self.categorizer = RefinedCategorizer()

    def test_classifies_known_indian_pos_merchants(self):
        cases = [
            (
                'POS 406584XXXXXX2203 000000000275 BANGALORE CALIFORNIA BURRITO',
                'Food & Dining',
                'Restaurants',
            ),
            (
                'POS 406584XXXXXX2203 000000005116 BANGALORE LULU INTERNATIONAL SHO',
                'Shopping',
                'Local Shops & Vendors',
            ),
            (
                'UPI-COCHIN INTERNATIONAL-CIATOCSD2@FBL-FDRL0001522-416813418400-NA',
                'Travel',
                'Travel Booking',
            ),
            (
                'UPI-BNG004 BENGALURU PHO-Q080639422@YBL-YESB0YBLUPI-843085443435-PAYMENT FROM PHONE',
                'Food & Dining',
                'Restaurants',
            ),
        ]

        for description, expected_category, expected_subcategory in cases:
            with self.subTest(description=description):
                result = self.categorizer.categorize(description, -100.0)
                self.assertEqual(result['category'], expected_category)
                self.assertEqual(result['subcategory'], expected_subcategory)

    def test_separates_travel_telecom_and_utilities(self):
        cases = [
            (
                'UPI/P2M/641417589512/IRCTC ETICKETING/IRCTC/NSDL PAYMENTS BANK',
                'Travel',
                'Rail & Train',
            ),
            (
                'UPI-IRCTC WEB UPI-PAYTM-651536@PAYTM-YESB0PTMUPI-456133-OID100005',
                'Travel',
                'Rail & Train',
            ),
            ('HOTEL RESERVATION PAYMENT', 'Travel', 'Hotels & Accommodation'),
            ('HOTEL SARAVANA BHAVAN', 'Food & Dining', 'Restaurants'),
            (
                'UPI-AIRTEL MOBILE BILL-PAYBIL3066@PTYBL-YESB0PTMUPI-185593',
                'Telecom',
                'Mobile & Phone',
            ),
            ('AIRTEL XSTREAM BROADBAND BILL', 'Telecom', 'Internet & Broadband'),
            ('BESCOM ELECTRICITY BILL', 'Utilities', 'Electricity'),
            (
                '50221702267754375181/PAYTMIRCTCECATERING',
                'Food & Dining',
                'Food Delivery',
            ),
            (
                'UPI-BUNDL TECHNOLOGIES P-BUNDLTECHNOLOGIESPVTLTDSWIGGYINSTAMART.RZP@AXISBANK-UTIB0000100-422418',
                'Food & Dining',
                'Groceries',
            ),
            (
                'UPI-BUNDL TECHNOLOGIES P-BUNDLTECHNOLOGIESPVTLTDSWIGGY.RZP@SBI-SBIN0016209-424446',
                'Food & Dining',
                'Food Delivery',
            ),
            (
                'UPI-CORNER HOUSE ICE CRE-CORNERHOUSEICECREAMS.42287574@HDFCBANK-HDFC0000001-425117',
                'Food & Dining',
                'Restaurants',
            ),
            (
                'UPI-MAKE MY TRIP INDIA P-MAKEMYTRIP@HDFCBANK-HDFC0000499-413164',
                'Travel',
                'Travel Booking',
            ),
            ('PQFBFAPKBUD2CM/RAZPBSEINDIACOM', 'Investments', 'Stocks & Trading'),
            ('113265520669/CCAALLENACIN', 'Education', 'Coaching & Tuition'),
            (
                'UPI-HMSHOST SERVICES IND-PAYPHI.HMSHOST@ICICI-ICIC0DC0099-508762',
                'Food & Dining',
                'Restaurants',
            ),
            (
                'UPI-THE NEW INDIA ASSURA-THENEWINDIAASSURANCE34.RZP@MAIRTEL-AIRP0000001-416086',
                'Insurance',
                'General Insurance',
            ),
            (
                '51002705083843845121/PAYTMLICINDIA',
                'Insurance',
                'Life Insurance',
            ),
            ('K4UXI4UOBN72HP6RCY/PAYUCOMEDCOLGKARNATA', 'Education', 'College & University'),
        ]

        for description, expected_category, expected_subcategory in cases:
            with self.subTest(description=description):
                result = self.categorizer.categorize(description, -100.0)
                self.assertEqual(result['category'], expected_category)
                self.assertEqual(result['subcategory'], expected_subcategory)

    def test_upi_classification_uses_payee_not_payment_bank(self):
        cases = [
            (
                'UPI/P2M/645776677014/Innovative Retail Con/UPIInt/AIRTEL PAYMENTS BANK',
                'Food & Dining',
                'Groceries',
            ),
            (
                'UPI/P2M/645339091669/BBNOW/Pay/HDFC BANK LTD',
                'Food & Dining',
                'Groceries',
            ),
            (
                'UPI-BIGBASKET-BIGBASKET1@PAYTM-YESB0PTMUPI-501959720729-PAY',
                'Food & Dining',
                'Groceries',
            ),
        ]

        for description, expected_category, expected_subcategory in cases:
            with self.subTest(description=description):
                result = self.categorizer.categorize(description, -100.0)
                self.assertEqual(result['category'], expected_category)
                self.assertEqual(result['subcategory'], expected_subcategory)

    def test_new_categories_are_everyday_expenses(self):
        self.assertEqual(get_category_group('Travel'), 'Expense')
        self.assertEqual(get_category_group('Telecom'), 'Expense')

    def test_classifies_upi_name_with_initial_as_personal_transfer(self):
        result = self.categorizer.categorize(
            'UPI-ARIF ALI P-ARIFALI7184632@IBL-KARB0000190-983252649024-PAYMENT FROM PHONE',
            -1045.0,
        )

        self.assertEqual(result['category'], 'Individual Transfers')
        self.assertEqual(result['subcategory'], 'Personal Payment')

    def test_keeps_personal_credit_transfers_out_of_income(self):
        cases = [
            (
                'IMPS-606348727989-SRAMALAKSHMI-UTIB-XXXXXX1444-INVESTMENT',
                300000.0,
                'IMPS Transfer',
            ),
            (
                'NEFT CR-CITI0000003-S RAMALAKSHMI-BALASUBRAMANIAM V-CITIN24401114659',
                500000.0,
                'NEFT Transfer',
            ),
            (
                'UPI-V NETHRAMBAL A KANNA-9886158576-2@YBL-IOBA0000898-419652231457-PAYMENT FROM PHONE',
                100000.0,
                'Personal Payment',
            ),
        ]

        for description, amount, expected_subcategory in cases:
            with self.subTest(description=description):
                result = self.categorizer.categorize(description, amount)
                self.assertEqual(result['category'], 'Individual Transfers')
                self.assertEqual(result['subcategory'], expected_subcategory)

    def test_classifies_investment_payout_as_investment_returns_not_salary(self):
        result = self.categorizer.categorize(
            'NEFT CR-YESB0000001-ZERODHA BROKING LTD-DSCNB A/C-BALASUBRAMANIAM VENKATANARAYANAN-YESB41242414643',
            212000.0,
        )

        self.assertEqual(result['category'], 'Income')
        self.assertEqual(result['subcategory'], 'Investment Returns')
        self.assertNotEqual(result['subcategory'], 'Salary')

    def test_keeps_explicit_refunds_as_income(self):
        result = self.categorizer.categorize(
            'UPI/P2A/601133819457/AUTOPE PA/YESB/Refund f/',
            1508.60,
        )

        self.assertEqual(result['category'], 'Income')
        self.assertEqual(result['subcategory'], 'Refunds')

    def test_keeps_ambiguous_standing_instructions_out_of_daily_expenses(self):
        result = self.categorizer.categorize(
            'SI HGAMP02D4A0338232824 BANGALO-30/09/26',
            -2921.0,
        )

        self.assertEqual(result['category'], 'Recurring Commitments')
        self.assertEqual(result['subcategory'], 'Standing Instruction (EMI/SIP)')
        self.assertEqual(get_category_group(result['category']), 'Planned')

    def test_payu_bank_bill_payment_is_credit_card_payment(self):
        result = self.categorizer.categorize(
            'K4UHY5MLAN72HO6QD4/PAYUICICIBANK',
            -500000.0,
        )

        self.assertEqual(result['category'], 'Loans & EMI')
        self.assertEqual(result['subcategory'], 'Credit Card Payment')

    def test_payu_non_bank_reference_is_not_treated_as_bank_bill(self):
        result = self.categorizer.categorize(
            'K4RX25UIAB62POGXCE/PAYUIRCTC',
            -1622.2,
        )

        self.assertNotEqual(result['subcategory'], 'Credit Card Payment')

    def test_eaw_prefix_is_atm_withdrawal(self):
        result = self.categorizer.categorize(
            'EAW-416021XXXXXX0788-DBL12076-KASAVANAHALL',
            -2000.0,
        )

        self.assertEqual(result['category'], 'Cash & ATM')

    def test_pes_and_dsu_are_education(self):
        for description in (
            'UPI-PES-PES.PAYU@AXISBANK-UTIB0000000-534069325152-UPIINTENT',
            'UPI-DSU-DSU.ESBZ@HDFCBANK-HDFC0MERUPI-510536649044-PAY',
        ):
            result = self.categorizer.categorize(description, -1000.0)
            self.assertEqual(result['category'], 'Education')
            self.assertEqual(result['subcategory'], 'College & University')

    def test_upi_autopay_uses_real_merchant_not_taxi(self):
        result = self.categorizer.categorize(
            'UPI-AUTOPAY-AIRTEL MOBILE BILL-PAYBIL3066@PTYBL-YESB0PTMUPI-185593682227-OID27756897916@ONE',
            -399.0,
        )

        self.assertEqual(result['category'], 'Telecom')

    def test_gateway_and_numeric_upi_payees_are_not_other(self):
        for description in (
            'UPI-PAYU-PAYUPAYMENTS@AXL-UTIB0AXLUPI-783157324316-PAYMENT FOR 271914',
            'UPI-4PS  4-PAYTM-82127554@PTYS-YESB0PTMUPI-987676608085-PAYMENT FROM PHONE',
        ):
            result = self.categorizer.categorize(description, -1000.0)
            self.assertNotEqual(result['category'], 'Other')

    def test_broker_payout_is_income_investment_returns(self):
        result = self.categorizer.categorize(
            'NEFT CR-YESB0000001-ZERODHA BROKING LTD-DSCNB A/C-SOME HOLDER-YESBN12025070506721416',
            5057.77,
        )

        self.assertEqual(result['category'], 'Income')
        self.assertEqual(result['subcategory'], 'Investment Returns')
        self.assertEqual(get_category_group(result['category']), 'Income')

    def test_broker_debit_is_still_an_investment(self):
        result = self.categorizer.categorize('0500151856578642/ZERODHA', -100.0)

        self.assertEqual(result['category'], 'Investments')
        self.assertEqual(result['subcategory'], 'Stocks & Trading')

    def test_ach_credit_from_company_is_dividend(self):
        for description in (
            'ACH C- KRITI NUTRIENTS LTD-0000000000000',
            'ACH C- COLGATPALMOLIVINDLTD-269875',
        ):
            result = self.categorizer.categorize(description, 2352.0)
            self.assertEqual(result['category'], 'Income')
            self.assertEqual(result['subcategory'], 'Dividends')

    def test_reversal_and_merchant_credits_are_refunds(self):
        for description in (
            'REV-UPI-00771050024065-9886158576@PTAXIS-522107679973-SENT USING PAYTM UPI',
            'UPI-PAYTM BILL-PAYBIL3066@PTYBL-YESB0PTMUPI-513404094670-EXPRESS',
        ):
            result = self.categorizer.categorize(description, 501.0)
            self.assertEqual(result['category'], 'Income')
            self.assertEqual(result['subcategory'], 'Refunds')

    def test_salary_credit_stays_salary(self):
        result = self.categorizer.categorize(
            'NEFT CR-ICIC0099999-XFORMICS TECHNOLOGIES INDIA PVT LTD-SOME HOLDER-IN22536512603387',
            172292.0,
        )

        self.assertEqual(result['subcategory'], 'Salary')

    def test_family_transfer_received_is_not_income(self):
        result = self.categorizer.categorize(
            'IMPS-533923441244-SRAMALAKSHMI-UTIB-XXXXXX1444-RAJI',
            65000.0,
        )

        self.assertEqual(result['category'], 'Individual Transfers')


if __name__ == '__main__':
    unittest.main()
