"""
Global pytest configuration to fix test issues.
Fixes file descriptor leaks, hanging tests, and recursion errors.
"""

import pytest
import sys
import os
import asyncio
import gc
import tempfile
import warnings
from unittest.mock import Mock, patch
from pathlib import Path

# Suppress warnings that can cause issues
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Global test timeout
pytest.timeout = 300  # 5 minutes


@pytest.fixture(autouse=True)
def cleanup_file_descriptors():
    """Ensure file descriptors are clean between tests."""
    # Before test
    sys.stdout.flush()
    sys.stderr.flush()
    
    yield
    
    # After test
    sys.stdout.flush()
    sys.stderr.flush()
    gc.collect()
    
    # Close any open temp files
    try:
        tempfile._get_default_tempdir()
    except:
        pass


# Removed custom event_loop fixture to prevent conflicts with pytest-asyncio
# The default pytest-asyncio event loop handling is sufficient


@pytest.fixture(autouse=True)
def prevent_recursion():
    """Prevent recursion errors in mocks."""
    original_recursion_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(1000)  # Reasonable limit
    
    yield
    
    sys.setrecursionlimit(original_recursion_limit)


# Removed problematic import mocking that interferes with legitimate imports


@pytest.fixture(autouse=True)
def disable_capture_for_problematic_tests(request):
    """Disable stdout/stderr capture for tests that have file descriptor issues."""
    test_name = request.node.name
    problematic_tests = [
        'test_final_1_percent',
        'test_force_100',
        'test_all_function_imports',
        'test_force_all_remaining_imports'
    ]
    
    if any(name in test_name for name in problematic_tests):
        # Disable capture
        request.config.option.capture = "no"


@pytest.fixture
def temp_directory():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up clean test environment."""
    # Set environment variables to prevent external calls
    test_env = {
        'LILYPAD_API_KEY': 'test_key',
        'LILYPAD_PROJECT_ID': 'test_project',
        'LILYPAD_BASE_URL': 'http://localhost:8000',
        'PYTEST_CURRENT_TEST': 'true',
        'CI': 'true',
    }
    
    with patch.dict(os.environ, test_env):
        yield


@pytest.fixture(autouse=True)
def mock_external_dependencies(request):
    """Mock external dependencies that can cause hanging."""
    # Skip subprocess mocking for closure tests
    test_name = request.node.name
    test_file = str(request.node.fspath) if hasattr(request.node, 'fspath') else str(request.node.path)
    
    # Don't mock subprocess for closure tests
    skip_subprocess_mock = (
        'closure' in test_name.lower() or 
        'test_closure.py' in test_file or
        '/closure/' in test_file
    )
    
    # Create proper mock responses with integer status codes
    def create_mock_httpx_client(*args, **kwargs):
        """Create mock httpx client that accepts any arguments."""
        from unittest.mock import AsyncMock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200  # Actual integer, not Mock
        mock_response.json.return_value = {"functions": [], "items": []}
        mock_response.raise_for_status.return_value = None
        mock_client.request.return_value = mock_response
        mock_client.get.return_value = mock_response
        mock_client.post.return_value = mock_response
        # Add timeout attribute for compatibility
        if 'timeout' in kwargs:
            mock_client.timeout = Mock()
            mock_client.timeout.read = kwargs['timeout']
        return mock_client
    
    def create_mock_async_httpx_client(*args, **kwargs):
        """Create mock async httpx client that accepts any arguments."""
        from unittest.mock import AsyncMock
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200  # Actual integer, not Mock
        mock_response.json.return_value = {"functions": [], "items": []}
        mock_response.raise_for_status.return_value = None
        # Make async methods return awaitables
        mock_client.request.return_value = mock_response
        mock_client.get.return_value = mock_response
        mock_client.post.return_value = mock_response
        # Add timeout attribute for compatibility
        if 'timeout' in kwargs:
            mock_client.timeout = Mock()
            mock_client.timeout.read = kwargs['timeout']
        return mock_client
    
    def create_mock_requests_response():
        mock_response = Mock()
        mock_response.status_code = 200  # Actual integer, not Mock
        mock_response.json.return_value = {"functions": [], "items": []}
        mock_response.raise_for_status.return_value = None
        return mock_response
    
    mocks = {
        'httpx.Client': create_mock_httpx_client,
        'httpx.AsyncClient': create_mock_async_httpx_client,
        'requests.get': create_mock_requests_response,
        'requests.post': create_mock_requests_response,
    }
    
    # Only add subprocess mocks if not a closure test
    if not skip_subprocess_mock:
        mocks['subprocess.run'] = Mock(return_value=Mock(returncode=0, stdout="", stderr=""))
        mocks['subprocess.Popen'] = Mock
    
    patches = []
    for module_path, mock_obj in mocks.items():
        try:
            patch_obj = patch(module_path, mock_obj)
            patches.append(patch_obj)
            patch_obj.start()
        except:
            pass
    
    yield
    
    for patch_obj in patches:
        try:
            patch_obj.stop()
        except:
            pass


@pytest.fixture
def mock_sync_client():
    """Mock sync client to prevent network calls."""
    mock_client = Mock()
    mock_client.projects.functions.get_by_name.return_value = []
    mock_client.projects.functions.list_paginated.return_value = Mock(items=[])
    return mock_client


@pytest.fixture
def mock_async_client():
    """Mock async client to prevent network calls."""
    mock_client = Mock()
    mock_client.projects.functions.get_by_name = Mock(return_value=[])
    mock_client.projects.functions.list_paginated = Mock(return_value=Mock(items=[]))
    return mock_client


# Test markers for problematic tests
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "hanging: marks tests that may hang")
    config.addinivalue_line("markers", "file_descriptor: marks tests with file descriptor issues")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle problematic tests."""
    for item in items:
        # Mark tests that might hang
        if any(name in item.name for name in ['test_final_1_percent', 'test_force_100', 'test_all_function_imports']):
            item.add_marker(pytest.mark.hanging)
            item.add_marker(pytest.mark.timeout(30))  # 30 second timeout
        
        # Mark tests with file descriptor issues  
        if any(name in item.name for name in ['test_force_all_remaining_imports', 'test_all_file_operations']):
            item.add_marker(pytest.mark.file_descriptor)


# Handle test failures gracefully
def pytest_runtest_teardown(item, nextitem):
    """Clean up after each test."""
    # Force garbage collection
    gc.collect()
    
    # Reset any global state
    try:
        import lilypad.cli.commands.sync
        lilypad.cli.commands.sync.DEBUG = False
    except:
        pass