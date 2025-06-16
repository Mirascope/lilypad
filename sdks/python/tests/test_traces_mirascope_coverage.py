"""Tests for mirascope-related coverage in traces.py."""

import asyncio
from unittest.mock import Mock, patch, MagicMock
import pytest
from src.lilypad.traces import trace
from src.lilypad.exceptions import RemoteFunctionError


def test_trace_decorator_sync_mirascope_middleware_creation():
    """Test that mirascope middleware is created for mirascope calls - covers lines 956-966."""
    # Create a function with __mirascope_call__ attribute
    def mirascope_function(arg1: str) -> str:
        return f"Result: {arg1}"
    
    # Add __mirascope_call__ attribute to make it a mirascope call
    mirascope_function.__mirascope_call__ = True
    
    with patch("src.lilypad.traces.create_mirascope_middleware") as mock_middleware:
        # Create decorated function
        decorated = trace(name="test_mirascope")(mirascope_function)
        
        # Call the function - this should trigger middleware creation
        try:
            decorated("test")
        except:
            # We don't care about the actual execution, just that middleware was created
            pass
        
        # Verify middleware was created
        assert mock_middleware.called


@pytest.mark.asyncio
async def test_trace_decorator_async_mirascope_middleware_creation():
    """Test that mirascope middleware is created for async mirascope calls - covers lines 787-796."""
    # Create an async function with __mirascope_call__ attribute
    async def mirascope_function_async(arg1: str) -> str:
        return f"Result: {arg1}"
    
    # Add __mirascope_call__ attribute to make it a mirascope call
    mirascope_function_async.__mirascope_call__ = True
    
    with patch("src.lilypad.traces.create_mirascope_middleware") as mock_middleware:
        # Create decorated function
        decorated = trace(name="test_mirascope_async")(mirascope_function_async)
        
        # Call the function - this should trigger middleware creation
        try:
            await decorated("test")
        except:
            # We don't care about the actual execution, just that middleware was created
            pass
        
        # Verify middleware was created
        assert mock_middleware.called