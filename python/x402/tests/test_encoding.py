import pytest
from x402.encoding import safe_base64_encode, safe_base64_decode


def test_safe_base64_encode():
    # Test basic string encoding
    assert safe_base64_encode("hello") == "aGVsbG8"

    # Test empty string
    assert safe_base64_encode("") == ""

    # Test string with special characters
    assert safe_base64_encode("hello!@#$%^&*()") == "aGVsbG8hQCMkJV4mKigp"

    # Test string with unicode characters
    assert safe_base64_encode("hello 世界") == "aGVsbG8g5LiW55WM"


def test_safe_base64_decode():
    # Test basic string decoding
    assert safe_base64_decode("aGVsbG8") == "hello"

    # Test empty string
    assert safe_base64_decode("") == ""

    # Test string with special characters
    assert safe_base64_decode("aGVsbG8hQCMkJV4mKigp") == "hello!@#$%^&*()"

    # Test string with unicode characters
    assert safe_base64_decode("aGVsbG8g5LiW55WM") == "hello 世界"


def test_encode_decode_roundtrip():
    test_strings = [
        "hello",
        "",
        "hello!@#$%^&*()",
        "hello 世界",
        "test123",
        "!@#$%^&*()_+",
        "Hello, World!",
    ]

    for test_str in test_strings:
        encoded = safe_base64_encode(test_str)
        decoded = safe_base64_decode(encoded)
        assert decoded == test_str, f"Roundtrip failed for string: {test_str}"
