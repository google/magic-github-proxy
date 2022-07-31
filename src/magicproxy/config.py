import os

API_ROOT = os.environ.get("API_ROOT", "https://api.github.com")
PRIVATE_KEY_LOCATION = os.environ.get("MAGICPROXY_PRIVATE_KEY", "keys/private.pem")
PUBLIC_KEY_LOCATION = os.environ.get("MAGICPROXY_PUBLIC_KEY", "keys/public.x509.cer")
PUBLICLY_ACCESSIBLE = os.environ["PUBLICLY_ACCESSIBLE"]

