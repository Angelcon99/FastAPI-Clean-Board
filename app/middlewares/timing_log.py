import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


logger = logging.getLogger("app.timing")

class TimingLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = None
        status = "N/A"
        try:
            response = await call_next(request)
            status = getattr(response, "status_code", "N/A")
            return response
        except Exception as e:
            status = "EXC"
            logger.exception(
                f"Error while processing {request.method} {request.url.path}: {e}"
            )
            raise
        finally:
            process_time = time.perf_counter() - start_time 
            trace_id = getattr(request.state, "trace_id", None)
            logger.info(
                f"{request.method} {request.url.path} -> {status} in {process_time:.4f}s",
                extra={"trace_id": trace_id}
            )

            if response is not None:
                try:
                    response.headers["X-Process-Time"] = f"{process_time:.4f}"
                except Exception:
                    logger.debug("Failed to set X-Process-Time header", exc_info=True)
