"""Tests for pyrest.rest module."""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pyrest.rest import (
    RESTClient,
    RESTResponse,
    ApiClient,
    ApiException,
)


class TestRESTResponse:
    """Test RESTResponse class."""

    def test_init_with_response(self):
        """Test initialization with urllib3 response."""
        mock_resp = Mock()
        mock_resp.status = 200
        mock_resp.reason = "OK"
        mock_resp.data = b'{"key": "value"}'
        mock_resp.headers = {"Content-Type": "application/json"}
        
        response = RESTResponse(mock_resp)
        
        assert response.status == 200
        assert response.reason == "OK"
        assert response.data == b'{"key": "value"}'

    def test_getheaders(self):
        """Test getting response headers."""
        mock_resp = Mock()
        mock_resp.headers = {"Content-Type": "application/json"}
        
        response = RESTResponse(mock_resp)
        headers = response.getheaders()
        
        assert headers == {"Content-Type": "application/json"}

    def test_getheader_with_default(self):
        """Test getting header with default."""
        mock_resp = Mock()
        mock_resp.headers = {"Content-Type": "application/json"}
        
        response = RESTResponse(mock_resp)
        
        assert response.getheader("Content-Type") == "application/json"
        assert response.getheader("X-Custom", "default") == "default"


class TestRESTClient:
    """Test RESTClient class."""

    @patch('pyrest.rest.urllib3.PoolManager')
    def test_init_with_defaults(self, mock_pool_manager):
        """Test initialization with default values."""
        from pyrest.configuration import Configuration
        config = Configuration()
        
        client = RESTClient(config)
        
        assert client.pool_manager is not None

    @patch('pyrest.rest.urllib3.PoolManager')
    def test_init_with_ssl_disabled(self, mock_pool_manager):
        """Test initialization with SSL disabled."""
        from pyrest.configuration import Configuration
        config = Configuration()
        config.verify_ssl = False
        
        client = RESTClient(config)
        
        assert client.pool_manager is not None

    @patch('pyrest.rest.urllib3.PoolManager')
    def test_init_with_proxy(self, mock_pool_manager):
        """Test initialization with proxy."""
        from pyrest.configuration import Configuration
        config = Configuration()
        config.proxy = "http://proxy.example.com:8080"
        
        client = RESTClient(config)
        
        assert client.pool_manager is not None


class TestApiException:
    """Test ApiException class."""

    def test_init_with_http_response(self):
        """Test initialization with HTTP response."""
        mock_resp = Mock()
        mock_resp.status = 404
        mock_resp.reason = "Not Found"
        mock_resp.data = b'{"error": "not found"}'
        mock_resp.getheaders = Mock(return_value={"X-Custom": "value"})
        
        exc = ApiException(http_resp=mock_resp)
        
        assert exc.status == 404
        assert exc.reason == "Not Found"
        assert exc.body == b'{"error": "not found"}'
        assert exc.headers == {"X-Custom": "value"}

    def test_init_without_response(self):
        """Test initialization without HTTP response."""
        exc = ApiException(status=500, reason="Internal Error")
        
        assert exc.status == 500
        assert exc.reason == "Internal Error"
        assert exc.body is None
        assert exc.headers is None

    def test_str_with_all_fields(self):
        """Test string representation with all fields."""
        mock_resp = Mock()
        mock_resp.status = 400
        mock_resp.reason = "Bad Request"
        mock_resp.data = b'{"message": "error"}'
        mock_resp.getheaders = Mock(return_value={"Content-Type": "application/json"})
        
        exc = ApiException(http_resp=mock_resp)
        exc_str = str(exc)
        
        assert "400" in exc_str
        assert "Bad Request" in exc_str
        assert "HTTP response body" in exc_str


class TestApiClient:
    """Test ApiClient class."""

    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        client = ApiClient()
        
        assert client.configuration is not None
        assert client.pool is not None
        assert client.rest_client is not None

    def test_init_with_baseurl(self):
        """Test initialization with base URL."""
        client = ApiClient(baseurl="https://api.example.com")
        
        assert client.configuration.host == "https://api.example.com"

    def test_init_with_custom_headers(self):
        """Test initialization with custom headers."""
        client = ApiClient(header_name="X-Custom", header_value="value")
        
        assert client.default_headers["X-Custom"] == "value"

    def test_reply_ok(self):
        """Test replyOK status check."""
        client = ApiClient()
        
        assert client.replyOK(200) is True
        assert client.replyOK(201) is True
        assert client.replyOK(299) is True
        assert client.replyOK(199) is False
        assert client.replyOK(300) is False

    def test_create_exception(self):
        """Test exception creation."""
        client = ApiClient()
        
        exc = client.createException("Error", 500)
        
        assert isinstance(exc, ApiException)
        assert exc.reason == "Error"
        assert exc.status == 500

    def test_user_agent_default(self):
        """Test default user agent."""
        client = ApiClient()
        
        assert client.user_agent == 'APYC-1.0.0'

    def test_user_agent_setter(self):
        """Test user agent setter."""
        client = ApiClient()
        client.user_agent = "MyClient/1.0"
        
        assert client.user_agent == "MyClient/1.0"

    def test_set_default_header(self):
        """Test setting default header."""
        client = ApiClient()
        client.set_default_header("X-API-Key", "secret123")
        
        assert client.default_headers["X-API-Key"] == "secret123"

    def test_constants(self):
        """Test HTTP method constants."""
        assert ApiClient.POST == "POST"
        assert ApiClient.GET == "GET"
        assert ApiClient.PUT == "PUT"
        assert ApiClient.DELETE == "DELETE"
        assert ApiClient.PATCH == "PATCH"
        assert ApiClient.HEAD == "HEAD"
        assert ApiClient.OPTIONS == "OPTIONS"

    @patch('pyrest.rest.RESTClient.request')
    def test_get_method(self, mock_request):
        """Test GET method call."""
        client = ApiClient()
        mock_request.return_value = Mock()
        
        client.GET("/test")
        
        mock_request.assert_called_once()
        args = mock_request.call_args
        assert args[0][0] == "GET"

    @patch('pyrest.rest.RESTClient.request')
    def test_post_method(self, mock_request):
        """Test POST method call."""
        client = ApiClient()
        mock_request.return_value = Mock()
        
        client.POST("/test", body={"key": "value"})
        
        mock_request.assert_called_once()
        args = mock_request.call_args
        assert args[0][0] == "POST"

    @patch('pyrest.rest.RESTClient.request')
    def test_put_method(self, mock_request):
        """Test PUT method call."""
        client = ApiClient()
        mock_request.return_value = Mock()
        
        client.PUT("/test", body={"key": "value"})
        
        mock_request.assert_called_once()
        args = mock_request.call_args
        assert args[0][0] == "PUT"

    @patch('pyrest.rest.RESTClient.request')
    def test_delete_method(self, mock_request):
        """Test DELETE method call."""
        client = ApiClient()
        mock_request.return_value = Mock()
        
        client.DELETE("/test")
        
        mock_request.assert_called_once()
        args = mock_request.call_args
        assert args[0][0] == "DELETE"


class TestRESTClientRequest:
    """Test RESTClient request method."""

    @patch('pyrest.rest.urllib3.PoolManager')
    def test_get_request(self, mock_pool_manager):
        """Test GET request construction."""
        from pyrest.configuration import Configuration
        config = Configuration()
        client = RESTClient(config)
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.reason = "OK"
        mock_response.data = b'{}'
        mock_response.headers = {}
        
        mock_pool_manager.return_value.request.return_value = mock_response
        
        response = client.request("GET", "http://example.com/api")
        
        assert response.status == 200

    @patch('pyrest.rest.urllib3.PoolManager')
    def test_post_with_json_body(self, mock_pool_manager):
        """Test POST request with JSON body."""
        from pyrest.configuration import Configuration
        config = Configuration()
        client = RESTClient(config)
        
        mock_response = Mock()
        mock_response.status = 201
        mock_response.reason = "Created"
        mock_response.data = b'{}'
        mock_response.headers = {}
        
        mock_pool_manager.return_value.request.return_value = mock_response
        
        body = {"name": "test", "value": 123}
        response = client.request("POST", "http://example.com/api", body=body)
        
        assert response.status == 201

    @patch('pyrest.rest.urllib3.PoolManager')
    def test_query_params_in_get(self, mock_pool_manager):
        """Test GET request with query parameters."""
        from pyrest.configuration import Configuration
        config = Configuration()
        client = RESTClient(config)
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.reason = "OK"
        mock_response.data = b'{}'
        mock_response.headers = {}
        
        mock_pool_manager.return_value.request.return_value = mock_response
        
        response = client.request(
            "GET", 
            "http://example.com/api",
            query_params={"page": 1, "limit": 10}
        )
        
        assert response.status == 200

    @patch('pyrest.rest.urllib3.PoolManager')
    def test_custom_headers(self, mock_pool_manager):
        """Test request with custom headers."""
        from pyrest.configuration import Configuration
        config = Configuration()
        client = RESTClient(config)
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.reason = "OK"
        mock_response.data = b'{}'
        mock_response.headers = {}
        
        mock_pool_manager.return_value.request.return_value = mock_response
        
        headers = {"Authorization": "Bearer token123"}
        response = client.request(
            "GET", 
            "http://example.com/api",
            headers=headers
        )
        
        assert response.status == 200
