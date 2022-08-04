import os
import types

import pytest

from magicproxy.plugins import (
    load_plugin,
    InvalidPluginError,
    load_plugins,
    PluginNotFoundError,
)

plugins_dir = os.path.join(os.path.dirname(__file__), "data", "plugins")
invalid_plugins_dir = os.path.join(os.path.dirname(__file__), "data", "invalid_plugins")


def test_plugin_load():
    plugin_path = os.path.join(plugins_dir, "allow_all.py")
    key, module = load_plugin(plugin_path)
    assert key == "allow_all"
    assert isinstance(module, types.ModuleType)

    assert module.is_request_allowed("DELETE", "/")


def test_plugin_load_allow_none():
    plugin_path = os.path.join(plugins_dir, "allow_none.py")
    key, module = load_plugin(plugin_path)
    assert key == "allow_none"
    assert isinstance(module, types.ModuleType)

    assert not module.is_request_allowed("DELETE", "/")
    assert not module.is_request_allowed("GET", "/that")


@pytest.mark.parametrize("plugin_py", ["invalid_plugin.py", "invalid_plugin2.py"])
def test_plugin_load_invalid_plugin(plugin_py):
    plugin_path = os.path.join(invalid_plugins_dir, plugin_py)
    with pytest.raises(InvalidPluginError):
        load_plugin(plugin_path)


def test_plugin_load_inexistent_plugin():
    plugin_path = os.path.join(invalid_plugins_dir, "plugin-does-not-exist.py")
    with pytest.raises(PluginNotFoundError):
        load_plugin(plugin_path)


def test_plugin_invalid_syntax(tmp_path):
    plugin_path = tmp_path / "p.py"
    with open(plugin_path, "w") as invalid:
        # not written as a file otherwise IDE/lint complains
        invalid.write(
            """
// this is not python

function is_request_allowed(method, path) {
    return false
}
"""
        )
    with pytest.raises(InvalidPluginError):
        load_plugin(plugin_path)


def test_plugins_load():
    plugins = load_plugins(plugins_dir)
    assert "allow_none" in plugins
    assert "allow_all" in plugins
    assert "other_code" in plugins
    assert "invalid_syntax" not in plugins
