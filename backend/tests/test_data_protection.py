"""Data Protection service unit tests.

Covers PII/sensitive-data scanning (``scan_for_sensitive_data``), redaction
before logging and AI processing (``validate_for_logging`` /
``validate_for_ai``), field masking (``mask_email`` / ``mask_phone``), and
Fernet encryption round-trips (``encrypt`` / ``decrypt``).
"""
import pytest

from app.services.data_protection import DataProtectionService, SENSITIVE_PATTERNS


@pytest.fixture
def svc():
    return DataProtectionService()


# ═══════════════════════════════════════════════════════════════════════════
# SENSITIVE DATA SCANNING
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
def test_scan_clean_text_no_sensitive_data(svc):
    result = svc.scan_for_sensitive_data("The quarterly report is ready for review.")
    assert result.has_sensitive_data is False
    assert result.patterns_found == {}
    assert result.redacted_text == "The quarterly report is ready for review."


@pytest.mark.unit
def test_scan_empty_document(svc):
    result = svc.scan_for_sensitive_data("")
    assert result.has_sensitive_data is False
    assert result.redacted_text == ""


@pytest.mark.unit
def test_scan_detects_pii_and_redacts(svc):
    # NB: the phone pattern requires 10 consecutive digits.
    text = "Contact alice@example.com or call 5551234567 today."
    result = svc.scan_for_sensitive_data(text)
    assert result.has_sensitive_data is True
    assert result.patterns_found["email"] == 1
    assert result.patterns_found["phone"] == 1
    assert "[REDACTED_EMAIL]" in result.redacted_text
    assert "[REDACTED_PHONE]" in result.redacted_text
    assert "alice@example.com" not in result.redacted_text


@pytest.mark.unit
def test_scan_mixed_content_multiple_hits(svc):
    text = (
        "SSN 123-45-6789 and credit card 4111 1111 1111 1111 "
        "from a@b.com and b@c.com"
    )
    result = svc.scan_for_sensitive_data(text)
    assert result.patterns_found["ssn"] == 1
    assert result.patterns_found["credit_card"] == 1
    assert result.patterns_found["email"] == 2


@pytest.mark.unit
def test_scan_secrets_and_keys(svc):
    text = (
        "api key sk-" + "a" * 40 + " "
        "aws AKIAIOSFODNN7EXAMPLE slack xoxb-abc-def-ghi "
        "jwt eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.abc.def"
    )
    result = svc.scan_for_sensitive_data(text)
    assert result.has_sensitive_data is True
    assert "api_key" in result.patterns_found
    assert "aws_key" in result.patterns_found
    assert "slack_token" in result.patterns_found
    assert "sk-" not in result.redacted_text


@pytest.mark.unit
def test_scan_private_key_and_stripe(svc):
    text = "-----BEGIN RSA PRIVATE KEY----- data -----END RSA PRIVATE KEY----- sk_live_abcdefgh"
    result = svc.scan_for_sensitive_data(text)
    assert "private_key" in result.patterns_found
    assert "stripe_key" in result.patterns_found
    assert "[REDACTED_PRIVATE_KEY]" in result.redacted_text
    assert "[REDACTED_STRIPE_KEY]" in result.redacted_text


@pytest.mark.unit
def test_scan_unknown_data_types_not_flagged(svc):
    result = svc.scan_for_sensitive_data("Order #12345 totals $1,234.56 processed at 12:30 UTC")
    assert result.has_sensitive_data is False


@pytest.mark.unit
def test_pattern_suite_covers_expected_categories():
    assert set(SENSITIVE_PATTERNS) >= {
        "email", "phone", "ssn", "credit_card", "ip_address", "api_key",
        "aws_key", "slack_token", "private_key", "jwt", "stripe_key",
    }


# ═══════════════════════════════════════════════════════════════════════════
# LOGGING / AI VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
async def test_validate_for_logging_redacts_sensitive(svc):
    redacted = await svc.validate_for_logging("User email is bob@corp.com")
    assert redacted == "User email is [REDACTED_EMAIL]"


@pytest.mark.unit
async def test_validate_for_logging_clean_unchanged(svc):
    redacted = await svc.validate_for_logging("Request completed in 120ms")
    assert redacted == "Request completed in 120ms"


@pytest.mark.unit
async def test_validate_for_ai_returns_warnings(svc):
    redacted, warnings = await svc.validate_for_ai(
        "user carol@example.com called 2025550100"
    )
    assert "carol@example.com" not in redacted
    assert any("email" in w for w in warnings)
    assert any("phone" in w for w in warnings)


@pytest.mark.unit
async def test_validate_for_ai_clean_no_warnings(svc):
    redacted, warnings = await svc.validate_for_ai("Nothing personal here.")
    assert redacted == "Nothing personal here."
    assert warnings == []


# ═══════════════════════════════════════════════════════════════════════════
# MASKING
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
def test_mask_email_typical(svc):
    assert svc.mask_email("john.doe@example.com") == "j****e@example.com"


@pytest.mark.unit
def test_mask_email_short_local_part_unchanged(svc):
    assert svc.mask_email("a@b.com") == "a@b.com"


@pytest.mark.unit
def test_mask_phone_typical(svc):
    assert svc.mask_phone("+1 (555) 123-4567") == "15****4567"


@pytest.mark.unit
def test_mask_phone_too_short_unchanged(svc):
    assert svc.mask_phone("12345") == "12345"


# ═══════════════════════════════════════════════════════════════════════════
# ENCRYPTION
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.unit
def test_encrypt_decrypt_roundtrip(svc):
    ciphertext = svc.encrypt("secret-value-42")
    assert ciphertext != "secret-value-42"
    assert svc.decrypt(ciphertext) == "secret-value-42"


@pytest.mark.unit
def test_encrypt_is_unique_per_call(svc):
    a = svc.encrypt("same")
    b = svc.encrypt("same")
    assert a != b
    assert svc.decrypt(a) == svc.decrypt(b) == "same"


@pytest.mark.unit
def test_decrypt_tampered_ciphertext_raises(svc):
    ciphertext = svc.encrypt("payload")
    tampered = ("A" + ciphertext[1:]) if not ciphertext.startswith("A") else ("B" + ciphertext[1:])
    with pytest.raises(Exception):
        svc.decrypt(tampered)
