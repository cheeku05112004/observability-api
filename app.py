from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
import time
import json
import uuid
from collections import deque
from datetime import datetime, timezone

app = FastAPI()

# Startup time
start_time = time.monotonic()

# Live Prometheus counter
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests"
)

# Store last 1000 logs
logs = deque(maxlen=1000)


# Middleware: count and log every request
@app.middleware("http")
async def observe_requests(request: Request, call_next):

    request_id = str(uuid.uuid4())

    REQUEST_COUNT.inc()

    start = time.monotonic()

    response = await call_next(request)

    log_entry = {
        "level": "INFO",
        "ts": datetime.now(timezone.utc).isoformat(),
        "path": request.url.path,
        "request_id": request_id,
        "method": request.method,
        "status_code": response.status_code,
        "duration_ms": round((time.monotonic() - start) * 1000, 2)
    }

    logs.append(log_entry)

    response.headers["X-Request-ID"] = request_id

    return response


# Work endpoint
@app.get("/work")
async def work(n: int = 1):

    done = max(0, n)

    # Perform K units of work
    result = 0
    for i in range(done):
        result += i

    return {
        "email": "24f2002795@ds.study.iitm.ac.in",
        "done": done
    }


# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics():

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# Health check
@app.get("/healthz")
async def healthz():

    uptime = time.monotonic() - start_time

    return {
        "status": "ok",
        "uptime_s": round(uptime, 3)
    }


# Last N logs
@app.get("/logs/tail")
async def logs_tail(limit: int = 10):

    limit = max(0, min(limit, 1000))

    return list(logs)[-limit:] if limit else []
