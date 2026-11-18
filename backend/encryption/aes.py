
import os
import hashlib

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def derive_aes_key(shared_key: str) -> bytes:
    """
    Derive a 256-bit AES key from the simulated BB84 key.
    """

    if not shared_key or len(shared_key) < 128:
        raise ValueError("Insufficient shared key material")

    key_material = shared_key.encode("utf-8")

    return hashlib.sha256(key_material).digest()


def encrypt_file(file_data: bytes, shared_key: str) -> dict:
    """
    Encrypt file data using AES-256-GCM.
    """

    aes_key = derive_aes_key(shared_key)

    aes = AESGCM(aes_key)

    nonce = os.urandom(12)

    encrypted_data = aes.encrypt(
        nonce,
        file_data,
        None
    )

    return {
        "encrypted_data": encrypted_data,
        "nonce": nonce
    }


def decrypt_file(
    encrypted_data: bytes,
    nonce: bytes,
    shared_key: str
) -> bytes:
    """
    Decrypt file data using AES-256-GCM.
    """

    aes_key = derive_aes_key(shared_key)

    aes = AESGCM(aes_key)

    decrypted_data = aes.decrypt(
        nonce,
        encrypted_data,
        None
    )

    return decrypted_data
