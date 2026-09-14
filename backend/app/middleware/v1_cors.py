"""Public key-authenticated API CORS, separate from website/account policy."""

from starlette.middleware.cors import CORSMiddleware

EXPOSED_HEADERS = [
    "X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset",
    "X-RateLimit-Requests-Per-Minute", "X-RateLimit-Request-Burst",
    "X-Quota-Bytes-Limit", "X-Quota-Bytes-Remaining",
    "Retry-After", "Location", "Idempotency-Replayed", "Content-Disposition",
]


class V1CORSMiddleware:
    def __init__(self, app):
        self.app = app
        self.public_api = CORSMiddleware(
            app, allow_origins=["*"], allow_credentials=False,
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["X-API-Key", "Authorization", "Content-Type", "Idempotency-Key", "X-Request-ID"],
            expose_headers=EXPOSED_HEADERS,
        )

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("path", "").startswith("/api/v1/"):
            await self.public_api(scope, receive, send)
        else:
            await self.app(scope, receive, send)
