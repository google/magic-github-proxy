import glob
import logging
import os
import traceback
from importlib import util
import inspect

logger = logging.getLogger()


class InvalidPluginError(Exception):
    pass


class PluginNotFoundError(Exception):
    pass


def load_module(path):
    name = os.path.split(path)[-1]
    spec = util.spec_from_file_location(name, path)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_plugins(plugins_folder):
    plugins = {}
    for python_file in glob.glob(f"{plugins_folder}/*.py"):
        logging.debug("load_plugin %s", python_file)
        scope_key, module = load_plugin(python_file)
        plugins[scope_key] = module

    return plugins


def load_plugin(python_file):
    scope_key = os.path.splitext(os.path.basename(python_file))[0]
    plugin_str = f"{scope_key} ({python_file})"
    if not os.path.exists(python_file):
        raise PluginNotFoundError("this plugin file does not exist")
    try:
        module = load_module(python_file)
    except Exception as e:
        logger.error("%s not importable", plugin_str)
        logger.error(traceback.format_exc())
        raise InvalidPluginError() from e

    has_is_requests_allowed = hasattr(module, "is_request_allowed")
    has_response_callback = hasattr(module, "response_callback")

    if has_is_requests_allowed or has_response_callback:
        if has_is_requests_allowed:
            signature = inspect.signature(module.is_request_allowed)
            if (
                "method" not in signature.parameters
                and "path" not in signature.parameters
            ):
                raise InvalidPluginError(
                    "%s is_request_allowed member needs 'method', 'path' parameters",
                    plugin_str,
                )

        if has_response_callback:
            signature = inspect.signature(module.response_callback)
            if (
                "content" not in signature.parameters
                and "code" not in signature.parameters
                and "headers" not in signature.parameters
            ):
                raise InvalidPluginError(
                    "%s response_callback member needs 'content', 'code', 'headers' parameters",
                    plugin_str,
                )
    else:
        raise InvalidPluginError(
            "%s no member is_request_allowed or request_callback", plugin_str
        )

    return scope_key, module
