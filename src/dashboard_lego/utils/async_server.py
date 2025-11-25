"""
Async server integration for dashboard_lego using FastAPI/Starlette.

Provides async web framework integration for embedding dashboards in async applications.

:hierarchy: [DashboardLego | Utils | AsyncServer]
:relates-to:
 - motivated_by: "Support async web frameworks (FastAPI, Starlette) for iframe embedding"
 - implements: "AsyncDashServer, FastAPI integration helpers"
 - uses: ["fastapi", "starlette", "dash"]

:contract:
 - pre: "FastAPI/Starlette available (optional dependency)"
 - post: "Dash app integrated with async web framework"
 - invariant: "Maintains backward compatibility with WSGI server"
"""

from typing import Any, List, Optional

from dashboard_lego.core.page import DashboardPage
from dashboard_lego.utils.logger import get_logger

logger = get_logger(__name__)


def create_async_dash_app(
    dashboard_page: Optional[DashboardPage] = None,
    app: Optional[Any] = None,
    cors_origins: Optional[List[str]] = None,
    allow_iframe: bool = True,
) -> Any:
    """
    Create Dash app configured for async web frameworks.

    Sets up CORS and iframe headers for embedding in FastAPI/Starlette applications.

    :hierarchy: [DashboardLego | Utils | AsyncServer | CreateApp]
    :relates-to:
     - motivated_by: "Integrate Dash app with FastAPI/Starlette"
     - implements: "function: 'create_async_dash_app'"

    :contract:
     - pre: "dashboard_page or app provided"
     - post: "Returns Dash app with CORS/iframe headers configured"

    Args:
        dashboard_page: DashboardPage instance (mutually exclusive with app)
        app: Dash app instance (mutually exclusive with dashboard_page)
        cors_origins: List of allowed CORS origins (default: ["*"])
        allow_iframe: Whether to allow iframe embedding (default: True)

    Returns:
        Dash app instance configured for async frameworks

    Example:
        >>> from fastapi import FastAPI
        >>> from dashboard_lego.utils.async_server import create_async_dash_app
        >>>
        >>> fastapi_app = FastAPI()
        >>> dash_app = create_async_dash_app(dashboard_page=page)
        >>>
        >>> # Mount Dash app on FastAPI
        >>> from starlette.middleware.wsgi import WSGIMiddleware
        >>> fastapi_app.mount("/dashboard", WSGIMiddleware(dash_app.server))
    """
    if dashboard_page is None and app is None:
        raise ValueError("Must provide either dashboard_page or app")
    if dashboard_page is not None and app is not None:
        raise ValueError("Cannot provide both dashboard_page and app")

    # Create or use provided app
    if dashboard_page:
        dash_app = dashboard_page.create_app(suppress_callback_exceptions=True)
    else:
        dash_app = app

    cors_origins = cors_origins or ["*"]

    # Setup CORS and iframe headers (same as ManagedDashServer)
    @dash_app.server.after_request
    def add_headers(response):
        """Add CORS and iframe headers to all responses."""
        # CORS headers
        if "*" in cors_origins:
            response.headers["Access-Control-Allow-Origin"] = "*"
        else:
            response.headers["Access-Control-Allow-Origin"] = (
                cors_origins[0] if cors_origins else "*"
            )

        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, OPTIONS, PUT, DELETE"
        )
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Credentials"] = "true"

        # Iframe embedding headers
        if allow_iframe:
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
            csp = response.headers.get("Content-Security-Policy", "")
            if "frame-ancestors" not in csp:
                if csp:
                    csp += "; frame-ancestors *"
                else:
                    csp = "frame-ancestors *"
                response.headers["Content-Security-Policy"] = csp
        else:
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"

        return response

    # Handle OPTIONS preflight requests
    @dash_app.server.before_request
    def handle_options():
        """Handle CORS preflight OPTIONS requests."""
        try:
            from flask import Response, request

            if request.method == "OPTIONS":
                response = Response()
                response.headers["Access-Control-Allow-Origin"] = (
                    "*"
                    if "*" in cors_origins
                    else (cors_origins[0] if cors_origins else "*")
                )
                response.headers["Access-Control-Allow-Methods"] = (
                    "GET, POST, OPTIONS, PUT, DELETE"
                )
                response.headers["Access-Control-Allow-Headers"] = (
                    "Content-Type, Authorization"
                )
                response.headers["Access-Control-Allow-Credentials"] = "true"
                return response
        except ImportError:
            # Flask not available, skip OPTIONS handling
            pass

    logger.debug(
        f"[create_async_dash_app] Dash app configured | "
        f"cors_origins={cors_origins} | allow_iframe={allow_iframe}"
    )

    return dash_app


class AsyncDashServer:
    """
    Async server wrapper for Dash apps using FastAPI/Starlette.

    Provides async web framework integration for embedding dashboards.

    :hierarchy: [DashboardLego | Utils | AsyncServer | AsyncDashServer]
    :relates-to:
     - motivated_by: "Support async web frameworks for iframe embedding"
     - implements: "class: 'AsyncDashServer'"

    :contract:
     - pre: "FastAPI/Starlette available (optional dependency)"
     - post: "Dash app integrated with async web framework"

    Example:
        >>> from fastapi import FastAPI
        >>> from dashboard_lego.utils.async_server import AsyncDashServer
        >>>
        >>> fastapi_app = FastAPI()
        >>> async_server = AsyncDashServer(dashboard_page=page)
        >>> async_server.mount_on_fastapi(fastapi_app, "/dashboard")
    """

    def __init__(
        self,
        dashboard_page: Optional[DashboardPage] = None,
        app: Optional[Any] = None,
        cors_origins: Optional[List[str]] = None,
        allow_iframe: bool = True,
    ):
        """
        Initialize AsyncDashServer.

        Args:
            dashboard_page: DashboardPage instance (mutually exclusive with app)
            app: Dash app instance (mutually exclusive with dashboard_page)
            cors_origins: List of allowed CORS origins (default: ["*"])
            allow_iframe: Whether to allow iframe embedding (default: True)
        """
        self._dash_app = create_async_dash_app(
            dashboard_page=dashboard_page,
            app=app,
            cors_origins=cors_origins,
            allow_iframe=allow_iframe,
        )
        self.logger = get_logger(__name__, AsyncDashServer)

    def mount_on_fastapi(self, fastapi_app: Any, path: str = "/dashboard") -> None:
        """
        Mount Dash app on FastAPI application.

        Args:
            fastapi_app: FastAPI application instance
            path: Path to mount dashboard (default: "/dashboard")
        """
        try:
            from starlette.middleware.wsgi import WSGIMiddleware

            fastapi_app.mount(path, WSGIMiddleware(self._dash_app.server))
            self.logger.info(f"[AsyncDashServer] Mounted on FastAPI at {path}")
        except ImportError:
            raise ImportError(
                "starlette is required for FastAPI integration. "
                "Install with: pip install starlette"
            )

    @property
    def dash_app(self) -> Any:
        """Get underlying Dash app instance."""
        return self._dash_app
