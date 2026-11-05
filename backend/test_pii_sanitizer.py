"""
Regression tests for the PII sanitizer used before data is sent to LLMs.

Uses synthetic names only. Run with:
    python test_pii_sanitizer.py
or with pytest, if it is installed.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'SRC'))

from pii_sanitizer import PIISanitizer  # type: ignore  # noqa: E402


def sanitize(text: str) -> str:
    return PIISanitizer().sanitize_text(text).sanitized


def test_upi_dash_format_masks_payee_and_vpa():
    out = sanitize("UPI-TEST PERSON-test.user@example.invalid-TESTBANK-123456789012-PAYMENT FROM PHONE")
    assert 'TEST PERSON' not in out
    assert 'test.user@example.invalid' not in out
    assert '[PAYEE]' in out
    assert 't***@example.invalid' in out
    assert 'PAYMENT FROM PHONE' in out


def test_upi_slash_format_masks_names_and_vpa():
    out = sanitize("UPI/DR/123456789012/TEST PERSON/TESTBANK/test.user@example.invalid/lunch")
    assert 'TEST PERSON' not in out
    assert 'test.user' not in out
    assert 't***@example.invalid' in out


def test_neft_debit_masks_payee():
    out = sanitize("NEFT DR-HDFC0001234-TEST PERSON-REF TESTREF")
    assert 'TEST PERSON' not in out
    assert 'HDFC0001234' in out


def test_neft_credit_two_part_name_is_masked():
    out = sanitize("NEFT CR-UTIB0005098-TEST PERSON-TEST PAYEE-TESTREF")
    assert 'TEST PERSON' not in out
    assert 'TEST PAYEE' not in out


def test_imps_masks_payee():
    out = sanitize("IMPS-123456789012-TEST PERSON-TESTBANK-TESTREF")
    assert 'TEST PERSON' not in out


def test_company_payee_is_masked_by_default_deny():
    out = sanitize("NEFT CR-ICIC0000123-SAMPLE COMPANY LTD-INV TESTREF")
    assert 'SAMPLE COMPANY' not in out


def test_known_merchants_are_kept():
    assert 'SWIGGY' in sanitize("UPI-SWIGGY-merchant@example.invalid-TESTBANK-TESTREF-ORDER")
    assert 'NETFLIX COM' in sanitize("UPI-NETFLIX COM-merchant@example.invalid-TESTBANK-TESTREF")


def test_card_and_pos_descriptions_are_unchanged():
    text = "POS 4000 SWIGGY BANGALORE"
    assert sanitize(text) == text


def test_phone_number_is_masked():
    out = sanitize("PAYMENT FROM PHONE 9999999999 TEST PERSON")
    assert '9999999999' not in out
    assert 'XXXXX99999' in out


def test_long_reference_number_is_masked():
    out = sanitize("UPI/DR/123456789012/TEST PERSON/TESTBANK/test.user@example.invalid/lunch")
    assert '123456789012' not in out


def test_upi_hyphen_prefix_is_not_treated_as_vpa():
    out = sanitize("UPI-TEST PERSON-test.user@example.invalid-TESTBANK-TESTREF")
    assert 'UP***' not in out
    assert 'UPI-[PAYEE]-t***@example.invalid' in out


def test_stats_count_masked_items():
    sanitizer = PIISanitizer()
    result = sanitizer.sanitize_text(
        "UPI-TEST PERSON-test.user@example.invalid-TESTBANK-123456789012-PAYMENT FROM PHONE"
    )
    assert sanitizer.stats['personal_names'] >= 1
    assert sanitizer.stats['upi_ids'] >= 1
    assert any(item['type'] == 'personal_name' for item in result.pii_found)


if __name__ == '__main__':
    tests = [value for name, value in list(globals().items()) if name.startswith('test_') and callable(value)]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except AssertionError as error:
            failures += 1
            print(f"FAIL {test.__name__}: {error!r}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    sys.exit(1 if failures else 0)
