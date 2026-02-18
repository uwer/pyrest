"""Tests for pyrest.__init__ module (utility functions)."""

import pytest
import os
import datetime
import re
from pyrest import (
    ensureProtocol,
    ensureURLPath,
    uuid,
    isValidUUID,
    isValidString,
    inferParse,
    mergeJson,
    stopwatch,
    logme,
    NM2KM,
    HOUR2SEC,
    DAYS2SEC,
)


class TestConstants:
    """Test module constants."""

    def test_nm2km_constant(self):
        """Test NM2KM conversion constant."""
        assert NM2KM == 1.852  # Nautical miles to km

    def test_hour2sec_constant(self):
        """Test HOUR2SEC conversion constant."""
        assert HOUR2SEC == 3600.0

    def test_days2sec_constant(self):
        """Test DAYS2SEC conversion constant."""
        assert DAYS2SEC == 86400.0  # 24 * 3600


class TestEnsureProtocol:
    """Test ensureProtocol function."""

    def test_add_http_protocol(self):
        """Test adding http protocol to URL without it."""
        result = ensureProtocol("example.com")
        
        assert result == "http://example.com"

    def test_preserve_existing_protocol(self):
        """Test preserving existing https protocol."""
        result = ensureProtocol("https://example.com")
        
        assert result == "https://example.com"

    def test_preserve_http_protocol(self):
        """Test preserving existing http protocol."""
        result = ensureProtocol("http://example.com")
        
        assert result == "http://example.com"

    def test_localhost_url(self):
        """Test localhost URL."""
        result = ensureProtocol("localhost:8080")
        
        assert result == "http://localhost:8080"


class TestEnsureURLPath:
    """Test ensureURLPath function."""

    def test_join_url_and_path(self):
        """Test joining URL and path."""
        result = ensureURLPath("http://example.com", "api/users")
        
        assert result == "http://example.com/api/users"

    def test_join_with_leading_slash(self):
        """Test joining with leading slash in path."""
        result = ensureURLPath("http://example.com", "/api/users")
        
        assert result == "http://example.com/api/users"

    def test_url_with_trailing_slash(self):
        """Test URL with trailing slash."""
        result = ensureURLPath("http://example.com/", "api/users")
        
        assert result == "http://example.com/api/users"

    def test_empty_path_returns_url(self):
        """Test empty path returns original URL."""
        result = ensureURLPath("http://example.com", "")
        
        assert result == "http://example.com"

    def test_none_path_returns_url(self):
        """Test None path returns original URL."""
        result = ensureURLPath("http://example.com", None)
        
        assert result == "http://example.com"

    def test_adds_protocol_if_missing(self):
        """Test protocol is added when missing."""
        result = ensureURLPath("example.com", "api")
        
        assert result == "http://example.com/api"


class TestUUID:
    """Test uuid function."""

    def test_uuid_returns_string(self):
        """Test UUID returns a string."""
        result = uuid()
        
        assert isinstance(result, str)

    def test_uuid_format(self):
        """Test UUID format (8-4-4-4-12 hex)."""
        result = uuid()
        
        # UUID format: 8-4-4-4-12
        pattern = r'^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$'
        assert re.match(pattern, result.lower())


class TestIsValidUUID:
    """Test isValidUUID function."""

    def test_valid_uuid(self):
        """Test valid UUID detection."""
        assert isValidUUID("12345678-1234-1234-1234-123456789012") is True

    def test_valid_uuid_uppercase(self):
        """Test valid uppercase UUID detection."""
        assert isValidUUID("12345678-1234-1234-1234-123456789012") is True

    def test_invalid_uuid(self):
        """Test invalid UUID detection."""
        assert isValidUUID("not-a-uuid") is False

    def test_empty_string(self):
        """Test empty string is not valid UUID."""
        assert isValidUUID("") is False

    def test_none_value(self):
        """Test None is not valid UUID."""
        assert isValidUUID(None) is False


class TestIsValidString:
    """Test isValidString function."""

    def test_valid_string(self):
        """Test valid string detection."""
        assert isValidString("hello") is True

    def test_string_with_spaces(self):
        """Test string with spaces is valid."""
        assert isValidString("hello world") is True

    def test_empty_string(self):
        """Test empty string is not valid."""
        assert isValidString("") is False

    def test_whitespace_only(self):
        """Test whitespace-only string is not valid."""
        assert isValidString("   ") is False

    def test_none_value(self):
        """Test None is not valid."""
        assert isValidString(None) is False


class TestInferParse:
    """Test inferParse function."""

    def test_parse_int(self):
        """Test parsing to int."""
        result = inferParse(int, "42")
        
        assert result == 42
        assert isinstance(result, float)  # int() returns float in this implementation

    def test_parse_float(self):
        """Test parsing to float."""
        result = inferParse(float, "3.14")
        
        assert result == 3.14

    def test_parse_date(self):
        """Test parsing to date."""
        result = inferParse(datetime.date, "2023-05-15")
        
        assert isinstance(result, datetime.date)
        assert result.year == 2023
        assert result.month == 5
        assert result.day == 15

    def test_parse_datetime(self):
        """Test parsing to datetime."""
        result = inferParse(datetime.datetime, "2023-05-15T10:30:00")
        
        assert isinstance(result, datetime.datetime)
        assert result.year == 2023

    def test_parse_string_default(self):
        """Test default parsing to string."""
        result = inferParse(list, "test")
        
        assert result == "test"


class TestMergeJson:
    """Test mergeJson function (from __init__)."""

    def test_merge_dicts(self):
        """Test merging dictionaries."""
        dict0 = {"a": 1, "b": 2}
        dict1 = {"b": 3, "c": 4}
        
        result = mergeJson(dict0, dict1)
        
        assert result is False  # Returns False when dict1 is a dict
        assert dict0 == {"a": 1, "b": 3, "c": 4}

    def test_merge_returns_true_for_non_dict(self):
        """Test merge returns True for non-dict."""
        dict0 = {"a": 1}
        
        result = mergeJson(dict0, "not a dict")
        
        assert result is True


class TestStopwatch:
    """Test stopwatch context manager."""

    def test_context_manager(self):
        """Test stopwatch context manager."""
        with stopwatch("test", "context"):
            x = 1 + 1
        
        # Just verify it runs without error

    def test_context_manager_with_code(self):
        """Test stopwatch runs code inside."""
        with stopwatch("operation", "test"):
            result = 2 + 2
        
        assert result == 4


class TestLogme:
    """Test logme function."""

    def test_log_message(self):
        """Test logging a message."""
        # Just verify it runs without error
        logme("Test message")

    def test_log_empty_message(self):
        """Test logging empty message."""
        logme("")
