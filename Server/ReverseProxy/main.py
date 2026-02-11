import asyncio
import time
from typing import Dict, Tuple

import maplex
import httpx
from fastapi import FastAPI, Request, Response
from more_itertools import bucket

logger = maplex.Logger(__name__)
configFile = maplex.MapleJson("config.json").read("ReverseProxyServer")

if configFile is None:
    logger.warn("config.json not found or ReverseProxyServer section missing, using default settings")
    configFile = {}

# Static configuration values

UPSTREAM_URL = configFile.get("Upstream", "http://pj-mobius-server")
PORT = configFile.get("ListenPort", 8085)
UPSTREAM_FULL_URL = f"{UPSTREAM_URL}:{PORT}"
RATE_LIMIT_PER_MINUTE = configFile.get("MaxRequestPerMinute", 60)
RATE_LIMIT_BURST = configFile.get("Burst", 20)
RATE_LIMIT_TIMEOUT_SECONDS = configFile.get("Timeout", 60)
REQUEST_TIMEOUT_SECONDS = configFile.get("SuspendTimeoutSeconds", 30)
TRUST_X_FORWARDED_FOR = configFile.get("TrustXForwardedFor", False)
MAX_TOKENS_CAPACITY = configFile.get("MaxTokensCapacity", 10000)

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}

logger.info(f"Starting reverse proxy to {UPSTREAM_FULL_URL} with rate limit {RATE_LIMIT_PER_MINUTE}/min burst {RATE_LIMIT_BURST}")

class TokenBucket:

    def __init__(self, rate_per_min: int, burst: int) -> None:
        self.capacity = max(burst, 1)
        self.refill_rate = max(rate_per_min, 1) / 60.0
        self.tokens: Dict[str, Tuple[float, float, bool, int]] = {}
        self.lock = asyncio.Lock()

    async def allow(self, key: str) -> bool:
        '''
        key: Client identifire (e.g., IP address)
        allow checks if a request from the given key (e.g., IP address) is allowed under the token bucket rate limit.
        It refills tokens based on elapsed time and checks if at least one token is available.
        If allowed, it consumes a token and updates the last request time.
        It also performs cleanup of stale entries if the token dictionary grows too large.
        '''

        now = time.monotonic()

        async with self.lock:

            # Get current tokens (Refill rate / Request per minute)

            tokens, last_time, timeOut, rejected = self.tokens.get(key, (self.capacity, now, False, 0))
            elapsed = max(now - last_time, 0.0)
            tokens = min(self.capacity, tokens + elapsed * self.refill_rate)

            if tokens < 1.0 or (timeOut and elapsed < RATE_LIMIT_TIMEOUT_SECONDS):

                # Not enough tokens, reject request

                logger.debug(f"Rate limit exceeded for {key}: tokens={tokens}, elapsed={elapsed:.2f}s, rejected={rejected + 1}")
                self.tokens[key] = (tokens, now + RATE_LIMIT_TIMEOUT_SECONDS * rejected, timeOut, rejected + 1)
                return False

            # Consume a token and update last request time

            tokens -= 1.0
            self.tokens[key] = (tokens, now, False, 0)

            if len(self.tokens) > MAX_TOKENS_CAPACITY:

                logger.warn(f"Token bucket size {len(self.tokens)} exceeds capacity {MAX_TOKENS_CAPACITY}, performing cleanup")
                self._cleanup(now)

            return True
        
    def _cleanup(self, now: float) -> None:

        # Remove entries that haven't been updated for over an hour

        cutoff = now - 3600.0
        stale_keys = [key for key, (_, last, timeout, _) in self.tokens.items() if last < cutoff and not timeout]
        logger.info(f"Cleaning up {len(stale_keys)} stale token entries")

        for key in stale_keys:

            del self.tokens[key]

        if len(self.tokens) > MAX_TOKENS_CAPACITY * 0.7:

            logger.warn(f"Token bucket size {len(self.tokens)} exceeds 70% of capacity, performing deep cleanup")
            self._deepCleanUp(now)

    def _deepCleanUp(self, now: float) -> None:

        # Remove all entries that have timed out

        stale_keys = []

        for key, (_, last, _, rejected) in self.tokens.items():

            # Recalculate cutoff based on the number of rejections

            cutoffSpan = max(RATE_LIMIT_TIMEOUT_SECONDS * rejected, 3600.0)
            cutoff = now - cutoffSpan

            if last < cutoff:

                stale_keys.append(key)

        logger.info(f"Deep cleaning up {len(stale_keys)} token entries that have timed out")

        # Remove stale entries

        for key in stale_keys:

            del self.tokens[key]

        logger.info(f"Token bucket size after cleanup: {len(self.tokens)}")

# Application setup

app = FastAPI()
bucket = TokenBucket(RATE_LIMIT_PER_MINUTE, RATE_LIMIT_BURST)
client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS)
logger.info("Reverse proxy application initialized")

def get_client_ip(request: Request) -> str:

    '''
    Extract the client's IP address from the request.
    '''

    if TRUST_X_FORWARDED_FOR:

        forwarded_for = request.headers.get("x-forwarded-for")

        if forwarded_for:

            # Use the first IP in the X-Forwarded-For header

            return forwarded_for.split(",")[0].strip()

    if request.client:

        return request.client.host

    return "unknown"

# Health check endpoint
@app.get("/health")
async def health_check() -> dict:

    return {"status": "ok"}

# Proxy endpoint
@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def proxy(full_path: str, request: Request) -> Response:

    '''
    Proxy the incoming request to the upstream server,
    applying rate limiting based on client IP.
    '''

    start = time.monotonic()
    client_ip = get_client_ip(request)

    if not await bucket.allow(client_ip):

        # Rate limit exceeded

        logger.warn(f"Rate limit exceeded for {client_ip}")
        return Response(content="Too Many Requests", status_code=429)
    
    # Forward the request to the upstream server

    upstream_url = f"{UPSTREAM_FULL_URL}/{full_path}"
    headers = {k: v for k, v in request.headers.items() if k.lower() not in HOP_BY_HOP_HEADERS}
    headers["x-forwarded-for"] = client_ip
    body = await request.body()

    try:

        upstream_response = await client.request(
            method=request.method,
            url=upstream_url,
            headers=headers,
            content=body,
            params=request.query_params
        )

    except httpx.RequestError as exc:

        logger.error(f"Error forwarding request to upstream: {exc}")
        return Response(content="Bad Gateway", status_code=502)
    
    # Log the request details

    elapsed_ms = (time.monotonic() - start) * 1000.0
    logger.info(f"proxied ip={client_ip} path=/{full_path} status={upstream_response.status_code} time={elapsed_ms:.2f}ms")

    # Build the response to return to the client

    response_headers = {
        k: v for k, v in upstream_response.headers.items() if k.lower() not in HOP_BY_HOP_HEADERS
    }

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=response_headers
    )

# Shutdown event to close the HTTP client
@app.on_event("shutdown")
async def shutdown_event() -> None:

    await client.aclose()
    logger.info("HTTP client closed on shutdown")