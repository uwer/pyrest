"""Tests for pyrest.deltat module."""

import pytest
from datetime import timedelta
from pyrest.deltat import parse_time, incrementMonth
from datetime import datetime, date


class TestParseTime:
    """Test time duration parsing."""

    def test_parse_weeks(self):
        """Test parsing weeks."""
        result = parse_time("2w")
        assert result == timedelta(weeks=2)

    def test_parse_days(self):
        """Test parsing days."""
        result = parse_time("3d")
        assert result == timedelta(days=3)

    def test_parse_hours(self):
        """Test parsing hours."""
        result = parse_time("4h")
        assert result == timedelta(hours=4)

    def test_parse_minutes(self):
        """Test parsing minutes."""
        result = parse_time("30m")
        assert result == timedelta(minutes=30)

    def test_parse_seconds(self):
        """Test parsing seconds."""
        result = parse_time("45s")
        assert result == timedelta(seconds=45)

    def test_parse_combined(self):
        """Test parsing combined time units."""
        result = parse_time("2d 3h 30m 15s")
        
        expected = timedelta(days=2, hours=3, minutes=30, seconds=15)
        assert result == expected

    def test_parse_decimal_values(self):
        """Test parsing decimal values."""
        result = parse_time("1.5h")
        
        expected = timedelta(hours=1.5)
        assert result == expected

    def test_parse_without_suffix(self):
        """Test parsing seconds without 's' suffix."""
        result = parse_time("30")
        assert result == timedelta(seconds=30)

    def test_parse_whitespace(self):
        """Test parsing with extra whitespace."""
        result = parse_time("  2h  30m  ")
        assert result == timedelta(hours=2, minutes=30)

    def test_parse_float(self):
        """Test parsing float values."""
        result = parse_time("1.5")
        assert result == timedelta(seconds=1.5)

    def test_parse_zero(self):
        """Test parsing zero values."""
        result = parse_time("0h")
        assert result == timedelta(0)

    def test_invalid_format(self):
        """Test invalid time format raises assertion error."""
        with pytest.raises(AssertionError):
            parse_time("not a time")

    def test_empty_string(self):
        """Test empty string raises assertion error."""
        with pytest.raises(AssertionError):
            parse_time("")

    def test_invalid_unit(self):
        """Test invalid unit raises assertion error."""
        with pytest.raises(AssertionError):
            parse_time("5x")


class TestIncrementMonth:
    """Test month incrementing."""

    def test_increment_single_month(self):
        """Test incrementing by single month."""
        result = incrementMonth(datetime(2023, 1, 15), 1)
        assert result.month == 2
        assert result.year == 2023

    def test_increment_multiple_months(self):
        """Test incrementing by multiple months."""
        result = incrementMonth(datetime(2023, 1, 15), 3)
        assert result.month == 4
        assert result.year == 2023

    def test_increment_year_boundary(self):
        """Test incrementing across year boundary."""
        result = incrementMonth(datetime(2023, 11, 15), 2)
        assert result.month == 1
        assert result.year == 2024

    def test_increment_negative_months(self):
        """Test decrementing months."""
        result = incrementMonth(datetime(2023, 3, 15), -1)
        assert result.month == 2
        assert result.year == 2023

    def test_increment_year_boundary_negative(self):
        """Test decrementing across year boundary."""
        result = incrementMonth(datetime(2023, 1, 15), -1)
        assert result.month == 12
        assert result.year == 2022
