"""Tests for pyrest.handlers module."""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pyrest.handlers import (
    MessageStore,
    BaseHandler,
)


class TestMessageStore:
    """Test MessageStore class."""

    def test_singleton_pattern(self):
        """Test MessageStore is a singleton."""
        store1 = MessageStore.getInstance()
        store2 = MessageStore.getInstance()
        
        assert store1 is store2

    def test_add_process(self):
        """Test adding a process to the store."""
        store = MessageStore.getInstance()
        
        def my_func():
            return "result"
        
        pid, obj = store.addProcess(my_func, [], {})
        
        assert pid is not None
        assert obj is not None
        assert store.has(pid)

    def test_process_results(self):
        """Test getting process results."""
        store = MessageStore.getInstance()
        
        def my_func():
            return "expected_result"
        
        pid, obj = store.addProcess(my_func, [], {})
        obj.start()
        obj.join()
        
        result = store.processResults(pid)
        
        assert result == "expected_result"

    def test_process_ended_normally(self):
        """Test checking if process ended normally."""
        store = MessageStore.getInstance()
        
        def my_func():
            return True
        
        pid, obj = store.addProcess(my_func, [], {})
        obj.start()
        obj.join()
        
        ended = store.processEndedNormaly(pid)
        
        assert ended is True

    def test_process_status(self):
        """Test getting process status."""
        store = MessageStore.getInstance()
        
        def quick_func():
            return "done"
        
        pid, obj = store.addProcess(quick_func, [], {})
        obj.start()
        obj.join()
        
        status, last_mod, running = store.status(pid)
        
        assert isinstance(status, str)
        assert isinstance(running, bool)

    def test_all_messages(self):
        """Test getting all messages."""
        store = MessageStore.getInstance()
        
        def func_with_print():
            print("Test message")
            return "done"
        
        pid, obj = store.addProcess(func_with_print, [], {})
        obj.start()
        obj.join()
        
        messages, last_mod, running = store.allMessages(pid)
        
        assert isinstance(messages, list)

    def test_delete_process(self):
        """Test deleting a process."""
        store = MessageStore.getInstance()
        
        def my_func():
            return "result"
        
        pid, obj = store.addProcess(my_func, [], {})
        
        assert store.has(pid)
        
        store.delete(pid)
        
        assert not store.has(pid)

    def test_all_method(self):
        """Test getting all processes."""
        store = MessageStore.getInstance()
        
        def func1():
            return "result1"
        
        def func2():
            return "result2"
        
        pid1, _ = store.addProcess(func1, [], {})
        pid2, _ = store.addProcess(func2, [], {})
        
        all_processes = store.all()
        
        assert len(all_processes) >= 2
        pids = [p["process"] for p in all_processes]
        assert pid1 in pids
        assert pid2 in pids


class TestBaseHandler:
    """Test BaseHandler class."""

    def test_init_with_empty_props(self):
        """Test initialization with empty properties."""
        handler = BaseHandler({})
        
        assert handler._properties == {}

    def test_init_with_props(self):
        """Test initialization with properties."""
        props = {"context": "test", "key": "value"}
        handler = BaseHandler(props)
        
        assert handler._properties["context"] == "test"
        assert handler._properties["key"] == "value"

    def test_has_properties(self):
        """Test handler has properties."""
        props = {"context": "myapp"}
        handler = BaseHandler(props)
        
        assert hasattr(handler, '_properties')

    def test_get_test_endpoint(self):
        """Test handler has test endpoint."""
        props = {"context": "test"}
        handler = BaseHandler(props)
        
        assert hasattr(handler, 'get_test')

    def test_message_endpoints_exist(self):
        """Test handler has message endpoints."""
        props = {"context": "test"}
        handler = BaseHandler(props)
        
        # Check for message-related endpoints
        assert hasattr(handler, 'get_status_message')
        assert hasattr(handler, 'get_messages')
        assert hasattr(handler, 'get_messages_all')
        assert hasattr(handler, 'delete_message')
        assert hasattr(handler, 'delete_messages_before')
        assert hasattr(handler, 'get_ended')
        assert hasattr(handler, 'get_results')
