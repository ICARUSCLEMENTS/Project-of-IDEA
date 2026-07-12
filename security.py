import hashlib
import os
from dotenv import load_dotenv
from fastapi import Header, HTTPException

load_dotenv()

_API_KEY_HASH = os.getenv("API_KEY_HASH")


def verificar_api_key(x_api_key: str = Header(...)):
    if _API_KEY_HASH is None:
        raise HTTPException(status_code=500,
                            detail="API_KEY_HASH não configurada no servidor")
    hash_recebido = hashlib.sha256(x_api_key.encode()).hexdigest()
    if hash_recebido != _API_KEY_HASH:
        raise HTTPException(status_code=401, detail="API Key inválida")