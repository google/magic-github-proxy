# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import calendar
import datetime

import google.auth.crypt
import google.auth.jwt
from cryptography import x509
from cryptography.hazmat import backends
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

from magicproxy.config import PRIVATE_KEY_LOCATION, PUBLIC_CERTIFICATE_LOCATION, SCOPES
from magicproxy.crypto import generate_keys
from magicproxy.types import DecodeResult, _Keys

VALIDITY_PERIOD = 365 * 5  # 5 years.

_BACKEND = backends.default_backend()
_PADDING = padding.OAEP(
    mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None
)


def _datetime_to_secs(value: datetime.datetime) -> int:
    return calendar.timegm(value.utctimetuple())


def _encrypt(key, plain_text: bytes) -> bytes:
    return key.encrypt(plain_text, _PADDING)


def _decrypt(key, cipher_text: bytes) -> bytes:
    return key.decrypt(
        cipher_text,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


class Keys(_Keys):
    @classmethod
    def from_files(cls, private_key_file, certificate_file):
        with open(private_key_file, "rb") as fh:
            private_key_bytes = fh.read()
            private_key = serialization.load_pem_private_key(
                private_key_bytes, password=None, backend=_BACKEND
            )
            private_key_signer = google.auth.crypt.RSASigner.from_string(
                private_key_bytes
            )

        with open(certificate_file, "rb") as fh:
            certificate_pem = fh.read()
            certificate = x509.load_pem_x509_certificate(certificate_pem, _BACKEND)
            public_key = certificate.public_key()

        return cls(
            private_key=private_key,
            private_key_signer=private_key_signer,
            public_key=public_key,
            certificate=certificate,
            certificate_pem=certificate_pem,
        )

    @classmethod
    def from_env(cls):
        try:
            return Keys.from_files(PRIVATE_KEY_LOCATION, PUBLIC_CERTIFICATE_LOCATION)
        except FileNotFoundError:
            generate_keys()
            return Keys.from_files(PRIVATE_KEY_LOCATION, PUBLIC_CERTIFICATE_LOCATION)


def create(keys: _Keys, token, scopes=None, allowed=None) -> str:
    # NOTE: This is the *public key* that we use to encrypt this token. It's
    # *extremely* important that the public key is used here, as we want only
    # our *private key* to be able to decrypt this value.
    encrypted_api_token = _encrypt(keys.public_key, token.encode("utf-8"))
    encoded_api_token = base64.b64encode(encrypted_api_token).decode("utf-8")

    issued_at = datetime.datetime.utcnow()
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=VALIDITY_PERIOD)

    claims = {
        "iat": _datetime_to_secs(issued_at),
        "exp": _datetime_to_secs(expires_at),
        "token": encoded_api_token,
    }

    if allowed:
        claims["allowed"] = allowed

    if scopes:
        claims["scopes"] = scopes

    jwt = google.auth.jwt.encode(keys.private_key_signer, claims)

    return jwt.decode("utf-8")


def decode(keys, token) -> DecodeResult:
    claims = dict(
        google.auth.jwt.decode(token, verify=True, certs=[keys.certificate_pem])
    )

    decoded_token = base64.b64decode(claims["token"])
    decrypted_token = _decrypt(keys.private_key, decoded_token).decode("utf-8")
    claims["token"] = decrypted_token

    return DecodeResult(claims["token"], claims.get("scopes"), claims.get("allowed"))


def magictoken_params_validate(params: dict):
    if not params:
        raise ValueError("Request must be json")

    if "token" not in params:
        raise ValueError("We need a token for the API behind, in the 'token' field")

    if "scopes" in params and "allowed" in params:
        raise ValueError(
            "allowed (spelling out the allowed requests) "
            "OR scopes (naming a scope configured on the proxy, not both"
        )

    if "scopes" in params:
        if not isinstance(params.get("scopes"), list):
            raise ValueError("scopes must be a list")
        params_scopes = params.get("scopes", [])
        if not all(isinstance(r, str) for r in params_scopes):
            raise ValueError("scopes must be a list of strings")
        if not all(r in SCOPES for r in params_scopes):
            raise ValueError(
                f"scopes must be configured on the proxy (valid: {' '.join(SCOPES)})"
            )

    elif "allowed" in params:
        if not isinstance(params.get("allowed"), list):
            raise ValueError("allowed must be a list of ")
        if not all(isinstance(r, str) for r in params.get("allowed", [])):
            raise ValueError("allowed must be a list of strings")
