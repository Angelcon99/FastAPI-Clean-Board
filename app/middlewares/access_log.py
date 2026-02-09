import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


access_logger = logging.getLogger("app.access")

class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):        
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:            
            status = getattr(response, "status_code", "N/A") if response else "N/A"
            trace_id = getattr(request.state, "trace_id", "-")

            client = request.client.host if request.client else "-"
            method = request.method
            path = request.url.path
            version = request.scope.get("http_version", "1.1")
            
            access_logger.info(
                f'{client} - "{method} {path} HTTP/{version}" {status}',
                extra={"trace_id": trace_id},
            )
