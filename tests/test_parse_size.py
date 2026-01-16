"""Unit tests for the parse_size function."""

import pytest
from splitics import parse_size


class TestParseSizeValidInputs:
    """Tests for valid size specifications."""

    def test_parse_size_megabytes_uppercase(self):
        """1M should return 1048576 bytes (1024 * 1024)."""
        assert parse_size("1M") == 1024 * 1024

    def test_parse_size_megabytes_with_b_suffix(self):
        """1MB should return 1048576 bytes."""
        assert parse_size("1MB") == 1024 * 1024

    def test_parse_size_megabytes_with_lowercase_b(self):
        """1Mb should return 1048576 bytes."""
        assert parse_size("1Mb") == 1024 * 1024

    def test_parse_size_kilobytes_uppercase(self):
        """1K should return 1024 bytes."""
        assert parse_size("1K") == 1024

    def test_parse_size_kilobytes_lowercase(self):
        """1k should return 1024 bytes."""
        assert parse_size("1k") == 1024

    def test_parse_size_kilobytes_with_b_suffix(self):
        """1KB should return 1024 bytes."""
        assert parse_size("1KB") == 1024

    def test_parse_size_kilobytes_lowercase_with_b(self):
        """1kb should return 1024 bytes."""
        assert parse_size("1kb") == 1024

    def test_parse_size_multiple_megabytes(self):
        """5M should return 5 * 1048576 bytes."""
        assert parse_size("5M") == 5 * 1024 * 1024

    def test_parse_size_multiple_kilobytes(self):
        """500K should return 500 * 1024 bytes."""
        assert parse_size("500K") == 500 * 1024

    def test_parse_size_large_number(self):
        """100M should return 100 * 1048576 bytes."""
        assert parse_size("100M") == 100 * 1024 * 1024


class TestParseSizeInvalidInputs:
    """Tests for invalid size specifications."""

    def test_parse_size_invalid_unit_g(self):
        """Gigabytes are not supported."""
        with pytest.raises(ValueError, match="Cannot understand size specification"):
            parse_size("1G")

    def test_parse_size_invalid_format_no_unit(self):
        """Plain numbers without unit should fail."""
        with pytest.raises(ValueError, match="Cannot understand size specification"):
            parse_size("1024")

    def test_parse_size_invalid_format_text(self):
        """Random text should fail."""
        with pytest.raises(ValueError, match="Cannot understand size specification"):
            parse_size("hello")

    def test_parse_size_invalid_format_empty(self):
        """Empty string should fail."""
        with pytest.raises(ValueError, match="Cannot understand size specification"):
            parse_size("")

    def test_parse_size_invalid_format_negative(self):
        """Negative numbers should fail."""
        with pytest.raises(ValueError, match="Cannot understand size specification"):
            parse_size("-1M")

    def test_parse_size_invalid_format_decimal(self):
        """Decimal numbers should fail."""
        with pytest.raises(ValueError, match="Cannot understand size specification"):
            parse_size("1.5M")

    def test_parse_size_invalid_format_spaces(self):
        """Spaces in size spec should fail."""
        with pytest.raises(ValueError, match="Cannot understand size specification"):
            parse_size("1 M")


class TestParseSizeEdgeCases:
    """Edge case tests for parse_size."""

    def test_parse_size_zero_megabytes(self):
        """0M should return 0 bytes."""
        assert parse_size("0M") == 0

    def test_parse_size_zero_kilobytes(self):
        """0K should return 0 bytes."""
        assert parse_size("0K") == 0
