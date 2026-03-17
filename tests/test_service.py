"""Tests for pyrest.service module."""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pyrest.service import (
    EchoHandler,
    APIDelegate,
    _class,
    _instanceFromConfig,
)


class TestEchoHandler:
    """Test EchoHandler class."""

    def test_init(self):
        """Test EchoHandler initialization."""
        handler = EchoHandler({})
        
        assert handler is not None

    def test_call_with_body(self):
        """Test handler with body."""
        handler = EchoHandler({})
        
        result = handler("process", body=b'{"test": "data"}')
        
        assert result["key"] == "process"
        assert result["body"] == '{"test": "data"}'

    def test_call_with_query(self):
        """Test handler with query params."""
        handler = EchoHandler({})
        
        result = handler("process", query={"page": "1", "limit": "10"})
        
        assert result["key"] == "process"
        assert result["query"]["page"] == "1"
        assert result["query"]["limit"] == "10"

    def test_call_with_wait_param(self):
        """Test handler with wait parameter."""
        handler = EchoHandler({})
        
        # Very short wait
        import time
        start = time.time()
        result = handler("process", query={"wait": "0.001"})
        elapsed = time.time() - start
        
        # Should have waited approximately 0.001 seconds
        assert elapsed >= 0.001

    def test_call_empty(self):
        """Test handler with no arguments."""
        handler = EchoHandler({})
        
        result = handler("process")
        
        assert result["key"] == "process"
        assert result["body"] == ""
        assert result["query"] == {}

    def test_call_with_file_reference(self):
        """Test handler with file reference."""
        handler = EchoHandler({})
        
        mock_file = Mock()
        mock_file.name = "test.txt"
        
        result = handler("process", fileref=mock_file)
        
        # Should handle file reference
        assert result["key"] == "process"


class TestAPIDelegate:
    """Test APIDelegate class."""

    def test_init(self):
        """Test APIDelegate initialization."""
        handler = EchoHandler({})
        delegate = APIDelegate(handler)
        
        assert delegate._handler is not None

    def test_has_submit_endpoint(self):
        """Test delegate has submit endpoint."""
        handler = EchoHandler({})
        delegate = APIDelegate(handler)
        
        assert hasattr(delegate, 'submit')
        assert hasattr(delegate, 'lookup')
        assert hasattr(delegate, 'search')
        assert hasattr(delegate, 'raw')


class TestClass:
    """Test _class function."""

    def test_class_not_found(self):
        """Test loading non-existent class."""
        result = _class("nonexistent.module.Class")
        
        assert result is None

    def test_class_from_stdlib(self):
        """Test loading standard library class."""
        result = _class("json.JSONDecoder")
        
        assert result is not None


class TestInstanceFromConfig:
    """Test _instanceFromConfig function."""

    def test_invalid_config_missing_class(self):
        """Test config without class key."""
        config = {"config": {}}
        
        with pytest.raises(ValueError):
            _instanceFromConfig(config)

    def test_invalid_config_missing_instance(self):
        """Test config without instance key."""
        config = {"instance": {}}
        
        with pytest.raises(ValueError):
            _instanceFromConfig(config)

    def test_valid_echo_handler_config(self):
        """Test loading EchoHandler from config."""
        config = {
            "instance": {"class": "pyrest.service.EchoHandler"},
            "config": {}
        }
        
        handler = _instanceFromConfig(config)
        
        assert isinstance(handler, EchoHandler)


class TestServiceApp:
    """Test service app creation."""

    @patch('pyrest.service.open')
    @patch('json.load')
    def test_app_creation(self, mock_json_load, mock_open):
        """Test app creation from config."""
        mock_json_load.return_value = {
            "instance": {"class": "pyrest.service.EchoHandler"},
            "config": {}
        }
        
        # This requires the HANDLERCONFIG env var to be set
        with patch.dict('os.environ', {'HANDLERCONFIG': '/test/config.json'}):
            from pyrest.service import app
            # Would need to mock FastAPI to fully test
            # Just verify the function exists
            assert callable(app)
