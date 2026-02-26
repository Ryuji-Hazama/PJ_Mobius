import asyncio
import time
from typing import Dict, Tuple

import maplex
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse

# Logger and configuration setup

logger = maplex.getLogger("reverse-proxy")
configFile = maplex.MapleJson("config.json").read("ReverseProxy")

if configFile is None:
    logger.warn("config.json not found or ReverseProxy section missing, using default settings")
    configFile = {}

# Static configuration values

RATE_LIMIT_PER_MIN = int(configFile.get("RateLimit", {}).get("PerMinute", 120))
RATE_LIMIT_BURST = int(configFile.get("RateLimit", {}).get("Burst", 60))
RATE_LIMIT_TIMEOUT_SECONDS = int(configFile.get("RateLimit", {}).get("TimeoutSeconds", 30))
REQUEST_TIMEOUT_SECONDS = int(configFile.get("RequestTimeoutSeconds", 30))
TRUST_X_FORWARDED_FOR = configFile.get("TrustXForwardedFor", False)
MAX_TOKEN_CAPACITY = int(configFile.get("MaxTokenCapacity", 10000))
BLACKLIST_ENABLED = configFile.get("BlackList", {}).get("Enabled", False)
BLACKLIST_IPS = set(configFile.get("BlackList", {}).get("IPs", []))

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

logger.info(f"Starting reverse proxy with rate limit {RATE_LIMIT_PER_MIN}/min burst {RATE_LIMIT_BURST}")

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

        # Check blacklist

        if BLACKLIST_ENABLED and key in BLACKLIST_IPS:

            logger.warn(f"blacklist_blocked ip={key}")
            return False

        now = time.monotonic()

        async with self.lock:

            # Get current tokens (Refill rate / Request per minute)

            tokens, last, timeOut, rejected = self.tokens.get(key, (self.capacity, now, False, 0))
            elapsed = max(0.0, now - last)
            tokens = min(self.capacity, tokens + elapsed * self.refill_rate)

            if tokens < 1.0 or (timeOut and elapsed < RATE_LIMIT_TIMEOUT_SECONDS):

                # If the request repeats too quickly, reset tokens to avoid starvation

                logger.debug(f"rate_limit_exceeded ip={key} tokens={tokens:.2f} timeOut={timeOut} rejected={rejected}")
                self.tokens[key] = (tokens, now + RATE_LIMIT_TIMEOUT_SECONDS * rejected, True, rejected + 1)
                return False
            
            # Add weight to the request

            self.tokens[key] = (tokens - 1.0, now, False, 0)

            if len(self.tokens) > MAX_TOKEN_CAPACITY:

                # Delete stale entries to prevent memory bloat

                logger.warn(f"Token bucket size {len(self.tokens)} exceeded max capacity {MAX_TOKEN_CAPACITY}, performing cleanup")
                self._cleanup(now)

            return True

    def _cleanup(self, now: float) -> None:

        # Remove entries that haven't been used for over an hour

        cutoff = now - 3600.0
        stale_keys = [key for key, (_, last, timeout, _) in self.tokens.items() if last < cutoff and not timeout]
        logger.info(f"Cleaning up {len(stale_keys)} stale token bucket entries")

        for key in stale_keys:

            del self.tokens[key]

        if len(self.tokens) > MAX_TOKEN_CAPACITY * 0.8:

            # If still over 80% capacity, perform deep cleanup

            logger.warn("Token bucket still over 80%% capacity after cleanup, performing deep cleanup")
            self._deepCleanup(now)

    def _deepCleanup(self, now: float) -> None:

        # Remove all entries that have timed out

        stale_keys = []

        for key, (_, last, _, rejected) in self.tokens.items():

            # Recalculate cutoff based on rejected count

            cutoffSpan = max(RATE_LIMIT_TIMEOUT_SECONDS * rejected, 3600.0)
            cutoff = now - cutoffSpan

            if last < cutoff:

                stale_keys.append(key)

        logger.info(f"Deep cleaning up {len(stale_keys)} timed out token bucket entries")

        # Remove timed out entries

        for key in stale_keys:

            del self.tokens[key]

        logger.info(f"Token bucket size after deep cleanup: {len(self.tokens)}")

# Application setup

bucket = TokenBucket(RATE_LIMIT_PER_MIN, RATE_LIMIT_BURST)
client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS)
app = FastAPI()
logger.info("Reverse proxy application initialized")

def get_client_ip(request: Request) -> str:

    '''
    Get the client's IP address from the request, considering X-Forwarded-For header if trusted.
    '''

    if TRUST_X_FORWARDED_FOR:

        forwarded_for = request.headers.get("x-forwarded-for")

        if forwarded_for:

            return forwarded_for.split(",")[0].strip()
        
    if request.client:

        return request.client.host
    
    return "unknown"

# Health check endpoint
@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}

# Favicon endpoint
@app.get("/favicon_rp.ico")
async def favicon() -> Response:
    try:
        with open("error_pages/favicon.ico", "rb") as f:
            content = f.read()
        return Response(status_code=200, content=content, media_type="image/x-icon")
    except Exception as exc:
        logger.ShowError(exc, "failed_to_load_favicon")
        return Response(status_code=404, content="Not Found")

# Proxy endpoint
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def proxy(request: Request, path: str) -> Response:

    '''
    Proxy endpoint to forward requests to the upstream server.
    Implements rate limiting based on client IP.
    '''

    start = time.monotonic()
    client_ip = get_client_ip(request)

    if not await bucket.allow(client_ip):

        # Rate limit exceeded

        logger.warn(f"rate_limit ip={client_ip} path=/{path}")

        try:

            # Return custom 429 error page if available

            with open("error_pages/429.html", "r") as f:
                content = f.read()

            return HTMLResponse(status_code=429, content=content)
        
        except Exception as exc:

            logger.ShowError(exc, "failed_to_load_429_page")
            return Response(status_code=429, content="Too Many Requests")

    # Determine upstream URL

    domain = request.headers.get("host", "")
    subdomain = domain.split(".")[0]
    upstreams = configFile.get("Upstreams", {})
    primary_upstream = upstreams.get("PrimaryUpstream", None)
    primary_domain = upstreams.get("PrimaryDomain", "")
    subdomain_map = upstreams.get("SubDomainMap", {})

    # Determine which upstream to use based on the host header and subdomain mapping

    if domain == primary_domain:

        upstream_info = primary_upstream

    else:

        upstream_info = subdomain_map.get(subdomain, None)

    if upstream_info is None:

        logger.warn(f"unknown host or subdomain ip={client_ip} host={domain} path=/{path}")
        
        try:

            # Return custom 404 error page if available

            with open("error_pages/404.html", "r") as f:
                content = f.read()

            return HTMLResponse(status_code=404, content=content)

        except Exception as exc:

            logger.ShowError(exc, "failed_to_load_404_page")
            return Response(status_code=404, content="Not Found")
        
    service = upstream_info.get("Service", "atc_listsite")
    port = upstream_info.get("Port", 8080)
    upstream_url = f"http://{service}:{port}"

    # Forward request to upstream server

    upstream_url = f"{upstream_url}/{path}"
    headers = {k: v for k, v in request.headers.items() if k.lower() not in HOP_BY_HOP_HEADERS}
    headers["x-forwarded-for"] = client_ip
    body = await request.body()

    try:

        upstream_response = await client.request(
            request.method,
            upstream_url,
            params=request.query_params,
            headers=headers,
            content=body,
        )

    except httpx.RequestError as exc:

        # Upstream request failed

        logger.error(f"upstream_error ip={client_ip} path=/{path} error={str(exc)}")

        try:

            # Return custom 502 error page if available

            with open("error_pages/502.html", "r") as f:
                content = f.read()

            return HTMLResponse(status_code=502, content=content)
        
        except Exception as excp:

            logger.ShowError(excp, "failed_to_load_502_page")
            return Response(status_code=502, content="Bad Gateway")

    # Log the request details

    elapsed_ms = (time.monotonic() - start) * 1000.0
    logger.info(
        f"request ip={client_ip} method={request.method} path=/{path} status={upstream_response.status_code} duration_ms={elapsed_ms:.2f}"
    )

    # Return the upstream response

    response_headers = {
        k: v for k, v in upstream_response.headers.items() if k.lower() not in HOP_BY_HOP_HEADERS
    }
    return Response(
        status_code=upstream_response.status_code,
        headers=response_headers,
        content=upstream_response.content,
    )


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await client.aclose()
