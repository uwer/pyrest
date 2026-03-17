# pyrest

A Python library for building REST API clients and servers with minimal boilerplate code.

## Overview

**pyrest** provides a generic REST API client modeled after Swagger, plus a FastAPI-based server framework. It handles encoding, parameter packaging, and supports pydantic models for data validation.

## Features

- **REST Client**: Generic HTTP client with support for all HTTP methods
- **REST Server**: FastAPI-based server with handler support
- **GeoServer Integration**: Specialized client for GeoServer REST API
- **Async Support**: Thread-based async execution with observable state
- **Prometheus Metrics**: Built-in monitoring support
- **Docker Ready**: Easy containerization

## Installation

```bash
# Install client dependencies only
pip install -r requirements-client.txt

# Install full server dependencies
pip install -r requirements-server.txt
```

### Client Dependencies

- `certifi` - SSL certificates
- `urllib3` - HTTP library
- `httpx` - HTTP client

### Server Dependencies

- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `starlette` - ASGI framework
- `pydantic` - Data validation
- `classy_fastapi` - Route class decorators
- `python-multipart` - Form data parsing

## Usage

### REST Client

```python
from pyrest import ApiClient
from pyrest.configuration import Configuration

# Create configuration
config = Configuration()
config.host = "https://api.example.com"
config.verify_ssl = True

# Create client
client = ApiClient(configuration=config)

# Make requests
response = client.GET("/users")
response = client.POST("/users", body={"name": "John"})
response = client.PUT("/users/1", body={"name": "Jane"})
response = client.DELETE("/users/1")
```

### REST Server

Create a handler class:

```python
from pyrest.service import APIDelegate

def my_handler(key, **kwargs):
    body = kwargs.get("body", b"").decode()
    query = kwargs.get("query", {})
    return {"success": True, "data": {"received": body}}

# Wrap in delegate
app = APIDelegate(my_handler)
```

Or extend `BaseHandler` for full control:

```python
from pyrest.handlers import BaseHandler
from classy_fastapi import get, post

class MyHandler(BaseHandler):
    
    @get("/hello/{name}")
    def hello(self, name: str):
        return {"message": f"Hello, {name}!"}
    
    @post("/data")
    def handle_data(self, request: Request):
        return {"success": True}
```

### Running the Server

```bash
# Using environment variables
export HANDLERCONFIG=/path/to/config.json
export HANDLERPORT=9088
python -m pyrest.service
```

## Configuration

### Handler Config Format (JSON)

```json
{
  "instance": {
    "class": "module.path.ToYourHandler"
  },
  "config": {
    "key": "value"
  },
  "file-config": "/path/to/config.json",
  "config-history": "/path/to/history.json"
}
```

### Docker

```dockerfile
FROM python:3.9-slim
COPY src/pyrest /app/pyrest
COPY requirements*.txt /app/
RUN pip install -r requirements-server.txt
ENV HANDLERCONFIG=/app/pyrest/echo.json
ENV HANDLERPORT=9088
CMD ["python", "-m", "pyrest.service"]
```

Build and run:

```bash
docker build -f echo.dockerfile -t pyrest .
docker run -p 9088:9088 pyrest
```

## API Reference

### ApiClient Methods

| Method | Description |
|--------|-------------|
| `GET(url, ...)` | GET request |
| `POST(url, body=..., ...)` | POST request |
| `PUT(url, body=..., ...)` | PUT request |
| `PATCH(url, body=..., ...)` | PATCH request |
| `DELETE(url, ...)` | DELETE request |
| `HEAD(url, ...)` | HEAD request |
| `OPTIONS(url, ...)` | OPTIONS request |

### BaseHandler Endpoints

The `BaseHandler` provides built-in endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/test` | GET | Health check |
| `/messages/status/{messageid}` | GET | Check message status |
| `/messages/message/{messageid}` | GET | Get message content |
| `/messages/all` | GET | List all messages |
| `/messages/message/{messageid}` | DELETE | Delete message |
| `/messages/before/{timestr}` | DELETE | Delete messages before time |
| `/messages/ended/{messageid}` | GET | Check if process ended |
| `/messages/results/{messageid}` | GET | Get process results |

### Message Store

`MessageStore` provides async task tracking:

```python
from pyrest.handlers import MessageStore

store = MessageStore.getInstance()

# Launch async task
pid, obj = store.addProcess(my_function, args=[], kwargs={})

# Check status
status = store.status(pid)

# Get results
results = store.processResults(pid)
```

### Time Duration Parsing

```python
from pyrest.deltat import parse_time

td = parse_time("2h 30m")  # Returns timedelta(hours=2, minutes=30)
```

Supported formats: `1w`, `2d`, `3h`, `4m`, `5s` (can be combined)

## GeoServer Client

Specialized client for GeoServer REST API:

```python
from pyrest.geoserver import GSAPIClient

client = GSAPIClient({
    "url": "http://localhost:8080/geoserver",
    "username": "admin",
    "password": "geoserver"
})

# List workspaces
workspaces = client.getWorkspaces()

# Create feature store
client.createFeatureStore("workspace", {"name": "store", ...})

# Upload shapefile
client.buildFeatureStoreAndType("workspace", "store", zip_data)
```

## Prometheus Metrics

Enable Prometheus metrics:

```python
from pyrest._prom import initPomScrape, start_pom

# Start scrape server on port
initPomScrape(9090)
start_pom()
```

Or use push gateway:

```python
from pyrest._prom import initPomPush, start_pom

initPomPush("localhost", 9091, "my-job")
start_pom()
```

## License

MIT License - see [LICENSE](LICENSE) file.

## Version

Current version: 0.9.0
