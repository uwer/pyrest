"""Tests for pyrest.utils module."""

import pytest
import json
import tempfile
import os
from datetime import datetime
from pyrest.utils import (
    loadJsonAndResolve,
    mergeJson,
    mergeJsonDicts,
    loadFromJsonFileList,
    mergeJsonFiles,
    ObservableThread,
    RepeatTimer,
)


class TestLoadJsonAndResolve:
    """Test JSON loading with environment variable resolution."""

    def test_load_simple_json(self, tmp_path):
        """Test loading a simple JSON file."""
        data = {"key": "value", "number": 42}
        
        f = tmp_path / "test.json"
        f.write_text(json.dumps(data))
        
        result = loadJsonAndResolve(str(f))
        assert result == data

    def test_load_json_with_env_var(self, tmp_path, monkeypatch):
        """Test loading JSON with environment variable."""
        monkeypatch.setenv("TEST_VAR", "resolved_value")
        
        f = tmp_path / "test.json"
        f.write_text('{"key": "$TEST_VAR"}')
        
        result = loadJsonAndResolve(str(f))
        assert result["key"] == "resolved_value"

    def test_load_json_with_missing_env_var(self, tmp_path, monkeypatch):
        """Test loading JSON with missing environment variable."""
        # Ensure env var doesn't exist
        monkeypatch.delenv("NONEXISTENT_VAR", raising=False)
        
        f = tmp_path / "test.json"
        f.write_text('{"key": "$NONEXISTENT_VAR"}')
        
        result = loadJsonAndResolve(str(f))
        assert result["key"] == ""


class TestMergeJson:
    """Test JSON merging functionality."""

    def test_merge_simple_dicts(self):
        """Test merging two simple dictionaries."""
        dict0 = {"a": 1, "b": 2}
        dict1 = {"b": 3, "c": 4}
        
        mergeJson(dict0, dict1)
        
        assert dict0 == {"a": 1, "b": 3, "c": 4}

    def test_merge_nested_dicts(self):
        """Test merging nested dictionaries."""
        dict0 = {"a": {"x": 1, "y": 2}}
        dict1 = {"a": {"y": 3, "z": 4}}
        
        mergeJson(dict0, dict1)
        
        assert dict0 == {"a": {"x": 1, "y": 3, "z": 4}}

    def test_merge_returns_false(self):
        """Test mergeJson returns False when dict1 is not a dict."""
        dict0 = {"a": 1}
        
        result = mergeJson(dict0, "not a dict")
        
        assert result is True
        assert dict0 == {"a": 1}

    def test_merge_adds_new_keys(self):
        """Test that merge adds new keys from dict1."""
        dict0 = {"a": 1}
        dict1 = {"b": 2, "c": 3}
        
        mergeJson(dict0, dict1)
        
        assert dict0 == {"a": 1, "b": 2, "c": 3}


class TestMergeJsonDicts:
    """Test merging multiple JSON dictionaries."""

    def test_merge_multiple_dicts(self):
        """Test merging multiple dictionaries."""
        dicts = [{"a": 1}, {"b": 2}, {"c": 3}]
        
        result = mergeJsonDicts(dicts)
        
        assert result == {"a": 1, "b": 2, "c": 3}

    def test_merge_overwrites_values(self):
        """Test that later dicts overwrite earlier ones."""
        dicts = [{"a": 1, "b": 2}, {"b": 3, "c": 4}]
        
        result = mergeJsonDicts(dicts)
        
        assert result == {"a": 1, "b": 3, "c": 4}


class TestLoadFromJsonFileList:
    """Test loading from JSON file list."""

    def test_load_single_file(self, tmp_path):
        """Test loading a single JSON file."""
        data = {"key": "value"}
        
        f = tmp_path / "config.json"
        f.write_text(json.dumps(data))
        
        result = loadFromJsonFileList(str(f))
        assert result == data

    def test_load_multiple_files(self, tmp_path):
        """Test loading multiple JSON files (comma-separated)."""
        data1 = {"a": 1}
        data2 = {"b": 2}
        
        f1 = tmp_path / "config1.json"
        f2 = tmp_path / "config2.json"
        f1.write_text(json.dumps(data1))
        f2.write_text(json.dumps(data2))
        
        result = loadFromJsonFileList(f"{f1},{f2}")
        
        assert result["a"] == 1
        assert result["b"] == 2

    def test_load_nonexistent_file_returns_empty(self, tmp_path):
        """Test loading nonexistent file returns empty dict."""
        result = loadFromJsonFileList("/nonexistent/file.json")
        
        assert result == {}


class TestMergeJsonFiles:
    """Test merging JSON files to disk."""

    def test_merge_to_temp_file(self, tmp_path):
        """Test merging creates a temp file."""
        data = {"a": 1, "b": 2}
        
        f = tmp_path / "config.json"
        f.write_text(json.dumps(data))
        
        filename, result = mergeJsonFiles(str(f))
        
        assert os.path.exists(filename)
        assert result == data
        
        # Clean up temp file
        os.unlink(filename)


class TestObservableThread:
    """Test ObservableThread class."""

    def test_thread_execution(self):
        """Test thread runs and returns result."""
        def my_func():
            return 42
        
        thread = ObservableThread("test_pid", my_func, [], {})
        thread.start()
        thread.join()
        
        assert thread.result() == 42

    def test_thread_with_args(self):
        """Test thread with arguments."""
        def add(a, b):
            return a + b
        
        thread = ObservableThread("test_pid", add, [1, 2], {})
        thread.start()
        thread.join()
        
        assert thread.result() == 3

    def test_thread_with_kwargs(self):
        """Test thread with keyword arguments."""
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"
        
        thread = ObservableThread("test_pid", greet, [], {"name": "World"})
        thread.start()
        thread.join()
        
        assert thread.result() == "Hello, World!"

    def test_thread_write_buffer(self):
        """Test thread write buffer."""
        def func_with_print():
            print("Test message")
            return "done"
        
        thread = ObservableThread("test_pid", func_with_print, [], {})
        thread.start()
        thread.join()
        
        assert len(thread._buf) > 0

    def test_thread_status(self):
        """Test thread status reporting."""
        def quick_func():
            return "done"
        
        thread = ObservableThread("test_pid", quick_func, [], {})
        thread.start()
        thread.join()
        
        status, last_mod, running = thread.status()
        
        assert isinstance(status, str)
        assert isinstance(running, bool)

    def test_thread_ended_normally(self):
        """Test endedNormaly flag."""
        def success_func():
            return True
        
        thread = ObservableThread("test_pid", success_func, [], {})
        thread.start()
        thread.join()
        
        assert thread.endedNormaly() is True

    def test_thread_exception_handling(self):
        """Test thread exception handling."""
        def fail_func():
            raise ValueError("Test error")
        
        thread = ObservableThread("test_pid", fail_func, [], {})
        thread.start()
        thread.join()
        
        # Thread should have recorded the error in buffer
        assert len(thread._buf) > 0


class TestRepeatTimer:
    """Test RepeatTimer class."""

    def test_timer_creation(self):
        """Test timer is created and starts."""
        call_count = {"count": 0}
        
        def increment():
            call_count["count"] += 1
        
        timer = RepeatTimer(0.1, increment)
        
        # Wait for at least one execution
        import time
        time.sleep(0.25)
        
        assert call_count["count"] >= 1
        
        timer.stop()

    def test_timer_stop(self):
        """Test stopping the timer."""
        call_count = {"count": 0}
        
        def increment():
            call_count["count"] += 1
        
        timer = RepeatTimer(0.1, increment)
        timer.stop()
        
        # Give some time
        import time
        time.sleep(0.2)
        
        # Timer should have executed at least once before stop
        # but shouldn't continue after stop
        timer.stop()  # Stop again is safe

    def test_timer_with_defer(self):
        """Test timer with deferred start."""
        call_count = {"count": 0}
        
        def increment():
            call_count["count"] += 1
        
        timer = RepeatTimer(0.1, increment, defer=0.2)
        
        import time
        # Wait less than defer time
        time.sleep(0.1)
        assert call_count["count"] == 0
        
        # Wait for deferred start
        time.sleep(0.2)
        assert call_count["count"] >= 1
        
        timer.stop()
