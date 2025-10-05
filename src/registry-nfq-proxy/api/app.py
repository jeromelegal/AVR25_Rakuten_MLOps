import os
import re
import asyncio
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import httpx

from api.middleware.logging import LoggingMiddleware
from api.utils import (
    skopeo_inspect_digest,
    copy_to_local_digest,
    copy_to_local_tag,
    local_has_manifest,
    REG_LOCAL_BASE_URL,
)

LISTEN_PORT = int(os.getenv("LISTEN_PORT", "8000"))
MAX_CONCURRENT_COPIES = int(os.getenv("MAX_CONCURRENT_COPIES", "4"))

# Auto repair config
AUTO_REPAIR_ON_BLOB_ERRORS = os.getenv("AUTO_REPAIR_ON_BLOB_ERRORS", "true").lower() in ("1", "true", "yes")
REPAIR_THROTTLE_SECONDS = int(os.getenv("REPAIR_THROTTLE_SECONDS", "30"))

ensure_lock = asyncio.Lock()
inflight: dict[str, asyncio.Lock] = {}
pending: set[str] = set()
last_errors: dict[str, str] = {}
sem = asyncio.Semaphore(MAX_CONCURRENT_COPIES)

# throttle: repo -> last repair timestamp
_last_repair: dict[str, float] = {}
_repair_lock = asyncio.Lock()

app = FastAPI(title="registry-nfq-proxy", version="1.2.0")
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

METRICS = {"requests_total": 0, "ensures": 0, "ensures_hit": 0, "ensures_miss": 0, "errors": 0, "repairs": 0}

_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailer", "transfer-encoding", "upgrade", "host",
}
def _filter_headers(h: dict) -> dict:
    return {k: v for k, v in h.items() if k.lower() not in _HOP}

_MANIFEST_ACCEPT = (
    "application/vnd.docker.distribution.manifest.v2+json,"
    "application/vnd.docker.distribution.manifest.list.v2+json,"
    "application/vnd.oci.image.index.v1+json,"
    "application/vnd.oci.image.manifest.v1+json,"
    "application/json"
)

def parse_manifest_path(path: str):
    m = re.match(r"^/v2/([^/]+)/(.+)/manifests/([^/]+)$", path)
    return m.groups() if m else None

def parse_blob_path(path: str):
    m = re.match(r"^/v2/([^/]+)/(.+)/blobs/(sha256:[0-9a-f]{64})$", path)
    return m.groups() if m else None

async def _head_local_manifest_digest(reg: str, name: str, ref: str) -> Optional[str]:
    url = f"{REG_LOCAL_BASE_URL}/v2/{reg}/{name}/manifests/{ref}"
    async with httpx.AsyncClient(timeout=None) as client:
        r = await client.head(url, headers={"Accept": _MANIFEST_ACCEPT})
    if r.status_code == 200:
        dcd = r.headers.get("Docker-Content-Digest")
        if dcd and dcd.startswith("sha256:"):
            return dcd
    return None

async def _list_local_tags(reg: str, name: str) -> list[str]:
    # GET /v2/<name>/tags/list
    url = f"{REG_LOCAL_BASE_URL}/v2/{reg}/{name}/tags/list"
    async with httpx.AsyncClient(timeout=None) as client:
        r = await client.get(url)
    if r.status_code != 200:
        return []
    data = r.json()
    return (data.get("tags") or []) if isinstance(data, dict) else []

async def _delete_local_manifest_by_digest(reg: str, name: str, digest: str) -> bool:
    # DELETE /v2/<name>/manifests/<digest>
    url = f"{REG_LOCAL_BASE_URL}/v2/{reg}/{name}/manifests/{digest}"
    async with httpx.AsyncClient(timeout=None) as client:
        r = await client.delete(url)
    # 202 Accepted attendu si delete activé
    return r.status_code in (202, 200)

async def _repair_repo(reg: str, name: str) -> bool:
    """
    Nettoie le repo local en supprimant les manifests existants (tous les tags).
    Requiert REGISTRY_STORAGE_DELETE_ENABLED=true côté internal-registry.
    Throttle pour éviter les tempêtes.
    """
    import time
    key = f"{reg}/{name}"
    async with _repair_lock:
        now = time.time()
        if now - _last_repair.get(key, 0) < REPAIR_THROTTLE_SECONDS:
            return False  # trop tôt, pas de nouveau cleanup
        _last_repair[key] = now

    tags = await _list_local_tags(reg, name)
    deleted_any = False
    for t in tags:
        dcd = await _head_local_manifest_digest(reg, name, t)
        if dcd:
            ok = await _delete_local_manifest_by_digest(reg, name, dcd)
            deleted_any = deleted_any or ok

    if deleted_any:
        METRICS["repairs"] += 1
    return deleted_any

async def ensure_local(reg: str, name: str, ref: str) -> str:
    if ref.startswith("sha256:"):
        key = f"{reg}/{name}@{ref}"
        async with ensure_lock:
            inflight.setdefault(key, asyncio.Lock())
        async with inflight[key]:
            if await local_has_manifest(reg, name, ref):
                METRICS["ensures_hit"] += 1
                return ref
            METRICS["ensures_miss"] += 1
            async with sem:
                await asyncio.to_thread(copy_to_local_digest, reg, name, ref)
            return ref

    local_d = await _head_local_manifest_digest(reg, name, ref)
    if local_d:
        METRICS["ensures_hit"] += 1
        return local_d

    ext_digest = skopeo_inspect_digest(f"{reg}/{name}:{ref}")
    key = f"{reg}/{name}@{ext_digest}"
    async with ensure_lock:
        inflight.setdefault(key, asyncio.Lock())
    async with inflight[key]:
        if await local_has_manifest(reg, name, ext_digest):
            final_d = await _head_local_manifest_digest(reg, name, ref) or ext_digest
            METRICS["ensures_hit"] += 1
            return final_d
        METRICS["ensures_miss"] += 1
        async with sem:
            await asyncio.to_thread(copy_to_local_tag, reg, name, ref)
        final_d = await _head_local_manifest_digest(reg, name, ref) or ext_digest
        return final_d

def _any_inflight_for(reg: str, name: str) -> bool:
    prefix = f"{reg}/{name}@"
    if any(k.startswith(prefix) and lock.locked() for k, lock in inflight.items()):
        return True
    if any(k.startswith(prefix) for k in pending):
        return True
    return False

@app.get("/healthz")
async def healthz(): return {"status": "ok"}

@app.get("/metrics")
async def metrics(): return METRICS

@app.api_route("/v2/", methods=["GET", "HEAD"])
async def ping(): return Response(status_code=200)

@app.get("/ensure-status/{reg}/{name}/{ref}")
async def ensure_status(reg: str, name: str, ref: str):
    if ref.startswith("sha256:"):
        if await local_has_manifest(reg, name, ref):
            return {"status": "ready", "digest": ref}
    else:
        dcd = await _head_local_manifest_digest(reg, name, ref)
        if dcd:
            return {"status": "ready", "digest": dcd}

    key = f"{reg}/{name}@{ref}"
    if key in last_errors:
        return Response(
            f'{{"status":"error","error":"{last_errors[key]}"}}',
            status_code=424,
            headers={"Content-Type": "application/json"},
        )

    if _any_inflight_for(reg, name):
        return Response(
            '{"status":"inflight"}',
            status_code=202,
            headers={"Content-Type": "application/json", "Retry-After": "1"},
        )

    return Response('{"status":"miss"}', status_code=404, headers={"Content-Type": "application/json"})

@app.api_route("/v2/{reg}/{path:path}", methods=["GET", "HEAD"])
async def v2_read(request: Request, reg: str, path: str):
    METRICS["requests_total"] += 1

    m = parse_manifest_path(f"/v2/{reg}/{path}")
    if m:
        METRICS["ensures"] += 1
        reg_m, name, ref = m

        prefer = request.headers.get("Prefer", "").lower()
        async_optin = "respond-async" in prefer or "async=1" in str(request.url).lower()
        if async_optin:
            key = f"{reg_m}/{name}@{ref}"
            pending.add(key)
            async def _bg():
                try:
                    await ensure_local(reg_m, name, ref)
                except Exception as e:
                    last_errors[key] = str(e)
                finally:
                    pending.discard(key)
            asyncio.create_task(_bg())
            loc = f"/ensure-status/{reg_m}/{name}/{ref}"
            return Response(status_code=202, headers={"Location": loc, "Retry-After": "1"})

        try:
            local_digest = await ensure_local(reg_m, name, ref)
        except Exception as e:
            METRICS["errors"] += 1
            return Response(str(e), status_code=502)

        manifest_ref = local_digest if request.method == "GET" else ref
        url = f"{REG_LOCAL_BASE_URL}/v2/{reg_m}/{name}/manifests/{manifest_ref}"

        fwd_headers = _filter_headers(dict(request.headers))
        fwd_headers["Accept"] = _MANIFEST_ACCEPT
        async with httpx.AsyncClient(timeout=None) as client:
            upstream = await client.request(request.method, url, headers=fwd_headers)
        resp_headers = _filter_headers(dict(upstream.headers))
        return Response(content=upstream.content, status_code=upstream.status_code, headers=resp_headers)

    b = parse_blob_path(f"/v2/{reg}/{path}")
    if b:
        reg_b, name, dg = b
        url = f"{REG_LOCAL_BASE_URL}/v2/{reg_b}/{name}/blobs/{dg}"
        fwd_headers = _filter_headers(dict(request.headers))

        # HEAD/GET relay to local registry; on HEAD failure with 5xx, attempt repo auto-repair then retry once
        try:
            async with httpx.AsyncClient(timeout=None, follow_redirects=False) as client:
                upstream = await client.request(request.method, url, headers=fwd_headers)
        except httpx.HTTPError as e:
            if request.method == "HEAD" and AUTO_REPAIR_ON_BLOB_ERRORS:
                repaired = await _repair_repo(reg_b, name)
                try:
                    async with httpx.AsyncClient(timeout=None, follow_redirects=False) as client:
                        upstream = await client.request(request.method, url, headers=fwd_headers)
                except httpx.HTTPError:
                    # après réparation, toujours KO -> 404 pour forcer upload
                    return Response(status_code=404, headers={"Docker-Distribution-API-Version": "registry/2.0"})
            else:
                return Response(str(e), status_code=502)

        if request.method == "HEAD" and upstream.status_code >= 500 and AUTO_REPAIR_ON_BLOB_ERRORS:
            repaired = await _repair_repo(reg_b, name)
            async with httpx.AsyncClient(timeout=None, follow_redirects=False) as client:
                upstream = await client.request(request.method, url, headers=fwd_headers)
            # si toujours 5xx après réparation, on force 404 pour permettre l'upload
            if upstream.status_code >= 500:
                return Response(status_code=404, headers={"Docker-Distribution-API-Version": "registry/2.0"})

        resp_headers = _filter_headers(dict(upstream.headers))
        body = b"" if request.method == "HEAD" else upstream.content
        return Response(content=body, status_code=upstream.status_code, headers=resp_headers)

    return Response(status_code=404)

@app.api_route("/v2/{reg}/{path:path}", methods=["POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def v2_write(request: Request, reg: str, path: str):
    url = f"{REG_LOCAL_BASE_URL}/v2/{reg}/{path}"
    if request.url.query:
        url = f"{url}?{request.url.query}"

    fwd_headers = _filter_headers(dict(request.headers))
    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            upstream = await client.request(request.method, url, headers=fwd_headers, content=body)
    except Exception as e:
        METRICS["errors"] += 1
        return Response(str(e), status_code=502)

    resp_headers = _filter_headers(dict(upstream.headers))
    return Response(content=upstream.content, status_code=upstream.status_code, headers=resp_headers)
