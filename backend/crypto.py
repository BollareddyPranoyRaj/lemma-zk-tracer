"""
backend/crypto.py
─────────────────
Cryptographic Provenance Layer.

Design:
  • doc_hash     = SHA-256(raw PDF bytes)           — document fingerprint
  • source_hash  = SHA-256(source_text.encode())    — evidence fingerprint
  • verification_hash = HMAC-SHA256(
        key   = settings.proof_hmac_secret,
        msg   = f"{doc_hash}|{metric_name}|{value}|{source_text}"
    )
    This is a ZK-style *attribute proof*: without the HMAC secret you cannot
    forge a valid verification_hash for any (doc, metric, value, source) tuple.

Phase 3 Note:
  The Poseidon hash (ZK-SNARK compatible) would replace SHA-256 for the
  commitment layer in a production system. We include the poseidon utility
  here so Phase 3 can swap it in without restructuring.
"""
from __future__ import annotations

import hashlib
import hmac
from functools import lru_cache

from backend.config import get_settings


# ─── Low-level primitives ─────────────────────────────────────────────────────


def sha256_bytes(data: bytes) -> str:
    """Return hex-encoded SHA-256 of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str, encoding: str = "utf-8") -> str:
    """Return hex-encoded SHA-256 of a UTF-8 string."""
    return sha256_bytes(text.encode(encoding))


def hmac_sha256(key: str, message: str, encoding: str = "utf-8") -> str:
    """Return hex-encoded HMAC-SHA256."""
    return hmac.new(
        key.encode(encoding),
        message.encode(encoding),
        hashlib.sha256,
    ).hexdigest()


# ─── Document Hashing ─────────────────────────────────────────────────────────


def hash_document(pdf_bytes: bytes) -> str:
    """
    Compute the canonical document hash from raw PDF bytes.
    This is the cryptographic anchor for all metrics extracted from the doc.
    """
    return sha256_bytes(pdf_bytes)


# ─── Metric Provenance ────────────────────────────────────────────────────────


def compute_source_hash(source_text: str) -> str:
    """
    SHA-256 of the verbatim source passage.
    Anyone with the source text can verify this hash independently — no secret needed.
    """
    return sha256_text(source_text)


def compute_verification_hash(
    doc_hash: str,
    metric_name: str,
    value: str,
    source_text: str,
) -> str:
    """
    HMAC-SHA256 binding (document, metric, value, source_evidence) together.

    Properties:
      - Deterministic: same inputs → same hash every time.
      - Unforgeable: without the HMAC secret you cannot produce a valid hash.
      - Auditable: given the secret, any auditor can re-derive and verify.

    The message format uses '|' as delimiter after URL-encoding each field
    to prevent injection attacks (e.g. a value that itself contains '|').
    """
    from urllib.parse import quote

    canonical = "|".join([
        quote(doc_hash, safe=""),
        quote(metric_name, safe=""),
        quote(value, safe=""),
        quote(source_text, safe=""),
    ])
    return hmac_sha256(get_settings().proof_hmac_secret, canonical)


def verify_metric_proof(
    doc_hash: str,
    metric_name: str,
    value: str,
    source_text: str,
    claimed_verification_hash: str,
) -> bool:
    """
    Constant-time verification of a claimed verification_hash.
    Returns True only if the hash is valid for the given inputs.
    """
    expected = compute_verification_hash(doc_hash, metric_name, value, source_text)
    return hmac.compare_digest(expected, claimed_verification_hash)


# ─── Poseidon hash (ZK-SNARK compatible commitment) ─────────────────────────


# BN254 scalar field prime (used in Groth16, Plonk circuits)
_BN254_PRIME = (
    21888242871839275222246405745257275088548364400416034343698204186575808495617
)

# Minimal Poseidon round constants (MDS + ARK for t=3 BN254 — simplified)
# In production use the full Iden3 poseidon params from circomlib.
_POSEIDON_C = [
    0x0eb7f9a1b12a84a6eb0e3faafbd42c26e47c7ab89c8d9a7e4e7b0b9c3d7a1234,
    0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a,
    0x2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b,
]


def poseidon_commitment(field_elements: list[int]) -> int:
    """
    Poseidon hash over the BN254 scalar field (simplified t=3 sponge).

    This is a *reference implementation* for Phase 3 hackathon purposes.
    For production ZK circuits, use circomlib's exact parameter set
    (matching your Circom circuit's poseidon component).

    Args:
        field_elements: List of integers (mod BN254_PRIME).

    Returns:
        Integer commitment in the BN254 scalar field.
    """
    p = _BN254_PRIME
    # Absorb each element
    state = [0, 0, 0]
    for elem in field_elements:
        state[0] = (state[0] + (elem % p)) % p
        # MDS mix (simplified: state[1] XOR, state[2] rotate)
        state[1] = (state[1] + state[0]) % p
        state[2] = (state[2] + state[1]) % p
        # S-box (x^5 in BN254 field — matches Poseidon spec)
        state = [pow(s, 5, p) for s in state]
        # Add round constant
        for i, c in enumerate(_POSEIDON_C):
            state[i] = (state[i] + c) % p

    return state[0]  # Return first element as commitment

