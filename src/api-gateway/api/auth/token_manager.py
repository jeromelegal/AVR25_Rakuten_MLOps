from fastapi import HTTPException, status, Header
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.fernet import Fernet
from datetime import datetime, timedelta, timezone
from jose import jwt
from api.config.settings import settings
from typing import Optional, Dict
import os, json

# Charger la clé privée à partir des paramètres
private_key = serialization.load_pem_private_key(
    settings.RSA_PRIVATE_KEY.encode('utf-8'),  # On suppose que la clé est au format PEM
    password=None,
    backend=default_backend()
)

public_key = private_key.public_key()
# Générer une clé symétrique pour le chiffrement du payload
symmetric_key = os.urandom(32)  # 256-bit key for AES-256

def create_meta_token(user_data: dict, backend_uid: dict, backend_tokens: dict):
    # Inclure directement les tokens des backends sans chiffrement
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    # Calculer les dates d'expiration et d'émission
    now_utc = datetime.now(timezone.utc)
    exp = now_utc + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Ajouter des informations supplémentaires au payload du token
    payload = {
        "user_id": user_data.get("user_id"),
        "tokens": backend_tokens,  # Tokens non chiffrés
        "uid": backend_uid,  # Tokens non chiffrés
        "public_key": public_key_pem,
        "exp": exp.isoformat(),
        "iat": now_utc.isoformat(),
        "scope": "access_token"
    }
    return payload

def encrypt_payload(payload: Dict) -> bytes:
    """Chiffre le payload avec une clé symétrique (AES)."""
    payload_json = json.dumps(payload).encode('utf-8')
    iv = os.urandom(16)  # AES block size is 16 bytes
    cipher = Cipher(algorithms.AES(symmetric_key), modes.CBC(iv), backend=default_backend())
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(payload_json) + padder.finalize()
    encryptor = cipher.encryptor()
    encrypted_payload = encryptor.update(padded_data) + encryptor.finalize()
    return iv + encrypted_payload

def decrypt_payload(encrypted_data: bytes) -> Dict:
    """Déchiffre le payload avec la clé symétrique."""
    iv = encrypted_data[:16]
    encrypted_payload = encrypted_data[16:]
    cipher = Cipher(algorithms.AES(symmetric_key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(encrypted_payload) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()

    return json.loads(data.decode('utf-8'))

# Le reste de votre code pour la signature, vérification, etc., reste inchangé
def sign_data(data: bytes) -> bytes:
    """Signe les données avec la clé privée."""
    signature = private_key.sign(
        data,
        asym_padding.PSS(
            mgf=asym_padding.MGF1(hashes.SHA256()),
            salt_length=asym_padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature

def verify_signature(data: bytes, signature: bytes, public_key) -> bool:
    """Vérifie la signature avec la clé publique."""
    try:
        public_key.verify(
            signature,
            data,
            asym_padding.PSS(
                mgf=asym_padding.MGF1(hashes.SHA256()),
                salt_length=asym_padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        return False

def create_signed_encrypted_token(payload: Dict) -> str:
    encrypted_data = encrypt_payload(payload)
    signature = sign_data(encrypted_data)
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return f"{encrypted_data.hex()}.{signature.hex()}.{public_key_pem.decode('utf-8')}"

def verify_and_decrypt_token(token: str) -> Optional[Dict]:
    """Vérifie la signature et déchiffre le token si la signature est valide."""
    try:
        encrypted_data_hex, signature_hex, public_key_pem = token.split('.')
        encrypted_data = bytes.fromhex(encrypted_data_hex)
        signature = bytes.fromhex(signature_hex)
        loaded_public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'),
            backend=default_backend()
        )
        if verify_signature(encrypted_data, signature, loaded_public_key):
            payload = decrypt_payload(encrypted_data)
            return payload
        else:
            return None
    except Exception as e:
        print(f"Erreur pendant la vérification/déchiffrement du token: {e}")
        return None

def get_token_from_header(authorization: str) -> str:
    try:
        # Diviser sur le premier espace seulement pour séparer "Bearer" du token
        parts = authorization.split(' ', 1)

        if len(parts) != 2:
            raise ValueError("Authorization header must contain exactly two parts.")

        scheme, token = parts
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token
    except ValueError as ve:
        print("Error:", ve)  # Affichage des erreurs éventuelles
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_user_data_from_token(authorization: str = Header(...)) -> Dict:
    """
    Fonction centrale pour récupérer les données utilisateur à partir du token.
    Elle vérifie la signature et déchiffre le payload.
    """
    token = get_token_from_header(authorization)
    user_data = verify_and_decrypt_token(token)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    print(f"user_data\n   {user_data}")
    return user_data
