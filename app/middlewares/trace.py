import uuid

from app.core.logging import current_trace_id


HEADER_NAME = "X-Request-ID"

def _looks_ok(value: str | None) -> bool:
    if not value:
        return False
    if not (16 <= len(value) <= 64):
        return False
    return all(ch.isalnum() or ch in "-_" for ch in value)

class TraceIdASGIMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # HTTP 요청만 처리
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)

        # 헤더에서 X-Request-ID 추출
        incoming = None
        for name, value in scope.get("headers", []):
            if name.lower() == b"x-request-id":
                incoming = value.decode("latin-1")
                break

        trace_id = incoming if _looks_ok(incoming) else uuid.uuid4().hex

        # request.state.trace_id 로 접근 가능하도록 scope.state 에 심기
        state = scope.setdefault("state", {})
        state["trace_id"] = trace_id

        current_trace_id.set(trace_id)

        # 응답 헤더에 X-Request-ID 주입
        async def send_wrapper(message):
            if message.get("type") == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", trace_id.encode("latin-1")))
                message["headers"] = headers
            await send(message)

        # 다음 앱 호출
        return await self.app(scope, receive, send_wrapper)
