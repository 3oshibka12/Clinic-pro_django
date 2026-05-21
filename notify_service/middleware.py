import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from metrics import REQUEST_COUNT, REQUEST_LATENCY

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start
        
        # Обновляем метрики
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response