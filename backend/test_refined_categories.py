import unittest

from SRC.refined_categories import RefinedCategorizer, get_category_group


class RefinedCategoryTests(unittest.TestCase):
    def setUp(self):
        self.categorizer = RefinedCategorizer()

    def test_classifies_known_indian_pos_merchants(self):
        cases = [
            (
                'POS CARD-XXXX TEST-REF BANGALORE CALIFORNIA BURRITO',
                'Food & Dining',
                'Restaurants',
            ),
            (
                'POS CARD-XXXX TEST-REF BANGALORE LULU INTERNATIONAL SHO',
                'Shopping',
                'Local Shops & Vendors',
            ),
            (
                'UPI-COCHIN INTERNATIONAL-TEST@SAMPLE.INVALID-TESTBANK-TESTREF-NA',
                'Travel',
                'Travel Booking',
            ),
            (
                'UPI-BNG004 BENGALURU PHO-TEST@SAMPLE.INVALID-TESTBANK-TESTREF-PAYMENT FROM PHONE',
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
                'UPI/P2M/TESTREF/IRCTC ETICKETING/IRCTC/TEST BANK',
                'Travel',
                'Rail & Train',
            ),
            (
                'UPI-IRCTC WEB UPI-PAYTM-TEST@SAMPLE.INVALID-TESTBANK-TESTREF',
                'Travel',
                'Rail & Train',
            ),
            ('HOTEL RESERVATION PAYMENT', 'Travel', 'Hotels & Accommodation'),
            ('HOTEL SARAVANA BHAVAN', 'Food & Dining', 'Restaurants'),
            (
                'UPI-AIRTEL MOBILE BILL-BILL@SAMPLE.INVALID-TESTBANK-TESTREF',
                'Telecom',
                'Mobile & Phone',
            ),
            ('AIRTEL XSTREAM BROADBAND BILL', 'Telecom', 'Internet & Broadband'),
            ('BESCOM ELECTRICITY BILL', 'Utilities', 'Electricity'),
            (
                'TESTREF/PAYTMIRCTCECATERING',
                'Food & Dining',
                'Food Delivery',
            ),
            (
                'UPI-BUNDL TECHNOLOGIES P-SWIGGYINSTAMART@SAMPLE.INVALID-TESTBANK-TESTREF',
                'Food & Dining',
                'Groceries',
            ),
            (
                'UPI-BUNDL TECHNOLOGIES P-SWIGGY@SAMPLE.INVALID-TESTBANK-TESTREF',
                'Food & Dining',
                'Food Delivery',
            ),
            (
                'UPI-CORNER HOUSE ICE CRE-MERCHANT@SAMPLE.INVALID-TESTBANK-TESTREF',
                'Food & Dining',
                'Restaurants',
            ),
            (
                'UPI-MAKE MY TRIP INDIA P-MERCHANT@SAMPLE.INVALID-TESTBANK-TESTREF',
                'Travel',
                'Travel Booking',
            ),
            ('PQFBFAPKBUD2CM/RAZPBSEINDIACOM', 'Investments', 'Stocks & Trading'),
            ('TESTREF/CCAALLENACIN', 'Education', 'Coaching & Tuition'),
            (
                'UPI-HMSHOST SERVICES IND-MERCHANT@SAMPLE.INVALID-TESTBANK-TESTREF',
                'Food & Dining',
                'Restaurants',
            ),
            (
                'UPI-THE NEW INDIA ASSURA-MERCHANT@SAMPLE.INVALID-TESTBANK-TESTREF',
                'Insurance',
                'General Insurance',
            ),
            (
                'TESTREF/PAYTMLICINDIA',
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
                'UPI/P2M/TESTREF/Innovative Retail Con/UPIInt/TEST BANK',
                'Food & Dining',
                'Groceries',
            ),
            (
                'UPI/P2M/TESTREF/BBNOW/Pay/TEST BANK',
                'Food & Dining',
                'Groceries',
            ),
            (
                'UPI-BIGBASKET-MERCHANT@SAMPLE.INVALID-TESTBANK-TESTREF-PAY',
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
            'UPI-TEST PERSON-test.person@sample.invalid-TESTBANK-TESTREF-PAYMENT FROM PHONE',
            -1045.0,
        )

        self.assertEqual(result['category'], 'Individual Transfers')
        self.assertEqual(result['subcategory'], 'Personal Payment')

    def test_keeps_personal_credit_transfers_out_of_income(self):
        cases = [
            (
                'IMPS-TESTREF-TEST PERSON-TESTBANK-XXXX-INVESTMENT',
                300000.0,
                'IMPS Transfer',
            ),
            (
                'NEFT CR-TESTBANK-TEST PERSON-TEST PAYEE-TESTREF',
                500000.0,
                'NEFT Transfer',
            ),
            (
                'UPI-TEST PERSON-test.person@sample.invalid-TESTBANK-TESTREF-PAYMENT FROM PHONE',
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
            'NEFT CR-TESTBANK-ZERODHA BROKING LTD-INVESTMENT PAYOUT-TESTREF',
            212000.0,
        )

        self.assertEqual(result['category'], 'Income')
        self.assertEqual(result['subcategory'], 'Investment Returns')
        self.assertNotEqual(result['subcategory'], 'Salary')

    def test_keeps_explicit_refunds_as_income(self):
        result = self.categorizer.categorize(
            'UPI/P2A/TESTREF/AUTOPE PA/TESTBANK/Refund',
            1508.60,
        )

        self.assertEqual(result['category'], 'Income')
        self.assertEqual(result['subcategory'], 'Refunds')

    def test_keeps_ambiguous_standing_instructions_out_of_daily_expenses(self):
        result = self.categorizer.categorize(
            'SI TEST-REFERENCE BANGALORE',
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
            'EAW-CARD-XXXX-TESTBANK-TESTLOCATION',
            -2000.0,
        )

        self.assertEqual(result['category'], 'Cash & ATM')

    def test_pes_and_dsu_are_education(self):
        for description in (
            'UPI-PES-MERCHANT@SAMPLE.INVALID-TESTBANK-TESTREF-UPIINTENT',
            'UPI-DSU-MERCHANT@SAMPLE.INVALID-TESTBANK-TESTREF-PAY',
            'UPI/P2M/TESTREF/DSU/Pay/TEST BANK',
        ):
            result = self.categorizer.categorize(description, -1000.0)
            self.assertEqual(result['category'], 'Education')
            self.assertEqual(result['subcategory'], 'College & University')
            self.assertEqual(get_category_group(result['category']), 'Investment')

    def test_amrita_university_names_and_payment_aliases_are_education(self):
        descriptions = (
            'UPI/P2M/TESTREF/AMRITA VISHWA VIDYAPE/UPI/TEST BANK',
            'UPI-AMRITA VISHWA VIDYAP-TEST@SAMPLE.INVALID-TESTBANK-TESTREF-UNIVERSITY FEE',
            'UPI-AOAP AMRITA-MERCHANT@SAMPLE.INVALID-TESTBANK-TESTREF-UPIINTENT',
            'UPI-AMRITHA VISHWA VIDYAPEETHAM',
            'AVV university admission payment',
            'Dayananda Sagar University admission payment',
        )

        for description in descriptions:
            with self.subTest(description=description):
                result = self.categorizer.categorize(description, -1000.0)
                self.assertEqual(result['category'], 'Education')
                self.assertEqual(result['subcategory'], 'College & University')
                self.assertEqual(get_category_group(result['category']), 'Investment')

    def test_education_tuition_and_entrance_exam_payments_are_investments(self):
        cases = [
            (
                'UPI/P2M/TESTREF/MATHSGYM/TEST PAYEE/TEST BANK',
                'Coaching & Tuition',
            ),
            ('IIT JEE application fee', 'Entrance Exams & Applications'),
            ('KCET entrance exam fee', 'Entrance Exams & Applications'),
            ('VITEEE application fee', 'Entrance Exams & Applications'),
            ('PESSAT entrance test fee', 'Entrance Exams & Applications'),
            ('MATHS tuition', 'Coaching & Tuition'),
            ('PHYSICS coaching', 'Coaching & Tuition'),
            ('CHEMISTRY classes', 'Coaching & Tuition'),
        ]

        for description, expected_subcategory in cases:
            with self.subTest(description=description):
                result = self.categorizer.categorize(description, -1000.0)
                self.assertEqual(result['category'], 'Education')
                self.assertEqual(result['subcategory'], expected_subcategory)
                self.assertEqual(get_category_group(result['category']), 'Investment')

    def test_upi_autopay_uses_real_merchant_not_taxi(self):
        result = self.categorizer.categorize(
            'UPI-AUTOPAY-AIRTEL MOBILE BILL-BILL@SAMPLE.INVALID-TESTBANK-TESTREF',
            -399.0,
        )

        self.assertEqual(result['category'], 'Telecom')

    def test_gateway_and_numeric_upi_payees_are_not_other(self):
        for description in (
            'UPI-PAYU-MERCHANT@SAMPLE.INVALID-TESTBANK-TESTREF-PAYMENT',
            'UPI-TEST PAYTM-TEST@SAMPLE.INVALID-TESTBANK-TESTREF-PAYMENT FROM PHONE',
        ):
            result = self.categorizer.categorize(description, -1000.0)
            self.assertNotEqual(result['category'], 'Other')

    def test_broker_payout_is_income_investment_returns(self):
        result = self.categorizer.categorize(
            'NEFT CR-TESTBANK-ZERODHA BROKING LTD-INVESTMENT PAYOUT-TESTREF',
            5057.77,
        )

        self.assertEqual(result['category'], 'Income')
        self.assertEqual(result['subcategory'], 'Investment Returns')
        self.assertEqual(get_category_group(result['category']), 'Income')

    def test_broker_debit_is_still_an_investment(self):
        result = self.categorizer.categorize('TESTREF/ZERODHA', -100.0)

        self.assertEqual(result['category'], 'Investments')
        self.assertEqual(result['subcategory'], 'Stocks & Trading')

    def test_ach_credit_from_company_is_dividend(self):
        for description in (
            'ACH C- SAMPLE COMPANY LTD-TESTREF',
            'ACH C- TEST COMPANY LTD-TESTREF',
        ):
            result = self.categorizer.categorize(description, 2352.0)
            self.assertEqual(result['category'], 'Income')
            self.assertEqual(result['subcategory'], 'Dividends')

    def test_reversal_and_merchant_credits_are_refunds(self):
        for description in (
            'REV-UPI-TESTREF-test@sample.invalid-TESTBANK-TESTREF-SENT USING PAYTM UPI',
            'UPI-PAYTM BILL-BILL@SAMPLE.INVALID-TESTBANK-TESTREF-EXPRESS',
        ):
            result = self.categorizer.categorize(description, 501.0)
            self.assertEqual(result['category'], 'Income')
            self.assertEqual(result['subcategory'], 'Refunds')

    def test_salary_credit_stays_salary(self):
        result = self.categorizer.categorize(
            'NEFT CR-TESTBANK-SAMPLE TECHNOLOGIES LTD-TEST PAYEE-TESTREF',
            172292.0,
        )

        self.assertEqual(result['subcategory'], 'Salary')

    def test_family_transfer_received_is_not_income(self):
        result = self.categorizer.categorize(
            'IMPS-TESTREF-TEST PERSON-TESTBANK-XXXX-TEST',
            65000.0,
        )

        self.assertEqual(result['category'], 'Individual Transfers')


if __name__ == '__main__':
    unittest.main()
