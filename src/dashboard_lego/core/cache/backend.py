"""
Cache backend abstraction for dashboard_lego.

Provides pluggable cache backends (disk, Redis, in-memory) for DataSource.

:hierarchy: [Core | Cache | Backend]
:relates-to:
 - motivated_by: "Contract 2: Support multiple cache backends including Redis"
 - implements: "CacheBackend protocol with disk/Redis/memory implementations"

:contract:
 - pre: "Backend implements CacheBackend protocol"
 - post: "DataSource can use any backend transparently"
 - invariant: "All backends provide get/set/__contains__ interface"

:complexity: 5
:decision_cache: "Protocol-based design for flexibility and testability"
"""

import hashlib
import hmac
import pickle
from typing import Any, Optional, Protocol


class CacheBackend(Protocol):
    """
    Protocol for cache backends.

    All cache backends must implement this interface for use with DataSource.

    :hierarchy: [Core | Cache | CacheBackend]
    :relates-to:
     - motivated_by: "Pluggable cache backends for flexibility"
     - implements: "protocol: 'CacheBackend'"

    :contract:
     - methods: "__contains__, __getitem__, __setitem__, set"
     - invariant: "Thread-safe operations"

    :complexity: 2
    """

    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache."""
        ...

    def __getitem__(self, key: str) -> Any:
        """Get value from cache."""
        ...

    def __setitem__(self, key: str, value: Any) -> None:
        """Set value in cache."""
        ...

    def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """Set value with optional TTL override."""
        ...


class DiskCacheBackend:
    """
    Disk-based cache backend using diskcache.

    :hierarchy: [Core | Cache | DiskCacheBackend]
    :relates-to:
     - motivated_by: "Backward compatibility with existing diskcache usage"
     - implements: "class: 'DiskCacheBackend'"

    :contract:
     - pre: "directory is valid path or None for temp"
     - post: "Implements CacheBackend protocol"
     - invariant: "Persistent storage on disk"

    :complexity: 2
    """

    def __init__(self, directory: Optional[str] = None, expire: int = 300):
        """
        Initialize disk cache backend.

        Args:
            directory: Directory for cache storage. None for temp directory.
            expire: Time-to-live for cache entries in seconds.
        """
        from diskcache import Cache

        self._cache = Cache(directory=directory, expire=expire)
        self.directory = directory
        self.expire = expire

    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache."""
        return key in self._cache

    def __getitem__(self, key: str) -> Any:
        """Get value from cache."""
        return self._cache[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set value in cache."""
        self._cache[key] = value

    def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """Set value in cache with optional TTL override.

        Args:
            key: Cache key
            value: Value to cache
            expire: Optional TTL override (uses default if None)
        """
        if expire is not None:
            self._cache.set(key, value, expire=expire)
        else:
            self._cache[key] = value

    def __repr__(self) -> str:
        return f"DiskCacheBackend(directory={self.directory!r}, expire={self.expire})"


class RedisCacheBackend:
    """
    Redis-based cache backend with HMAC signature verification.

    :hierarchy: [Core | Cache | RedisCacheBackend]
    :relates-to:
     - motivated_by: "Contract 2: Redis support for distributed caching"
     - implements: "class: 'RedisCacheBackend'"

    :contract:
     - pre: "Redis server accessible at host:port"
     - post: "Implements CacheBackend protocol with HMAC verification"
     - invariant: "Distributed cache across processes/machines"

    :complexity: 5
    """

    # Class-level connection pool for sharing connections
    _connection_pools = {}

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        expire: int = 300,
        password: Optional[str] = None,
        signing_key: Optional[bytes] = None,
        **redis_kwargs,
    ):
        """
        Initialize Redis cache backend with HMAC signing.

        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number
            expire: Time-to-live for cache entries in seconds
            password: Optional Redis password
            signing_key: Optional HMAC signing key (auto-generated if None)
                        Share this key across instances for cache sharing
            **redis_kwargs: Additional arguments passed to redis.Redis()
        """
        try:
            import redis
        except ImportError:
            raise ImportError(
                "Redis support requires 'redis' package. Install with: pip install redis"
            )

        # Use connection pool for efficiency
        pool_key = f"{host}:{port}:{db}"
        if pool_key not in RedisCacheBackend._connection_pools:
            RedisCacheBackend._connection_pools[pool_key] = redis.ConnectionPool(
                host=host, port=port, db=db, password=password, **redis_kwargs
            )

        self._redis = redis.Redis(
            connection_pool=RedisCacheBackend._connection_pools[pool_key]
        )
        self.expire = expire
        self.host = host
        self.port = port
        self.db = db

        # HMAC signing key for security (prevents RCE from compromised Redis)
        if signing_key is None:
            # Generate random key - WARNING: won't match across process restarts
            # For production, provide a shared signing_key
            import secrets

            signing_key = secrets.token_bytes(32)
        self._signing_key = signing_key

    def _sign_data(self, data: bytes) -> bytes:
        """Add HMAC signature to data."""
        signature = hmac.new(self._signing_key, data, hashlib.sha256).digest()
        return signature + data

    def _verify_data(self, signed_data: bytes) -> bytes:
        """Verify and extract data from signed blob."""
        if len(signed_data) < 32:
            raise ValueError("Invalid signed data: too short")

        signature = signed_data[:32]
        data = signed_data[32:]

        expected_sig = hmac.new(self._signing_key, data, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected_sig):
            raise ValueError("Invalid HMAC signature - data may be tampered")

        return data

    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache."""
        return self._redis.exists(key) > 0

    def __getitem__(self, key: str) -> Any:
        """Get value from cache with HMAC verification."""
        value = self._redis.get(key)
        if value is None:
            raise KeyError(key)

        try:
            # Verify HMAC signature before unpickling (prevents RCE)
            verified_data = self._verify_data(value)
            return pickle.loads(verified_data)
        except (ValueError, pickle.UnpicklingError) as e:
            # Signature verification failed or corrupted data
            raise ValueError(f"Cache data verification failed for key {key}: {e}")

    def __setitem__(self, key: str, value: Any) -> None:
        """Set value in cache with HMAC signing and expiration."""
        serialized = pickle.dumps(value)
        # Sign the data to prevent tampering
        signed_data = self._sign_data(serialized)
        self._redis.setex(key, self.expire, signed_data)

    def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """Set value in cache with optional TTL override.

        Args:
            key: Cache key
            value: Value to cache
            expire: Optional TTL override (uses default if None)
        """
        serialized = pickle.dumps(value)
        signed_data = self._sign_data(serialized)
        ttl = expire if expire is not None else self.expire
        self._redis.setex(key, ttl, signed_data)

    def __repr__(self) -> str:
        return f"RedisCacheBackend(host={self.host!r}, port={self.port}, db={self.db}, expire={self.expire})"


class InMemoryCacheBackend:
    """
    In-memory cache backend using dict.

    :hierarchy: [Core | Cache | InMemoryCacheBackend]
    :relates-to:
     - motivated_by: "Simple in-memory cache for testing and development"
     - implements: "class: 'InMemoryCacheBackend'"

    :contract:
     - pre: "No external dependencies"
     - post: "Implements CacheBackend protocol"
     - invariant: "Cache lost on process restart; TTL NOT enforced"

    :complexity: 1

    Warning:
        TTL (expire parameter) is accepted for API compatibility but NOT enforced.
        All entries remain in cache until process restart or explicit clearing.
    """

    def __init__(self, expire: int = 300):
        """
        Initialize in-memory cache backend.

        Args:
            expire: Time-to-live for cache entries (NOT enforced, for API compatibility only)
        """
        self._cache: dict = {}
        self.expire = expire

    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache."""
        return key in self._cache

    def __getitem__(self, key: str) -> Any:
        """Get value from cache."""
        return self._cache[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set value in cache (TTL not enforced)."""
        self._cache[key] = value

    def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """Set value in cache (TTL not enforced in memory backend).

        Args:
            key: Cache key
            value: Value to cache
            expire: Ignored (for API compatibility only)

        Warning:
            In-memory backend does not support TTL. All entries persist until
            process restart regardless of expire parameter.
        """
        self._cache[key] = value

    def __repr__(self) -> str:
        return f"InMemoryCacheBackend(size={len(self._cache)}, expire={self.expire})"
