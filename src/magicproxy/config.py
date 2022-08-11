import json
import logging
import os
from collections.abc import Mapping
from typing import Union

from magicproxy.plugins import load_plugins
from magicproxy.types import Scope

logger = logging.getLogger(__name__)

DEFAULT_API_ROOT = "https://api.github.com"
DEFAULT_PRIVATE_KEY_LOCATION = "keys/private.pem"
DEFAULT_PUBLIC_KEY_LOCATION = "keys/public.pem"
DEFAULT_PUBLIC_CERTIFICATE_LOCATION = "keys/public.x509.cer"
DEFAULT_PUBLIC_ACCESS = "http://localhost"

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

logger.debug("config %s", config)
PLUGINS_LOCATION = config.get("plugins_location")

API_ROOT = os.environ.get("API_ROOT", config.get("api_root", DEFAULT_API_ROOT))
PRIVATE_KEY_LOCATION = os.environ.get(
    "PRIVATE_KEY_LOCATION",
    config.get("private_key_location", DEFAULT_PRIVATE_KEY_LOCATION),
)
PUBLIC_KEY_LOCATION = os.environ.get(
    "PUBLIC_KEY_LOCATION",
    config.get("public_key_location", DEFAULT_PUBLIC_KEY_LOCATION),
)
PUBLIC_CERTIFICATE_LOCATION = os.environ.get(
    "PUBLIC_CERTIFICATE_LOCATION",
    config.get("public_certificate_location", DEFAULT_PUBLIC_CERTIFICATE_LOCATION),
)
PUBLIC_ACCESS = os.environ.get(
    "PUBLIC_ACCESS", config.get("public_access", DEFAULT_PUBLIC_ACCESS)
)

SCOPES = config.get("scopes", {})


def parse_scope(element: Union[str, Mapping]) -> Scope:
    logging.debug("parsing scope from %s", element)
    if isinstance(element, str):
        try:
            method, path = element.split(" ", 1)
            return Scope(method=method, path=path)
        except ValueError as e:
            raise ValueError('a scope string should be a "METHOD path_regex"') from e
    elif isinstance(element, Mapping):
        if "method" in element and "path" in element:
            return Scope(method=element["method"], path=element["path"])
        else:
            raise ValueError(
                "a scope mapping should be a mapping with method, path keys"
            )


for scope_key in SCOPES:
    scope_elements = []
    for scope_element in SCOPES[scope_key]:
        scope_elements.append(parse_scope(scope_element))
    SCOPES[scope_key] = scope_elements

logger.debug("PLUGINS_LOCATION %s", PLUGINS_LOCATION)
if PLUGINS_LOCATION:
    SCOPES.update(**load_plugins(PLUGINS_LOCATION))

logger.debug("SCOPES %s", SCOPES)
