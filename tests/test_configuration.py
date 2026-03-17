"""Tests for pyrest.configuration module."""

import pytest
from pyrest.configuration import Configuration


class TestConfiguration:
    """Test Configuration class."""

    def test_default_values(self):
        """Test configuration has correct default values."""
        config = Configuration()
        
        assert config.host == "https://<host>/api"
        assert config.verify_ssl is True
        assert config.debug is False
        assert config.connection_pool_maxsize is not None
        assert config.proxy is None

    def test_api_key_settings(self):
        """Test API key configuration."""
        config = Configuration()
        
        # Test setting API key
        config.api_key = {"api_key": "test_key_123"}
        assert config.api_key["api_key"] == "test_key_123"
        
        # Test API key prefix
        config.api_key_prefix = {"api_key": "Bearer"}
        assert config.api_key_prefix["api_key"] == "Bearer"

    def test_get_api_key_with_prefix(self):
        """Test getting API key with prefix."""
        config = Configuration()
        config.api_key = {"my_api": "secret123"}
        config.api_key_prefix = {"my_api": "Bearer"}
        
        result = config.get_api_key_with_prefix("my_api")
        assert result == "Bearer secret123"

    def test_get_api_key_without_prefix(self):
        """Test getting API key without prefix."""
        config = Configuration()
        config.api_key = {"my_api": "secret123"}
        
        result = config.get_api_key_with_prefix("my_api")
        assert result == "secret123"

    def test_get_api_key_missing(self):
        """Test getting non-existent API key."""
        config = Configuration()
        
        result = config.get_api_key_with_prefix("nonexistent")
        assert result is None

    def test_basic_auth_token(self):
        """Test basic auth token generation."""
        config = Configuration()
        
        # No credentials
        token = config.get_basic_auth_token()
        assert token == ""
        
        # With credentials
        config.username = "admin"
        config.password = "secret"
        token = config.get_basic_auth_token()
        assert token.startswith("Basic ")

    def test_timeout_setting(self):
        """Test timeout configuration."""
        config = Configuration()
        config.setTimeout(5, 30)
        
        assert config.timeout is not None
        assert config.timeout.connect_timeout == 5
        assert config.timeout.read_timeout == 30

    def test_ssl_settings(self):
        """Test SSL configuration."""
        config = Configuration()
        
        # Default verify_ssl is True
        assert config.verify_ssl is True
        
        # Disable SSL verification
        config.verify_ssl = False
        assert config.verify_ssl is False
        
        # Custom CA cert
        config.ssl_ca_cert = "/path/to/ca.crt"
        assert config.ssl_ca_cert == "/path/to/ca.crt"
        
        # Client certificates
        config.cert_file = "/path/to/client.crt"
        config.key_file = "/path/to/client.key"
        assert config.cert_file == "/path/to/client.crt"
        assert config.key_file == "/path/to/client.key"

    def test_auth_settings(self):
        """Test auth settings method."""
        config = Configuration()
        
        settings = config.auth_settings()
        assert isinstance(settings, dict)

    def test_debug_property(self):
        """Test debug property setter/getter."""
        config = Configuration()
        
        # Default is False
        assert config.debug is False
        
        # Set to True
        config.debug = True
        assert config.debug is True
        
        # Set back to False
        config.debug = False
        assert config.debug is False

    def test_logger_settings(self):
        """Test logger configuration."""
        config = Configuration()
        
        # Logger should be initialized
        assert "package_logger" in config.logger
        assert "urllib3_logger" in config.logger
        
        # Logger format should have default
        assert config.logger_format is not None
        assert "%(asctime)s" in config.logger_format

    def test_safe_chars_default(self):
        """Test safe chars for path params default."""
        config = Configuration()
        
        assert config.safe_chars_for_path_param == ''

    def test_to_debug_report(self):
        """Test debug report generation."""
        config = Configuration()
        
        report = config.to_debug_report()
        assert "Python SDK Debug Report" in report
        assert "OS:" in report
        assert "Python Version:" in report
