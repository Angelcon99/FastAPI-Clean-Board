import logging
import traceback
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .types import BaseAppException    
from app.schemas.error import ErrorResponse


logger = logging.getLogger(__name__)

def _make_error_response(exc: BaseAppException, status_code: int, trace_id: str | None = None):
    body = ErrorResponse(
        code=exc.code,
        message=exc.message,
        details=getattr(exc, "details", None),
        trace_id=trace_id,
    ).model_dump()

    headers = getattr(exc, "headers", None)

    return JSONResponse(
        status_code=status_code,
        content=body,
        headers=headers
    )

async def _unknown_exception_handler(request: Request, exc: Exception):    
    trace_id = getattr(request.state, "trace_id", None)

    # 로그에 스택 트레이스 남기기
    logger.error(
        f"[UNHANDLED_EXCEPTION] {type(exc).__name__}: {exc}\n"
        f"Trace ID: {trace_id}\n"
        f"Path: {request.url.path}\n"
        f"Traceback:\n{''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))}"
    )

    # 클라이언트로는 민감한 내부 정보는 보내지 않음
    base = BaseAppException(
        message="An unexpected error occurred. Please try again later.",
        code="UNKNOWN_ERROR",
        details=None,
    )

    body = ErrorResponse(
        code=base.code,
        message=base.message,
        details=None,
        trace_id=trace_id,
    ).model_dump()

    return JSONResponse(status_code=500, content=body)


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(BaseAppException)
    async def base_exception_handler(request: Request, exc: BaseAppException):
        return _make_error_response(exc, exc.status_code, getattr(request.state, "trace_id", None))    

    @app.exception_handler(HTTPException)
    async def http_exc_handler(request: Request, exc: HTTPException):
        base = BaseAppException(
            message=exc.detail if isinstance(exc.detail, str) else "HTTP error",
            code="HTTP_ERROR",
            status_code=exc.status_code,
            headers=exc.headers
            )
        return _make_error_response(base, exc.status_code, getattr(request.state, "trace_id", None))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        base = BaseAppException(
            message="Input validation failed.",
            code="VALIDATION_ERROR",
            details=exc.errors(),
            status_code=422
        )
        return _make_error_response(base, 422, getattr(request.state, "trace_id", None))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return await _unknown_exception_handler(request, exc)
