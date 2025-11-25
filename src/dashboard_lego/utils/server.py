"""Utility for running Dash applications in background threads for iframe embedding."""

import socket
import threading
from typing import Callable, Dict, Optional

from werkzeug.serving import BaseWSGIServer, make_server

from dashboard_lego.core.page import DashboardPage
from dashboard_lego.utils.logger import get_logger

logger = get_logger(__name__)


# LLM:METADATA
# :hierarchy: [DashboardLego | Utils | Server]
# :relates-to:
#  - motivated_by: "Need generic background server management for embedding Dash apps in other frameworks (e.g. FastHTML)"
#  - implements: "ManagedDashServer, get_or_create_dash_server"
#  - uses: ["werkzeug.serving", "threading"]
# :contract:
#  - pre: "DashboardPage instance provided"
#  - post: "Server running in background thread, accessible via .url"
#  - invariant: "Thread-safe server registry, automatic port finding"
# :complexity: 3
# :decision_cache: "Moved from sales_predictor to core utils for reusability [refactor-001]"
# LLM:END
class ManagedDashServer:
    """Manage Dash server lifecycle for background execution and iframe embedding.

    This class manages a Dash application server running in a background thread,
    allowing it to be embedded in an iframe within FastHTML pages.
    """

    def __init__(
        self,
        dashboard_page: DashboardPage,
        host: str = "127.0.0.1",
        port: Optional[int] = None,
    ):
        """Initialize Dash server manager.

        Args:
            dashboard_page: DashboardPage instance to serve.
            host: Host interface to bind (default: 127.0.0.1).
            port: Port number to bind (default: None, auto-assign available port).
        """
        self._dashboard_page = dashboard_page
        self._host = host
        self._port = port or self._find_free_port()
        self._app = dashboard_page.create_app(suppress_callback_exceptions=True)
        self._server: Optional[BaseWSGIServer] = None
        self._thread: Optional[threading.Thread] = None
        self._ready_event = threading.Event()
        self._shutdown_event = threading.Event()
        self._lock = threading.Lock()

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

    def start(self, on_exit: Optional[Callable[[], None]] = None) -> None:
        """Start dashboard server in background thread.

        Args:
            on_exit: Optional callback invoked when server stops.
        """
        self._setup_server()
        assert self._server is not None

        def _target() -> None:
            self._ready_event.set()
            logger.debug(
                "dash_server_started",
                host=self._host,
                port=self._port,
                title=self._dashboard_page.title,
            )
            try:
                self._server.serve_forever()
            except Exception as exc:
                logger.exception(
                    "dash_server_error",
                    host=self._host,
                    port=self._port,
                    error=str(exc),
                )
            finally:
                logger.debug("dash_server_stopped", host=self._host, port=self._port)
                self._finalize_server()
                if on_exit:
                    on_exit()

        self._thread = threading.Thread(target=_target, daemon=True)
        self._thread.start()

        # Wait for server to be ready
        if not self._ready_event.wait(timeout=2):
            self.shutdown()
            raise RuntimeError(
                "Dashboard server failed to start within readiness timeout"
            )

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
    server_id: str, dashboard_page: DashboardPage, host: str = "127.0.0.1"
) -> ManagedDashServer:
    """Get existing or create new Dash server for given ID.

    Args:
        server_id: Unique identifier for the server (e.g., user_id or session_id).
        dashboard_page: DashboardPage instance to serve.
        host: Host interface to bind.

    Returns:
        ManagedDashServer instance.
    """
    with _registry_lock:
        if server_id in _server_registry:
            server = _server_registry[server_id]
            if server.is_running:
                return server
            # Server stopped, remove from registry
            del _server_registry[server_id]

        # Create new server
        server = ManagedDashServer(dashboard_page, host=host)
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
