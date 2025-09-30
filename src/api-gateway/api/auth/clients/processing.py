import logging
import os.path
from fastapi import UploadFile
import requests
from requests import Session, HTTPError
from urllib3.util.ssl_ import create_urllib3_context
from requests.adapters import HTTPAdapter
from typing import List, Optional, Dict, Any
from config.settings import Settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class MTLSAdapter(HTTPAdapter):
    def __init__(self, ca_path: str, key_path: str, cert_path: str, *args, **kwargs):
        self.ca_path = ca_path
        self.key_path = key_path
        self.cert_path = cert_path
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.load_verify_locations(cafile=self.ca_path)
        context.load_cert_chain(certfile=self.cert_path, keyfile=self.key_path)
        kwargs["ssl_context"] = context
        return super().init_poolmanager(*args, **kwargs)


class ProcessingClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    # -------- helpers to read env even if Settings doesn’t declare fields ------
    def _get_env(self, name: str, default: Optional[str] = None) -> Optional[str]:
        val = getattr(self.settings, name, None)
        if val is not None:
            return val
        return os.getenv(name, default)

    def _get_bool(self, name: str, default: bool = False) -> bool:
        val = self._get_env(name, None)
        if val is None:
            return default
        if isinstance(val, bool):
            return val
        return str(val).strip().lower() in ("1", "true", "yes", "y", "on")

    def _get_int(self, name: str, default: int) -> int:
        val = self._get_env(name, None)
        try:
            return int(val) if val is not None else default
        except Exception:
            return default

    # --------------------------------------------------------------------------

    def _check_file_existence(self, file_path: str, description: str) -> None:
        """Vérifie l'existence d'un fichier et log une erreur si non trouvé."""
        if not os.path.exists(file_path):
            logger.error(f"{description} file not found: '{file_path}'")
            raise FileNotFoundError(f"{description} file not found: '{file_path}'")

    def _get_base_url(self) -> str:
        """Resolve processing service base URL from settings/env."""
        base = self._get_env("API_PROCESSING_BASE_URL", None)
        if base:
            # TODO: remove the port from API_PROCESSING_BASE_URL instead
            if ":" in base:
                # Remove port
                base = base.split(":")[0]
            base = str(base).rstrip("/")

            logger.debug(f"ProcessingClient base URL (BASE_URL) resolved to: {base}")
            return base
        scheme = self._get_env("API_PROCESSING_SCHEME", "https")
        host = self._get_env("API_PROCESSING_HOST", "api-processing")
        url = f"{scheme}://{host}"
        logger.debug(f"ProcessingClient base URL (composed) resolved to: {url}")
        return url

    def get_session(self) -> Session:
        """Create a session. mTLS can be disabled via API_PROCESSING_MTLS_ENABLED=false."""
        mtls_enabled = self._get_bool("API_PROCESSING_MTLS_ENABLED", False)
        verify_ssl = self._get_bool("API_PROCESSING_VERIFY_SSL", True)
        session = Session()
        session.verify = verify_ssl

        if mtls_enabled:
            logger.debug("mTLS enabled for processing client session")
            """ Crée une session avec les configurations SSL/TLS nécessaires. """
            ca_path = self.settings.API_PROCESSING_API_GATEWAY_CA_PATH
            key_path = self.settings.API_PROCESSING_API_GATEWAY_KEY_PATH
            cert_path = self.settings.API_PROCESSING_API_GATEWAY_CERT_PATH
            # Vérification de l'existence des fichiers
            self._check_file_existence(ca_path, "CA certificate")
            self._check_file_existence(key_path, "Key")
            self._check_file_existence(cert_path, "Certificate")

            adapter = MTLSAdapter(
                ca_path=ca_path, key_path=key_path, cert_path=cert_path
            )
            session.mount("https://", adapter)
        else:
            logger.debug("mTLS disabled for processing client session")
        return session

    def get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """Génère les en-têtes pour la requête HTTP."""
        headers = {
            "Referer": f"{self.settings.API_GATEWAY_HOST}{self.settings.INTERNAL_ENDPOINT_URL}",
        }
        if token:
            headers.update({"X-API-Key": token, "Authorization": f"Bearer {token}"})
        return headers

    def authenticate(
        self, token: Optional[str], credentials: Dict[str, str]
    ) -> Optional[Dict[str, str]]:
        """Authentifie un utilisateur."""
        base_url = self._get_base_url()
        headers = self.get_headers(token)
        session = self.get_session()
        try:
            response = session.post(
                f"{base_url}/token", data=credentials, headers=headers
            )
            logger.debug(f"Authentication Response Status Code: {response.status_code}")
            logger.debug(f"Authentication Response Content: {response.text}")
            response.raise_for_status()
            return response.json()
        except HTTPError as e:
            logger.error(f"Authentication error: {e}")
            return None

    async def predict(
        self,
        token: str,
        description: str,
        designation: Optional[str] = "",
        files: Optional[List[UploadFile]] = None,
    ):

        url = f"{self._get_base_url()}/api/internal/api-processing/predict"

        headers = self.get_headers(token)
        session = self.get_session()

        data = {"description": description, "designation": designation or ""}
        files_payload = []
        if files:
            files_payload = [
                ("files", (f.filename, await f.read(), f.content_type)) for f in files
            ]
        try:
            r = session.post(
                url, headers=headers, data=data, files=files_payload, timeout=30
            )
            logging.debug(f"response: {r.status_code} - {r.text}")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error(f"Error calling processing service: {e}")
            raise
