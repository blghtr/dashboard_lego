"""Utility for running Dash applications in background threads for iframe embedding."""

import socket
import threading
from typing import Any, Callable, Dict, Optional

from werkzeug.serving import BaseWSGIServer, make_server

from dashboard_lego.core.page import DashboardPage
from dashboard_lego.utils.logger import get_logger

logger = get_logger(__name__)


# LLM:METADATA
# :hierarchy: [DashboardLego | Utils | Server]
# :relates-to:
#  - motivated_by: "Need generic server management for embedding Dash apps in other frameworks (e.g. FastHTML) and IPython magics, supporting both DashboardPage and direct Dash app instances"
#  - implements: "ManagedDashServer, get_or_create_dash_server"
#  - uses: ["werkzeug.serving", "threading"]
# :contract:
#  - pre: "DashboardPage instance OR Dash app provided"
#  - post: "Server running in background or foreground thread, accessible via .url"
#  - invariant: "Thread-safe server registry, automatic port finding, supports both blocking and non-blocking execution"
# :complexity: 4
# :decision_cache: "Extended to accept DashboardPage or Dash app for reuse in IPython magics, added run_blocking() for foreground execution [refactor-002]"
# LLM:END
class ManagedDashServer:
    """Manage Dash server lifecycle for foreground and background execution.

    This class manages a Dash application server running in either a foreground
    (blocking) or background (non-blocking) thread, supporting both DashboardPage
    instances and direct Dash app instances.
    """

    def __init__(
        self,
        dashboard_page: Optional[DashboardPage] = None,
        app: Optional[Any] = None,
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        title: Optional[str] = None,
        cors_origins: Optional[list[str]] = None,
        allow_iframe: bool = True,
    ):
        """Initialize Dash server manager.

        Args:
            dashboard_page: DashboardPage instance to serve (mutually exclusive with app).
            app: Dash application instance to serve (mutually exclusive with dashboard_page).
            host: Host interface to bind (default: 127.0.0.1).
            port: Port number to bind (default: None, auto-assign available port).
            title: Human-readable dashboard title for logging (default: from dashboard_page or "Dashboard").
            cors_origins: List of allowed CORS origins (default: None, allows all with "*").
            allow_iframe: Whether to allow iframe embedding (default: True).
        """
        if dashboard_page is None and app is None:
            raise ValueError("Must provide either dashboard_page or app")
        if dashboard_page is not None and app is not None:
            raise ValueError("Cannot provide both dashboard_page and app")

        self._dashboard_page = dashboard_page
        self._host = host
        self._port = port or self._find_free_port()
        self._title = title or (dashboard_page.title if dashboard_page else "Dashboard")
        self._cors_origins = cors_origins or ["*"]
        self._allow_iframe = allow_iframe

        # Create or use provided app
        if dashboard_page:
            self._app = dashboard_page.create_app(suppress_callback_exceptions=True)
        else:
            self._app = app

        # Setup CORS and iframe headers
        self._setup_cors_and_iframe()

        self._server: Optional[BaseWSGIServer] = None
        self._thread: Optional[threading.Thread] = None
        self._ready_event = threading.Event()
        self._shutdown_event = threading.Event()
        self._lock = threading.Lock()

    def _setup_cors_and_iframe(self) -> None:
        """Setup CORS headers and iframe embedding support."""

        @self._app.server.after_request
        def add_headers(response):
            """Add CORS and iframe headers to all responses."""
            # CORS headers
            if "*" in self._cors_origins:
                response.headers["Access-Control-Allow-Origin"] = "*"
            else:
                # In production, you'd check the Origin header and set accordingly
                # For simplicity, allow first origin or use * for development
                response.headers["Access-Control-Allow-Origin"] = (
                    self._cors_origins[0] if self._cors_origins else "*"
                )

            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, OPTIONS, PUT, DELETE"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization"
            )
            response.headers["Access-Control-Allow-Credentials"] = "true"

            # Iframe embedding headers
            if self._allow_iframe:
                # Allow iframe embedding (remove X-Frame-Options or set to SAMEORIGIN)
                # Use Content-Security-Policy for modern browsers
                response.headers["X-Frame-Options"] = "SAMEORIGIN"
                # CSP frame-ancestors allows embedding
                csp = response.headers.get("Content-Security-Policy", "")
                if "frame-ancestors" not in csp:
                    if csp:
                        csp += "; frame-ancestors *"
                    else:
                        csp = "frame-ancestors *"
                    response.headers["Content-Security-Policy"] = csp
            else:
                # Block iframe embedding
                response.headers["X-Frame-Options"] = "DENY"
                response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"

            return response

        # Handle OPTIONS preflight requests
        @self._app.server.before_request
        def handle_options():
            """Handle CORS preflight OPTIONS requests."""
            from flask import request

            if request.method == "OPTIONS":
                from flask import Response

                response = Response()
                response.headers["Access-Control-Allow-Origin"] = (
                    "*"
                    if "*" in self._cors_origins
                    else (self._cors_origins[0] if self._cors_origins else "*")
                )
                response.headers["Access-Control-Allow-Methods"] = (
                    "GET, POST, OPTIONS, PUT, DELETE"
                )
                response.headers["Access-Control-Allow-Headers"] = (
                    "Content-Type, Authorization"
                )
                response.headers["Access-Control-Allow-Credentials"] = "true"
                return response

        logger.debug(
            f"[ManagedDashServer] CORS and iframe headers configured | "
            f"cors_origins={self._cors_origins} | allow_iframe={self._allow_iframe}"
        )

    @staticmethod
    def _find_free_port() -> int:
        """Find an available port for the server."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port

    def _setup_server(self) -> None:
        """Construct underlying Werkzeug server."""
        if self._server is not None:
            raise RuntimeError("Server already initialized")

        self._ready_event.clear()
        self._shutdown_event.clear()

        # Align with previous behaviour: debug tooling enabled without hot reload
        if hasattr(self._app, "enable_dev_tools"):
            self._app.enable_dev_tools(debug=True, dev_tools_hot_reload=False)

        # Create WSGI server
        server = make_server(self._host, self._port, self._app.server, threaded=True)
        server.timeout = 1
        server.shutdown_signal = False
        self._server = server

    def _finalize_server(self) -> None:
        """Tear down server resources and signal shutdown."""
        with self._lock:
            server = self._server
            if server is None:
                self._shutdown_event.set()
                return

            try:
                server.server_close()
            finally:
                self._server = None
                self._shutdown_event.set()

    def run_blocking(self) -> None:
        """Serve dashboard in the current thread until interrupted or shutdown."""
        self._setup_server()
        assert self._server is not None

        self._ready_event.set()
        logger.debug(
            "[ManagedDashServer] ENTER run_blocking | title=%s | port=%s",
            self._title,
            self._port,
        )
        try:
            self._server.serve_forever()
        finally:
            logger.debug(
                "[ManagedDashServer] EXIT run_blocking | title=%s | port=%s",
                self._title,
                self._port,
            )

    def run_background(self, on_exit: Optional[Callable[[], None]] = None) -> None:
        """Run dashboard in background thread.

        Args:
            on_exit: Optional callback invoked when server stops.
        """
        self._setup_server()
        assert self._server is not None

        def _target() -> None:
            self._ready_event.set()
            logger.debug(
                "[ManagedDashServer] ENTER run_background | title=%s | port=%s",
                self._title,
                self._port,
            )
            try:
                self._server.serve_forever()
            except Exception as exc:
                logger.exception(
                    "[ManagedDashServer] Background server error | title=%s | port=%s | error=%s",
                    self._title,
                    self._port,
                    exc,
                )
            finally:
                logger.debug(
                    "[ManagedDashServer] EXIT run_background | title=%s | port=%s",
                    self._title,
                    self._port,
                )
                self._finalize_server()
                if on_exit:
                    on_exit()

        self._thread = threading.Thread(target=_target, daemon=True)
        self._thread.start()

        # Wait for server to be ready
        if not self._ready_event.wait(timeout=2):
            self.shutdown()
            raise RuntimeError(
                f"Dashboard '{self._title}' failed to start within readiness timeout"
            )

    def start(self, on_exit: Optional[Callable[[], None]] = None) -> None:
        """Start dashboard server in background thread (alias for run_background).

        Args:
            on_exit: Optional callback invoked when server stops.
        """
        self.run_background(on_exit=on_exit)

    def shutdown(self) -> None:
        """Signal server to stop and release resources."""
        with self._lock:
            server = self._server
        if server is None:
            self._shutdown_event.set()
            return

        server.shutdown_signal = True

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self._finalize_server()
        self._thread = None

    def wait_until_ready(self, timeout: Optional[float] = None) -> bool:
        """Wait until server is ready to accept requests.

        Args:
            timeout: Maximum time to wait in seconds.

        Returns:
            True if server is ready, False if timeout.
        """
        return self._ready_event.wait(timeout=timeout)

    @property
    def url(self) -> str:
        """Get URL for accessing the dashboard."""
        return f"http://{self._host}:{self._port}/"

    @property
    def port(self) -> int:
        """Get port number."""
        return self._port

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._thread is not None and self._thread.is_alive()


# Global registry for managing multiple Dash servers
_server_registry: Dict[str, ManagedDashServer] = {}
_registry_lock = threading.Lock()


def get_or_create_dash_server(
    server_id: str,
    dashboard_page: Optional[DashboardPage] = None,
    app: Optional[Any] = None,
    host: str = "127.0.0.1",
    title: Optional[str] = None,
    cors_origins: Optional[list[str]] = None,
    allow_iframe: bool = True,
) -> ManagedDashServer:
    """Get existing or create new Dash server for given ID.

    Supports both old API (positional dashboard_page) and new API (named parameters).

    Args:
        server_id: Unique identifier for the server (e.g., user_id or session_id).
        dashboard_page: DashboardPage instance to serve (mutually exclusive with app).
            Can be passed as positional argument for backward compatibility:
            get_or_create_dash_server(server_id, dashboard_page)
        app: Dash application instance to serve (mutually exclusive with dashboard_page).
        host: Host interface to bind.
        title: Human-readable dashboard title for logging.

    Returns:
        ManagedDashServer instance.

    Examples:
        >>> # Old API (backward compatible)
        >>> server = get_or_create_dash_server("user_123", dashboard_page)
        >>> # New API
        >>> server = get_or_create_dash_server("user_123", dashboard_page=dashboard_page, title="My Dashboard")
        >>> server = get_or_create_dash_server("user_123", app=app, title="My Dashboard")
    """
    with _registry_lock:
        if server_id in _server_registry:
            server = _server_registry[server_id]
            if server.is_running:
                return server
            # Server stopped, remove from registry
            del _server_registry[server_id]

        # Create new server
        server = ManagedDashServer(
            dashboard_page=dashboard_page,
            app=app,
            host=host,
            title=title,
            cors_origins=cors_origins,
            allow_iframe=allow_iframe,
        )
        server.start()
        _server_registry[server_id] = server
        return server


def shutdown_dash_server(server_id: str) -> None:
    """Shutdown and remove Dash server from registry.

    Args:
        server_id: Unique identifier for the server.
    """
    with _registry_lock:
        if server_id in _server_registry:
            server = _server_registry[server_id]
            server.shutdown()
            del _server_registry[server_id]
