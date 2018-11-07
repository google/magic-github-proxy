import base64
import calendar
import datetime
from typing import Tuple, List

import attr
from cryptography import x509
from cryptography.hazmat import backends
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
import google.auth.crypt
import google.auth.jwt


VALIDITY_PERIOD = 365 * 5  # 5 years.

_BACKEND = backends.default_backend()
_PADDING = padding.OAEP(
    mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None
)


def _datetime_to_secs(value: datetime) -> int:
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


@attr.s(slots=True, auto_attribs=True)
class Keys:
    private_key: rsa.RSAPrivateKey = None
    private_key_signer: google.auth.crypt.RSASigner = None
    public_key: rsa.RSAPublicKey = None
    certificate: x509.Certificate = None
    certificate_pem: str = None

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


def create(keys: Keys, github_token, scopes) -> str:
    # NOTE: This is the *public key* that we use to encrypt this token. It's
    # *extremely* important that the public key is used here, as we want only
    # our *private key* to be able to decrypt this value.
    encrypted_github_token = _encrypt(keys.public_key, github_token.encode("utf-8"))
    encoded_github_token = base64.b64encode(encrypted_github_token).decode("utf-8")

    issued_at = datetime.datetime.utcnow()
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=VALIDITY_PERIOD)

    claims = {
        "iat": _datetime_to_secs(issued_at),
        "exp": _datetime_to_secs(expires_at),
        "github_token": encoded_github_token,
        "scopes": scopes,
    }

    jwt = google.auth.jwt.encode(keys.private_key_signer, claims)

    return jwt.decode("utf-8")


def decode(keys, token) -> Tuple[str, List[str]]:
    claims = google.auth.jwt.decode(token, verify=True, certs=[keys.certificate_pem])

    decoded_github_token = base64.b64decode(claims["github_token"])
    decrypted_github_token = _decrypt(keys.private_key, decoded_github_token).decode(
        "utf-8"
    )
    claims["github_token"] = decrypted_github_token

    return claims["github_token"], claims["scopes"]


# keys = Keys.from_files("keys/private.pem", "keys/public.x509.cer")

# claims = create_token(keys, "awwyis", ["one", "two"])

# print(claims)

# print(decode_token(keys, claims))
