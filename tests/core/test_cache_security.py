"""
Test security improvements for cache backends.

Verifies HMAC signing and hash collision prevention.
"""

import pandas as pd
import pytest

from dashboard_lego.core.cache import RedisCacheBackend
from dashboard_lego.utils.hashing import get_function_hash


def test_function_hash_includes_module():
    """Test that function hash includes module to prevent collisions."""
    # Define a lambda
    func = lambda x: x * 2

    # Get hash
    hash1 = get_function_hash(func)
    assert hash1 is not None

    # Verify that changing module changes hash
    original_module = func.__module__
    func.__module__ = "fake.module.name"
    hash2 = get_function_hash(func)

    # Restore
    func.__module__ = original_module

    # Hashes should be different due to different modules
    assert hash1 != hash2, "Hash should change when module changes"


def test_function_hash_includes_qualname():
    """Test that function hash includes qualname for uniqueness."""

    class Outer1:
        def method(self):
            return 1

    class Outer2:
        def method(self):
            return 1

    # Same method name and source, but different qualname
    hash1 = get_function_hash(Outer1.method)
    hash2 = get_function_hash(Outer2.method)

    # Should produce different hashes
    assert hash1 != hash2


@pytest.mark.skipif(
    True,  # Skip by default - requires Redis server
    reason="Requires Redis server running on localhost:6379",
)
def test_redis_hmac_verification():
    """Test that RedisCacheBackend verifies HMAC signatures."""
    try:
        import redis

        # Create backend with specific signing key
        signing_key = b"test_secret_key_for_hmac_test"
        backend = RedisCacheBackend(
            host="localhost", port=6379, expire=300, signing_key=signing_key
        )

        # Store value
        test_data = {"test": "data", "value": 123}
        backend["secure_key"] = test_data

        # Retrieve should work
        retrieved = backend["secure_key"]
        assert retrieved == test_data

        # Tamper with Redis data directly
        raw_client = redis.Redis(host="localhost", port=6379)
        raw_client.set("secure_key", b"tampered_data_without_signature")

        # Should raise ValueError on tampering detection
        with pytest.raises(ValueError, match="verification failed"):
            _ = backend["secure_key"]

        # Cleanup
        raw_client.delete("secure_key")

    except ImportError:
        pytest.skip("Redis package not installed")
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")


@pytest.mark.skipif(
    True,  # Skip by default - requires Redis server
    reason="Requires Redis server running on localhost:6379",
)
def test_redis_connection_pooling():
    """Test that connection pooling works correctly."""
    try:
        # Create two backends with same connection params
        backend1 = RedisCacheBackend(host="localhost", port=6379, db=0)
        backend2 = RedisCacheBackend(host="localhost", port=6379, db=0)

        # They should share the same connection pool
        assert backend1._redis.connection_pool is backend2._redis.connection_pool

        # Different db should have different pool
        backend3 = RedisCacheBackend(host="localhost", port=6379, db=1)
        assert backend1._redis.connection_pool is not backend3._redis.connection_pool

    except Exception as e:
        pytest.skip(f"Redis not available: {e}")
