"""
Finance Tracker API — application entry point.

Responsibilities:
  - Create the FastAPI application with metadata
  - Register global exception handlers
  - Mount all routers
  - Create DB tables on startup
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from database.connection import Base, engine
from routes.analytics import router as analytics_router
from routes.transactions import router as transactions_router
from routes.auth import router as auth_router
from routes.export import router as export_router


# ── Lifespan: initialise DB tables ────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all tables on startup (idempotent — safe to call multiple times)."""
    Base.metadata.create_all(bind=engine)
    yield


# ── Application factory ───────────────────────────────────────────────────────

app = FastAPI(
    title="Finance Tracker API",
    description=(
        "A clean, production-grade REST API for tracking personal or business "
        "finances. Supports transactions, filtering, analytics, CSV export, and "
        "role-based access control via Token authentication."
    ),
    version="1.0.0",
    contact={
        "name": "Finance Tracker",
        "url": "https://github.com/your-org/finance-tracker",
    },
    license_info={"name": "MIT"},
    lifespan=lifespan,
)


# ── Global exception handlers ─────────────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Return a structured 422 response for Pydantic / query-parameter validation errors.
    Makes error messages easier to consume from client code.
    """
    errors = [
        {
            "field": " → ".join(str(loc) for loc in err["loc"]),
            "message": err["msg"],
            "type": err["type"],
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"success": False, "error": "Validation failed", "details": errors},
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Standardize manually raised standard HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": str(exc.detail)},
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """
    Catch unexpected database errors and return a safe 500 response.
    The raw DB error is not exposed to the client.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "error": "An internal database error occurred. Please try again later."},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all for any unhandled exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "error": "An unexpected error occurred."},
    )


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(transactions_router)
app.include_router(analytics_router)
app.include_router(export_router)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"], summary="API health check")
def health_check():
    """Returns 200 OK when the service is running."""
    return {"success": True, "data": {"status": "ok", "version": app.version}, "message": "Service is healthy"}
