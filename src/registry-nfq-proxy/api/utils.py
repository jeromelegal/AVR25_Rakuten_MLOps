import os
import json
import subprocess
import platform
import time
import httpx

# Base URL du registry tampon (interne)
REG_LOCAL_BASE_URL = os.getenv("REG_LOCAL_BASE_URL", "http://internal-registry:5000")
# Hôte/port du registry tampon pour skopeo
TAMPON_REGISTRY = os.getenv("TAMPON_REGISTRY", "internal-registry:5000")

# Registry amont par défaut (si le chemin demandé ne contient pas de domaine)
UPSTREAM_REGISTRY = os.getenv("UPSTREAM_REGISTRY", "docker.io")

# TLS / proxies
INSECURE_SRC = os.getenv("INSECURE_SRC", "false").lower() in ("1", "true", "yes")
INSECURE_DEST = os.getenv("INSECURE_DEST", "true").lower() in ("1", "true", "yes")

# Mirroring: single-arch rapide par défaut, all-arch optionnel
MIRROR_ALL_ARCHS = os.getenv("MIRROR_ALL_ARCHS", "false").lower() in ("1", "true", "yes")
PLATFORM_OS = os.getenv("PLATFORM_OS", "linux")
PLATFORM_ARCH = os.getenv("PLATFORM_ARCH", "").lower()   # "amd64", "arm64", ...
PLATFORM_VARIANT = os.getenv("PLATFORM_VARIANT", "")     # ex "v7" pour arm 32 bits

# Retries réseau (timeouts, EOF, i/o timeout, handshake timeout…)
SKOPEO_RETRIES = int(os.getenv("SKOPEO_RETRIES", "6"))
SKOPEO_BACKOFF_BASE = float(os.getenv("SKOPEO_BACKOFF_BASE", "0.8"))  # secondes

_MANIFEST_ACCEPT = (
    "application/vnd.docker.distribution.manifest.v2+json,"
    "application/vnd.docker.distribution.manifest.list.v2+json,"
    "application/vnd.oci.image.index.v1+json,"
    "application/vnd.oci.image.manifest.v1+json,"
    "application/json"
)

_TRANSIENT_ERR_SNIPPETS = (
    "TLS handshake timeout",
    "i/o timeout",
    "Client.Timeout exceeded",
    "EOF",
    "temporary failure",
    "connection reset",
    "PROXY",
)

def _norm_arch(x: str) -> str:
    x = x.lower()
    return {"x86_64": "amd64", "aarch64": "arm64", "armv7l": "arm", "armv6l": "arm"}.get(x, x)

def _has_domain(ns: str) -> bool:
    """Détecte si 'ns' ressemble à un host (docker.io, ghcr.io, quay.io, localhost:5000, ...)."""
    return "." in ns or ":" in ns or ns == "localhost"

def _compose_upstream_tag(reg: str, name: str, ref: str) -> str:
    """
    Construit 'host/namespace/name:tag' pour l’amont.
    Si 'reg' ne contient pas de domaine, on préfixe UPSTREAM_REGISTRY (docker.io par défaut).
    """
    host_ns = f"{reg}/{name}" if _has_domain(reg) else f"{UPSTREAM_REGISTRY}/{reg}/{name}"
    return f"{host_ns}:{ref}"

def _compose_upstream_digest(reg: str, name: str, digest: str) -> str:
    """
    Construit 'host/namespace/name@sha256:...' pour l’amont.
    """
    host_ns = f"{reg}/{name}" if _has_domain(reg) else f"{UPSTREAM_REGISTRY}/{reg}/{name}"
    return f"{host_ns}@{digest}"

def _tls_flags(src=False, dest=False):
    flags = []
    if src and INSECURE_SRC:
        flags += ["--src-tls-verify=false"]
    if dest and INSECURE_DEST:
        flags += ["--dest-tls-verify=false"]
    return flags

def _run_skopeo(args: list[str]) -> str:
    """
    Lance skopeo avec retries exponentiels sur erreurs transitoires réseau.
    Retourne stdout (str) si OK, sinon relance puis finit par propager l’exception.
    """
    attempt = 0
    last_err = None
    while attempt < SKOPEO_RETRIES:
        try:
            return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            out = e.output or str(e)
            # Erreurs transitoires fréquentes derrière VPN/proxy
            if any(snip.lower() in out.lower() for snip in _TRANSIENT_ERR_SNIPPETS):
                last_err = out
                delay = SKOPEO_BACKOFF_BASE * (2 ** attempt)
                time.sleep(delay)
                attempt += 1
                continue
            # Sinon, on remonte directement
            raise
        except Exception as e:  # sécurité
            last_err = str(e)
            delay = SKOPEO_BACKOFF_BASE * (2 ** attempt)
            time.sleep(delay)
            attempt += 1
            continue
    # Après tous les retries, échoue proprement
    if last_err:
        raise RuntimeError(f"skopeo retried {SKOPEO_RETRIES} times and still failed: {last_err}")
    raise RuntimeError(f"skopeo failed after {SKOPEO_RETRIES} attempts")

def skopeo_inspect_digest(ref: str) -> str:
    """
    Retourne le digest du manifest (tag ou digest) depuis la source publique.
    ref: 'host/ns/name:tag' (sans docker://)
    """
    cmd = ["skopeo", "inspect", "--retry-times", "3"]
    if INSECURE_SRC:
        cmd += ["--tls-verify=false"]
    cmd += [f"docker://{ref}"]
    out = _run_skopeo(cmd)
    data = json.loads(out)
    digest = data.get("Digest")
    if not digest:
        raise RuntimeError(f"Digest not found for {ref}")
    return digest

async def local_has_manifest(reg: str, name: str, digest: str) -> bool:
    """
    Vérifie la présence locale (tampon) d’un manifest par digest.
    """
    url = f"{REG_LOCAL_BASE_URL}/v2/{reg}/{name}/manifests/{digest}"
    async with httpx.AsyncClient(timeout=None) as client:
        r = await client.head(url, headers={"Accept": _MANIFEST_ACCEPT})
    return r.status_code == 200

def copy_to_local_digest(reg: str, name: str, digest: str) -> None:
    """
    Copie par DIGEST (manifest simple, pas manifest list).
    """
    src_ref = _compose_upstream_digest(reg, name, digest)
    src = f"docker://{src_ref}"
    dest = f"docker://{TAMPON_REGISTRY}/{reg}/{name}@{digest}"
    cmd = ["skopeo", "copy", "--retry-times", "3"] + _tls_flags(src=True, dest=True) + [src, dest]
    _run_skopeo(cmd)

def copy_to_local_tag(reg: str, name: str, ref: str) -> None:
    """
    Copie par TAG.
      - MIRROR_ALL_ARCHS=true  -> --all (manifest list + variantes)  [plus lent]
      - sinon (défaut)         -> single-arch via --override-os/--override-arch[/--override-variant]
    """
    src_ref = _compose_upstream_tag(reg, name, ref)
    src = f"docker://{src_ref}"
    dest = f"docker://{TAMPON_REGISTRY}/{reg}/{name}:{ref}"
    base = ["skopeo", "copy", "--retry-times", "3"] + _tls_flags(src=True, dest=True)

    if MIRROR_ALL_ARCHS:
        cmd = base + ["--all", src, dest]
    else:
        arch = PLATFORM_ARCH or _norm_arch(platform.machine())
        cmd = base + [f"--override-os={PLATFORM_OS}", f"--override-arch={arch}"]
        if PLATFORM_VARIANT:
            cmd += [f"--override-variant={PLATFORM_VARIANT}"]
        cmd += [src, dest]

    _run_skopeo(cmd)
