from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import PlainTextResponse, Response

from .api import auth
from .core.settings import settings

app = FastAPI(title=settings.APP_NAME)
app.include_router(auth.router, prefix="/auth")


# minimal security headers
@app.middleware("http")
async def headers_mw(request, call_next):
    res: Response = await call_next(request)
    res.headers["X-Content-Type-Options"] = "nosniff"
    res.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    res.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
    return res


REQS = Counter("http_requests", "Requests", ["path", "method", "code"])
LAT = Histogram("http_latency_seconds", "Latency", ["path", "method"])


@app.middleware("http")
async def metrics_mw(request, call_next):
    import time

    start = time.perf_counter()
    res = await call_next(request)
    LAT.labels(request.url.path, request.method).observe(time.perf_counter() - start)
    REQS.labels(request.url.path, request.method, str(res.status_code)).inc()
    return res


@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest())


@app.get("/healthz")
def healthz():
    return {"ok": True}
