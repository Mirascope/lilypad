"""Test cases for fn_is_async utility."""

import asyncio
import functools
from typing import Awaitable, Coroutine, Any


from lilypad._utils.fn_is_async import fn_is_async


def test_sync_function():
    """Test that regular sync functions return False."""

    def sync_func():
        return 42

    assert fn_is_async(sync_func) is False

    def sync_func_with_args(x, y):
        return x + y

    assert fn_is_async(sync_func_with_args) is False


def test_async_function():
    """Test that async functions return True."""

    async def async_func():
        return 42

    assert fn_is_async(async_func) is True

    async def async_func_with_args(x, y):
        await asyncio.sleep(0)
        return x + y

    assert fn_is_async(async_func_with_args) is True


def test_lambda_functions():
    """Test lambda functions."""

    def sync_lambda(x):
        return x * 2

    assert fn_is_async(sync_lambda) is False

    # Note: Can't create async lambdas directly in Python


def test_wrapped_functions():
    """Test functions wrapped with functools.wraps."""

    # Test wrapped sync function
    def sync_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    @sync_decorator
    def sync_wrapped():
        return 42

    assert fn_is_async(sync_wrapped) is False

    # Test wrapped async function
    def async_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    @async_decorator
    async def async_wrapped():
        return 42

    assert fn_is_async(async_wrapped) is True


def test_nested_wrapped_functions():
    """Test multiply-wrapped functions."""

    def decorator1(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    def decorator2(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    @decorator1
    @decorator2
    async def nested_async():
        return 42

    assert fn_is_async(nested_async) is True

    @decorator1
    @decorator2
    def nested_sync():
        return 42

    assert fn_is_async(nested_sync) is False


def test_class_methods():
    """Test class methods."""

    class TestClass:
        def sync_method(self):
            return 42

        async def async_method(self):
            return 42

        @classmethod
        def sync_classmethod(cls):
            return 42

        @classmethod
        async def async_classmethod(cls):
            return 42

        @staticmethod
        def sync_staticmethod():
            return 42

        @staticmethod
        async def async_staticmethod():
            return 42

    obj = TestClass()

    # Instance methods
    assert fn_is_async(obj.sync_method) is False
    assert fn_is_async(obj.async_method) is True

    # Class methods
    assert fn_is_async(TestClass.sync_classmethod) is False
    assert fn_is_async(TestClass.async_classmethod) is True

    # Static methods
    assert fn_is_async(TestClass.sync_staticmethod) is False
    assert fn_is_async(TestClass.async_staticmethod) is True


def test_coroutine_function():
    """Test with coroutine functions."""

    async def coro_func() -> Coroutine[Any, Any, int]:
        return 42

    assert fn_is_async(coro_func) is True


def test_awaitable_return_type():
    """Test functions that return Awaitable."""

    async def returns_awaitable() -> Awaitable[int]:
        return 42

    assert fn_is_async(returns_awaitable) is True


def test_partial_functions():
    """Test functools.partial functions."""

    async def async_add(x, y):
        return x + y

    def sync_add(x, y):
        return x + y

    # fn_is_async now checks partial.func attribute
    async_partial = functools.partial(async_add, 10)
    sync_partial = functools.partial(sync_add, 10)

    # fn_is_async detects async functions through partial.func
    assert fn_is_async(async_partial) is True
    assert fn_is_async(sync_partial) is False


def test_direct_async_function_detection():
    """Test that async functions are detected directly (line 13)."""

    async def simple_async_func():
        return 42

    # This should trigger line 13 (direct async function detection)
    assert fn_is_async(simple_async_func) is True


def test_wrapped_async_function_detection():
    """Test that wrapped async functions are detected (line 20)."""

    async def original_async():
        return 42

    def wrapper_func():
        return 42

    # Manually set __wrapped__ to test the unwrapping logic
    wrapper_func.__wrapped__ = original_async

    # This should trigger line 20 (wrapped async function detection)
    assert fn_is_async(wrapper_func) is True


def test_callable_objects():
    """Test callable objects."""

    class AsyncCallable:
        async def __call__(self):
            return 42

    class SyncCallable:
        def __call__(self):
            return 42

    async_obj = AsyncCallable()
    sync_obj = SyncCallable()

    # fn_is_async checks if the object itself is a coroutine function,
    # not if its __call__ method is async
    assert fn_is_async(async_obj) is False
    assert fn_is_async(sync_obj) is False
