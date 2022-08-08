from dataclasses import dataclass
from typing import Optional, List, Union

import google.auth
import google.auth.crypt
import google.auth.jwt
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import rsa


@dataclass
class Permission:
    method: str
    path: str


@dataclass
class DecodeResult:
    token: str
    scopes: Optional[str]
    allowed: Optional[List[Union[str, Permission]]]


@dataclass
class _Keys:
    private_key: rsa.RSAPrivateKey = None
    private_key_signer: google.auth.crypt.RSASigner = None
    public_key: rsa.RSAPublicKey = None
    certificate: x509.Certificate = None
    certificate_pem: bytes = None
