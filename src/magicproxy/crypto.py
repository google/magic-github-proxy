import os
from urllib.parse import urlparse

from OpenSSL import crypto

from magicproxy.config import Config


def generate_keys(config: Config):
    os.makedirs(os.path.dirname(config.private_key_location), exist_ok=True)
    os.makedirs(os.path.dirname(config.public_key_location), exist_ok=True)
    os.makedirs(os.path.dirname(config.public_certificate_location), exist_ok=True)
    parsed = urlparse(config.public_access)
    if not parsed.hostname:
        raise ValueError(f"url {config.public_access} does not seem to have a hostname")

    hostname = str(parsed.hostname)
    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_RSA, 2048)

    with open(config.private_key_location, "wb") as private_key_file:
        private_key_file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))

    with open(config.public_key_location, "wb") as public_key_file:
        public_key_file.write(crypto.dump_publickey(crypto.FILETYPE_PEM, pkey))

    req = crypto.X509Req()
    subject = req.get_subject()
    setattr(subject, "CN", hostname)
    req.set_pubkey(pkey)
    req.sign(pkey, "sha256")

    certificate = crypto.X509()
    certificate.gmtime_adj_notBefore(0)
    certificate.gmtime_adj_notAfter(1825 * 24 * 60 * 60)
    certificate.set_subject(req.get_subject())
    certificate.set_issuer(req.get_subject())
    certificate.set_pubkey(pkey)
    certificate.sign(pkey, "sha256")

    with open(config.public_certificate_location, "wb") as certificate_file:
        certificate_file.write(
            crypto.dump_certificate(crypto.FILETYPE_PEM, certificate)
        )
