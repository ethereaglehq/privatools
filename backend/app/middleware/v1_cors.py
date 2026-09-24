"""Public key-authenticated API CORS, separate from website/account policy."""

from starlette.middleware.cors import CORSMiddleware

from .cors import SITE_EXPOSED_HEADERS

# The same handlers answer /api/v1, so its answers carry the headers the
# site's pages read (the file name, Redact's report...) as well as its own.
EXPOSED_HEADERS = list(dict.fromkeys([
    "X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset",
    "X-RateLimit-Requests-Per-Minute", "X-RateLimit-Request-Burst",
    "X-Quota-Bytes-Limit", "X-Quota-Bytes-Remaining",
    "Retry-After", "Location", "Idempotency-Replayed", "Content-Disposition",
    *SITE_EXPOSED_HEADERS,
]))

PUBLIC_API_CORS = dict(
    allow_origins=["*"], allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["X-API-Key", "Authorization", "Content-Type", "Idempotency-Key", "X-Request-ID"],
    expose_headers=EXPOSED_HEADERS,
)


def public_api_cors(app) -> CORSMiddleware:
    """The public API's CORS layer around `app`."""
    return CORSMiddleware(app, **PUBLIC_API_CORS)


class V1CORSMiddleware:
    def __init__(self, app):
        self.app = app
        self.public_api = public_api_cors(app)

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("path", "").startswith("/api/v1/"):
            await self.public_api(scope, receive, send)
        else:
            await self.app(scope, receive, send)
