from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from backend.app.middleware.request_context import request_context_middleware
from backend.app.middleware.security_headers import security_headers_middleware
from backend.app.routes import admin_panel_routes, admin_routes, auth_routes, connected_accounts_routes, dashboard_routes, deployment_routes, domain_routes, job_routes, notification_routes, platform_routes, project_routes, repository_analysis_routes, repository_routes
from backend.core.config import get_settings
from backend.core.exceptions import YGITError, unhandled_exception_handler, validation_error_handler, ygit_error_handler
from backend.core.logging import configure_logging
from backend.engines.auth_engine.public import auth_service

def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(title="YGIT API", version=settings.app_version, debug=settings.debug, docs_url="/docs", redoc_url="/redoc", openapi_url=f"{settings.api_prefix}/openapi.json")
    auth_service.configure_app_state(app)
    app.middleware("http")(request_context_middleware)
    app.middleware("http")(security_headers_middleware)
    app.add_exception_handler(YGITError, ygit_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    prefix = settings.api_prefix
    app.include_router(dashboard_routes.router)
    app.include_router(admin_panel_routes.router)
    for router in [auth_routes.router, auth_routes.me_router, platform_routes.router, project_routes.router, repository_routes.router, repository_analysis_routes.router, connected_accounts_routes.router, domain_routes.router, deployment_routes.router, job_routes.router, notification_routes.router, admin_routes.router]:
        app.include_router(router, prefix=prefix)
    return app

app = create_app()
