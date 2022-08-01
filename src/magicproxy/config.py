import json
import os
from collections.abc import Mapping

from magicproxy.types import Scope

DEFAULT_API_ROOT = "https://api.github.com"
DEFAULT_PRIVATE_KEY_LOCATION = "keys/private.pem"
DEFAULT_PUBLIC_KEY_LOCATION = "keys/public.x509.cer"

CONFIG_FILE = os.environ.get("CONFIG_FILE")

config = {}

if CONFIG_FILE is not None:
    try:
        config_string = open(CONFIG_FILE, "r", encoding="utf-8").read()
    except IOError:
        raise RuntimeError("I/O error, config file should be readable")
    try:
        config = json.loads(config_string)
    except ValueError:
        raise RuntimeError("config file should be a valid JSON file")


API_ROOT = os.environ.get("API_ROOT", config.get("api_root", DEFAULT_API_ROOT))
PRIVATE_KEY_LOCATION = os.environ.get(
    "MAGICPROXY_PRIVATE_KEY",
    config.get("private_key_location", DEFAULT_PRIVATE_KEY_LOCATION),
)
PUBLIC_KEY_LOCATION = os.environ.get(
    "MAGICPROXY_PUBLIC_KEY",
    config.get("public_key_location", DEFAULT_PUBLIC_KEY_LOCATION),
)
PUBLIC_ACCESS = os.environ.get("PUBLIC_ACCESS", config.get("public_access"))

SCOPES = config.get("scopes", {})
for scope_key in SCOPES:
    scope_elements = []
    for element in SCOPES[scope_key]:
        if isinstance(element, str):
            method, path = element.split(" ", 1)
            scope_elements.append(Scope(method=method, path=path))
        elif isinstance(element, Mapping):
            if "method" in element and "path" in element:
                scope_elements.append(
                    Scope(method=element["method"], path=element["path"])
                )
            else:
                raise RuntimeError(
                    "a scope element should be a mapping with method and path key"
                )

    SCOPES[scope_key] = scope_elements
