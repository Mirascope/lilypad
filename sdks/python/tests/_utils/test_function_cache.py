"""Test cases for function_cache utilities."""

import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock

import pytest

from lilypad._utils.function_cache import (
    get_function_by_hash_sync,
    get_function_by_hash_async,
    get_function_by_version_sync,
    get_function_by_version_async,
    get_deployed_function_sync,
    get_deployed_function_async,
    get_cached_closure,
    _LRU,
    _expired,
    _deployed_cache,
    _hash_async_cache,
    _version_async_cache,
)
from lilypad.generated.types.function_public import FunctionPublic
from lilypad._utils import Closure


@pytest.fixture
def mock_function():
    """Create a mock FunctionPublic."""
    func = Mock(spec=FunctionPublic)
    func.uuid_ = "test-uuid-123"
    func.name = "test_function"
    func.code = "def test_function(): return 42"
    func.signature = "def test_function():"
    func.hash = "abc123"
    func.dependencies = {"numpy": Mock(model_dump=Mock(return_value={"version": "1.21.0", "extras": []}))}
    return func


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear all caches before each test."""
    _deployed_cache.clear()
    _hash_async_cache.clear()
    _version_async_cache.clear()
    get_function_by_hash_sync.cache_clear()
    get_function_by_version_sync.cache_clear()


def test_expired():
    """Test the _expired helper function."""
    current = time.time()

    # Not expired - timestamp is recent
    assert _expired(current - 10, 30) is False

    # Expired - timestamp is old
    assert _expired(current - 40, 30) is True

    # TTL is 0 - never expires
    assert _expired(current - 1000, 0) is False

    # TTL is negative - never expires
    assert _expired(current - 1000, -1) is False


@patch("lilypad._utils.function_cache.get_sync_client")
def test_get_function_by_hash_sync(mock_get_client, mock_function):
    """Test synchronous function retrieval by hash."""
    # Setup mock client
    mock_client = Mock()
    mock_client.projects.functions.get_by_hash.return_value = mock_function
    mock_get_client.return_value = mock_client

    # First call - should hit API
    result1 = get_function_by_hash_sync("project-123", "hash-abc")
    assert result1 == mock_function
    mock_client.projects.functions.get_by_hash.assert_called_once_with(
        project_uuid="project-123", function_hash="hash-abc"
    )

    # Second call - should use cache (LRU)
    result2 = get_function_by_hash_sync("project-123", "hash-abc")
    assert result2 == mock_function
    # Still only called once due to caching
    assert mock_client.projects.functions.get_by_hash.call_count == 1


@pytest.mark.asyncio
@patch("lilypad._utils.function_cache.get_async_client")
async def test_get_function_by_hash_async(mock_get_client, mock_function):
    """Test asynchronous function retrieval by hash."""
    # Setup mock client
    mock_client = Mock()
    mock_client.projects.functions.get_by_hash = AsyncMock(return_value=mock_function)
    mock_get_client.return_value = mock_client

    # First call - should hit API
    result1 = await get_function_by_hash_async("project-123", "hash-abc")
    assert result1 == mock_function
    mock_client.projects.functions.get_by_hash.assert_called_once_with(
        project_uuid="project-123", function_hash="hash-abc"
    )

    # Second call - should use cache
    result2 = await get_function_by_hash_async("project-123", "hash-abc")
    assert result2 == mock_function
    # Still only called once due to caching
    assert mock_client.projects.functions.get_by_hash.call_count == 1


@patch("lilypad._utils.function_cache.get_sync_client")
def test_get_function_by_version_sync(mock_get_client, mock_function):
    """Test synchronous function retrieval by version."""
    # Setup mock client
    mock_client = Mock()
    mock_client.projects.functions.get_by_version.return_value = mock_function
    mock_get_client.return_value = mock_client

    # First call - should hit API
    result1 = get_function_by_version_sync("project-123", "my_func", 1)
    assert result1 == mock_function
    mock_client.projects.functions.get_by_version.assert_called_once_with(
        project_uuid="project-123", function_name="my_func", version_num=1
    )

    # Second call - should use cache
    result2 = get_function_by_version_sync("project-123", "my_func", 1)
    assert result2 == mock_function
    assert mock_client.projects.functions.get_by_version.call_count == 1


@pytest.mark.asyncio
@patch("lilypad._utils.function_cache.get_async_client")
async def test_get_function_by_version_async(mock_get_client, mock_function):
    """Test asynchronous function retrieval by version."""
    # Setup mock client
    mock_client = Mock()
    mock_client.projects.functions.get_by_version = AsyncMock(return_value=mock_function)
    mock_get_client.return_value = mock_client

    # First call - should hit API
    result1 = await get_function_by_version_async("project-123", "my_func", 1)
    assert result1 == mock_function
    mock_client.projects.functions.get_by_version.assert_called_once_with(
        project_uuid="project-123", function_name="my_func", version_num=1
    )

    # Second call - should use cache
    result2 = await get_function_by_version_async("project-123", "my_func", 1)
    assert result2 == mock_function
    assert mock_client.projects.functions.get_by_version.call_count == 1


@patch("lilypad._utils.function_cache.get_sync_client")
@patch("lilypad._utils.function_cache.time")
def test_get_deployed_function_sync(mock_time, mock_get_client, mock_function):
    """Test synchronous deployed function retrieval with TTL."""
    # Setup mock client
    mock_client = Mock()
    mock_client.projects.functions.get_deployed_environments.return_value = mock_function
    mock_get_client.return_value = mock_client

    # Mock time
    mock_time.return_value = 1000.0

    # First call - should hit API
    result1 = get_deployed_function_sync("project-123", "my_func", ttl=30)
    assert result1 == mock_function
    mock_client.projects.functions.get_deployed_environments.assert_called_once()

    # Second call within TTL - should use cache
    mock_time.return_value = 1020.0  # 20 seconds later
    result2 = get_deployed_function_sync("project-123", "my_func", ttl=30)
    assert result2 == mock_function
    assert mock_client.projects.functions.get_deployed_environments.call_count == 1

    # Third call after TTL - should hit API again
    mock_time.return_value = 1040.0  # 40 seconds later
    result3 = get_deployed_function_sync("project-123", "my_func", ttl=30)
    assert result3 == mock_function
    assert mock_client.projects.functions.get_deployed_environments.call_count == 2


@patch("lilypad._utils.function_cache.get_sync_client")
def test_get_deployed_function_sync_force_refresh(mock_get_client, mock_function):
    """Test force refresh for deployed function."""
    # Setup mock client
    mock_client = Mock()
    mock_client.projects.functions.get_deployed_environments.return_value = mock_function
    mock_get_client.return_value = mock_client

    # First call
    result1 = get_deployed_function_sync("project-123", "my_func")
    assert result1 == mock_function
    assert mock_client.projects.functions.get_deployed_environments.call_count == 1

    # Second call with force_refresh
    result2 = get_deployed_function_sync("project-123", "my_func", force_refresh=True)
    assert result2 == mock_function
    assert mock_client.projects.functions.get_deployed_environments.call_count == 2


@pytest.mark.asyncio
@patch("lilypad._utils.function_cache.get_async_client")
@patch("lilypad._utils.function_cache.time")
async def test_get_deployed_function_async(mock_time, mock_get_client, mock_function):
    """Test asynchronous deployed function retrieval with TTL."""
    # Setup mock client
    mock_client = Mock()
    mock_client.projects.functions.get_deployed_environments = AsyncMock(return_value=mock_function)
    mock_get_client.return_value = mock_client

    # Mock time
    mock_time.return_value = 1000.0

    # First call - should hit API
    result1 = await get_deployed_function_async("project-123", "my_func", ttl=30)
    assert result1 == mock_function
    mock_client.projects.functions.get_deployed_environments.assert_called_once()

    # Second call within TTL - should use cache
    mock_time.return_value = 1020.0  # 20 seconds later
    result2 = await get_deployed_function_async("project-123", "my_func", ttl=30)
    assert result2 == mock_function
    assert mock_client.projects.functions.get_deployed_environments.call_count == 1


def test_get_cached_closure(mock_function):
    """Test closure caching."""
    # First call - should create closure
    closure1 = get_cached_closure(mock_function)
    assert isinstance(closure1, Closure)
    assert closure1.name == "test_function"
    assert closure1.code == "def test_function(): return 42"
    assert closure1.signature == "def test_function():"
    assert closure1.hash == "abc123"
    assert "numpy" in closure1.dependencies

    # Second call - should return same closure
    closure2 = get_cached_closure(mock_function)
    assert closure2 is closure1  # Same object reference


def test_lru_cache():
    """Test the custom LRU cache implementation."""
    cache = _LRU(maxsize=3)

    # Test basic get_or_create
    factory_calls = 0

    def factory():
        nonlocal factory_calls
        factory_calls += 1
        return f"value_{factory_calls}"

    # Add items
    val1 = cache.get_or_create("key1", factory)
    assert val1 == "value_1"
    assert factory_calls == 1

    val2 = cache.get_or_create("key2", factory)
    assert val2 == "value_2"
    assert factory_calls == 2

    val3 = cache.get_or_create("key3", factory)
    assert val3 == "value_3"
    assert factory_calls == 3

    # Access existing key - should not call factory
    val1_again = cache.get_or_create("key1", factory)
    assert val1_again == "value_1"
    assert factory_calls == 3

    # Add fourth item - should evict least recently used (key2)
    val4 = cache.get_or_create("key4", factory)
    assert val4 == "value_4"
    assert factory_calls == 4
    assert len(cache) == 3
    assert "key2" not in cache
    assert "key1" in cache  # Was accessed recently
    assert "key3" in cache
    assert "key4" in cache


def test_lru_cache_thread_safety():
    """Test that LRU cache is thread-safe."""
    import threading

    cache = _LRU(maxsize=100)
    results = []

    def worker(thread_id):
        for i in range(10):
            key = f"thread_{thread_id}_item_{i}"
            value = cache.get_or_create(key, lambda idx=i: f"value_{thread_id}_{idx}")
            results.append((key, value))

    threads = []
    for i in range(5):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Verify all operations completed
    assert len(results) == 50

    # Verify cache consistency
    for key, expected_value in results:
        if key in cache:
            assert cache[key] == expected_value


@pytest.mark.asyncio
async def test_get_function_by_hash_async_race_condition(mock_function):
    """Test async hash cache with race condition (lines 54-68)."""
    # Clear the async cache
    _hash_async_cache.clear()

    # Setup mock client
    mock_client = Mock()
    mock_client.projects.functions.get_by_hash = AsyncMock(return_value=mock_function)

    with patch("lilypad._utils.function_cache.get_async_client", return_value=mock_client):
        # First call to populate cache
        result1 = await get_function_by_hash_async("project-123", "hash-abc")
        assert result1 == mock_function

        # Second call should hit cache (line 56)
        result2 = await get_function_by_hash_async("project-123", "hash-abc")
        assert result2 == mock_function
        assert mock_client.projects.functions.get_by_hash.call_count == 1

        # Clear cache and test race condition handling
        _hash_async_cache.clear()

        # Manually add to cache to test lost race scenario (line 60)
        key = ("project-123", "hash-abc")
        _hash_async_cache[key] = mock_function

        # Call should return cached value
        result3 = await get_function_by_hash_async("project-123", "hash-abc")
        assert result3 == mock_function


@pytest.mark.asyncio
async def test_get_function_by_version_async_race_condition(mock_function):
    """Test async version cache with race condition (lines 92-107)."""
    # Clear the async cache
    _version_async_cache.clear()

    # Setup mock client
    mock_client = Mock()
    mock_client.projects.functions.get_by_version = AsyncMock(return_value=mock_function)

    with patch("lilypad._utils.function_cache.get_async_client", return_value=mock_client):
        # First call to populate cache
        result1 = await get_function_by_version_async("project-123", "my_func", 1)
        assert result1 == mock_function

        # Second call should hit cache (line 94)
        result2 = await get_function_by_version_async("project-123", "my_func", 1)
        assert result2 == mock_function
        assert mock_client.projects.functions.get_by_version.call_count == 1

        # Clear cache and test race condition handling
        _version_async_cache.clear()

        # Manually add to cache to test lost race scenario (line 98)
        key = ("project-123", "my_func", 1)
        _version_async_cache[key] = mock_function

        # Call should return cached value
        result3 = await get_function_by_version_async("project-123", "my_func", 1)
        assert result3 == mock_function


@pytest.mark.asyncio
async def test_get_deployed_function_async_with_ttl_and_force_refresh(mock_function):
    """Test async deployed function with TTL and race conditions (lines 148-169)."""
    # Clear the deployed cache
    _deployed_cache.clear()

    # Setup mock client
    mock_client = Mock()
    mock_client.projects.functions.get_deployed_environments = AsyncMock(return_value=mock_function)

    with (
        patch("lilypad._utils.function_cache.get_async_client", return_value=mock_client),
        patch("lilypad._utils.function_cache.time") as mock_time,
    ):
        mock_time.return_value = 1000.0

        # Test default TTL assignment (line 149)
        result1 = await get_deployed_function_async("project-123", "my_func")  # No TTL provided
        assert result1 == mock_function
        assert mock_client.projects.functions.get_deployed_environments.call_count == 1

        # Second call within default TTL - should use cache (test lines 152-154)
        mock_time.return_value = 1020.0  # 20 seconds later (within default 30s TTL)
        result2 = await get_deployed_function_async("project-123", "my_func")
        assert result2 == mock_function
        assert mock_client.projects.functions.get_deployed_environments.call_count == 1

        # Clear cache and manually add entry to test race condition inside lock (line 161)
        _deployed_cache.clear()
        key = ("project-123", "my_func")

        # Set up a scenario where another coroutine has filled the cache during lock acquisition
        # Reset call count
        mock_client.projects.functions.get_deployed_environments.reset_mock()

        # Call function - first call will fetch from API
        mock_time.return_value = 2000.0
        result3 = await get_deployed_function_async("project-123", "my_func", ttl=30)
        assert result3 == mock_function

        # Manually add same entry to cache (simulating another coroutine)
        _deployed_cache[key] = (2000.0, mock_function)

        # Call again with force_refresh=False - should find cache entry inside lock (line 161)
        mock_time.return_value = 2010.0  # Within TTL
        result4 = await get_deployed_function_async("project-123", "my_func", ttl=30, force_refresh=False)
        assert result4 == mock_function

        # Test force_refresh=True (should bypass cache)
        result5 = await get_deployed_function_async("project-123", "my_func", ttl=30, force_refresh=True)
        assert result5 == mock_function


@pytest.mark.asyncio
async def test_get_function_by_hash_async_race_condition_2():
    """Test race condition handling in get_function_by_hash_async (covers line 60)."""
    from lilypad._utils.function_cache import get_function_by_hash_async, _hash_async_cache, _hash_async_lock
    from unittest.mock import AsyncMock, patch

    # Clear cache
    _hash_async_cache.clear()

    mock_function = Mock(uuid="test-123", name="test_func")
    key = ("project-123", "hash-abc")

    # Simulate race condition - another coroutine fills cache while waiting for lock
    original_lock_acquire = _hash_async_lock.acquire

    async def mock_acquire():
        await original_lock_acquire()
        # Simulate another coroutine filling the cache
        _hash_async_cache[key] = mock_function

    with (
        patch.object(_hash_async_lock, "acquire", mock_acquire),
        patch("lilypad._utils.function_cache.get_async_client") as mock_get_client,
    ):
        mock_client = Mock()
        mock_client.projects.functions.get_by_hash = AsyncMock()
        mock_get_client.return_value = mock_client

        result = await get_function_by_hash_async("project-123", "hash-abc")

        # Should return cached value without calling API
        assert result == mock_function
        mock_client.projects.functions.get_by_hash.assert_not_called()


@pytest.mark.asyncio
async def test_get_function_by_version_async_race_condition_2():
    """Test race condition handling in get_function_by_version_async (covers line 98)."""
    from lilypad._utils.function_cache import get_function_by_version_async, _version_async_cache, _version_async_lock
    from unittest.mock import AsyncMock, patch

    # Clear cache
    _version_async_cache.clear()

    mock_function = Mock(uuid="test-123", name="test_func", version=1)
    key = ("project-123", "test_func", 1)

    # Simulate race condition
    original_lock_acquire = _version_async_lock.acquire

    async def mock_acquire():
        await original_lock_acquire()
        # Simulate another coroutine filling the cache
        _version_async_cache[key] = mock_function

    with (
        patch.object(_version_async_lock, "acquire", mock_acquire),
        patch("lilypad._utils.function_cache.get_async_client") as mock_get_client,
    ):
        mock_client = Mock()
        mock_client.projects.functions.get_by_version = AsyncMock()
        mock_get_client.return_value = mock_client

        result = await get_function_by_version_async("project-123", "test_func", 1)

        # Should return cached value without calling API
        assert result == mock_function
        mock_client.projects.functions.get_by_version.assert_not_called()


@pytest.mark.asyncio
@patch("lilypad._utils.function_cache.time")
@patch("lilypad._utils.function_cache.get_async_client")
async def test_get_deployed_function_async_not_expired(mock_get_client, mock_time):
    """Test deployed function with non-expired cache entry during race condition (covers line 161)."""
    from lilypad._utils.function_cache import get_deployed_function_async, _deployed_cache, _deployed_async_lock
    from unittest.mock import AsyncMock

    # Clear cache
    _deployed_cache.clear()

    mock_function = Mock(uuid="test-123", name="test_func")
    key = ("project-123", "test_func")

    # Set initial time
    mock_time.return_value = 1000.0

    # Mock client
    mock_client = Mock()
    mock_client.projects.functions.get_deployed_environments = AsyncMock(return_value=mock_function)
    mock_get_client.return_value = mock_client

    # Create a task that will populate the cache while we're waiting for the lock
    async def populate_cache():
        await asyncio.sleep(0.01)  # Small delay to ensure we're in the lock
        _deployed_cache[key] = (995.0, mock_function)

    # Patch the lock to add delay and allow cache population
    original_acquire = _deployed_async_lock.acquire

    async def delayed_acquire():
        await original_acquire()
        # Give time for the other coroutine to populate cache
        await asyncio.sleep(0.02)

    with patch.object(_deployed_async_lock, "acquire", side_effect=delayed_acquire):
        # Start the cache population task
        populate_task = asyncio.create_task(populate_cache())

        # Call the function - it will check cache (miss), acquire lock (delayed),
        # then check cache again (hit with non-expired entry)
        result = await get_deployed_function_async("project-123", "test_func", ttl=30)

        # Wait for populate task to complete
        await populate_task

        # Should return cached value found inside lock (line 161)
        assert result == mock_function
        # API should not be called since we found non-expired entry
        mock_client.projects.functions.get_deployed_environments.assert_not_called()
