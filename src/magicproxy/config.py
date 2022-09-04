import dataclasses
import json
import logging
import os
from collections.abc import Mapping
from typing import Union

from magicproxy.plugins import load_plugins
from magicproxy.types import Permission

logger = logging.getLogger(__name__)


DEFAULT_API_ROOT = "https://api.github.com"
DEFAULT_PRIVATE_KEY_LOCATION = "keys/private.pem"
DEFAULT_PUBLIC_KEY_LOCATION = "keys/public.pem"
DEFAULT_PUBLIC_CERTIFICATE_LOCATION = "keys/public.x509.cer"
DEFAULT_PUBLIC_ACCESS = "http://localhost"


@dataclasses.dataclass
class Config:
    api_root: str = DEFAULT_API_ROOT
    private_key_location: str = DEFAULT_PRIVATE_KEY_LOCATION
    public_key_location: str = DEFAULT_PUBLIC_KEY_LOCATION
    public_certificate_location: str = DEFAULT_PUBLIC_CERTIFICATE_LOCATION
    public_access: str = DEFAULT_PUBLIC_ACCESS
    plugins_location: str = None
    scopes: dict = dataclasses.field(default_factory=lambda: {})


def from_env():
    return Config(
        api_root=os.environ.get("API_ROOT") or DEFAULT_API_ROOT,
        private_key_location=os.environ.get("PRIVATE_KEY_LOCATION")
        or DEFAULT_PRIVATE_KEY_LOCATION,
        public_key_location=os.environ.get("PUBLIC_KEY_LOCATION")
        or DEFAULT_PUBLIC_KEY_LOCATION,
        public_certificate_location=os.environ.get("PUBLIC_CERTIFICATE_LOCATION")
        or DEFAULT_PUBLIC_CERTIFICATE_LOCATION,
        public_access=os.environ.get("PUBLIC_ACCESS") or DEFAULT_PUBLIC_ACCESS,
    )


def from_file(config_file):
    try:
        config_string = open(config_file, "r", encoding="utf-8").read()
    except IOError:
        raise RuntimeError("I/O error, config file should be readable")
    try:
        config = json.loads(config_string)
    except ValueError:
        raise RuntimeError("config file should be a valid JSON file")

    scopes = config.get("scopes", {})
    for scope_key in scopes:
        scope_elements = []
        for scope_element in scopes[scope_key]:
            scope_elements.append(parse_permission(scope_element))
        scopes[scope_key] = scope_elements
    plugins_location = config.get("plugins_location")
    if plugins_location:
        scopes.update(**load_plugins(plugins_location))
    return Config(
        api_root=config.get("api_root") or DEFAULT_API_ROOT,
        private_key_location=config.get("private_key_location")
        or DEFAULT_PRIVATE_KEY_LOCATION,
        public_key_location=config.get("public_key_location")
        or DEFAULT_PUBLIC_KEY_LOCATION,
        public_certificate_location=config.get("public_certificate_location")
        or DEFAULT_PUBLIC_CERTIFICATE_LOCATION,
        public_access=config.get("public_access") or DEFAULT_PUBLIC_ACCESS,
        plugins_location=plugins_location,
        scopes=scopes,
    )


def load_config():
    from magicproxy.magictoken import Keys

    CONFIG_FILE = os.environ.get("CONFIG_FILE")

    config = from_file(CONFIG_FILE) if CONFIG_FILE else from_env()
    config.keys = Keys.from_files(
        config.private_key_location, config.public_certificate_location
    )
    return config


def parse_permission(element: Union[str, Mapping]) -> Permission:
    logging.debug("parsing permission from %s", element)
    if isinstance(element, str):
        try:
            method, path = element.split(" ", 1)
            return Permission(method=method, path=path)
        except ValueError as e:
            raise ValueError('a scope string should be a "METHOD path_regex"') from e
    elif isinstance(element, Mapping):
        if "method" in element and "path" in element:
            return Permission(method=element["method"], path=element["path"])
        else:
            raise ValueError(
                "a scope mapping should be a mapping with method, path keys"
            )
