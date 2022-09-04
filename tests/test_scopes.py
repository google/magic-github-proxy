from magicproxy.config import Config
from magicproxy.scopes import is_request_allowed, validate_request
from magicproxy.types import Permission


def test_valid_scopes():
    assert is_request_allowed(Permission(method="GET", path="/this"), "GET", "/this")
    assert is_request_allowed(
        Permission(method="GET", path="/subpath/*"), "GET", "/subpath/works"
    )
    assert is_request_allowed(
        Permission(method="GET", path="/subpath*"),
        "GET",
        "/subpath/works/also/that/way",
    )
    assert is_request_allowed(Permission(method="GET", path="/this*"), "GET", "this")

    assert not is_request_allowed(
        Permission(method="GET", path="/this"), "GET", "/that"
    )
    assert not is_request_allowed(
        Permission(method="GET", path="/subpath*"), "PUT", "/different/method/fails"
    )


def test_request_allowed():
    allowed = ["GET /this", "GET /that"]
    config = Config()
    assert validate_request(config, "GET", "/this", allowed=allowed)
    assert validate_request(config, "GET", "/that", allowed=allowed)
    assert not validate_request(config, "GET", "/notthat", allowed=allowed)
    assert not validate_request(config, "POST", "/this", allowed=allowed)


def test_request_scopes():
    config = Config(
        scopes={
            "this_scope": [
                Permission(method="GET", path="/this"),
                Permission(method="GET", path="/that"),
            ]
        }
    )
    scopes = ["this_scope"]
    assert validate_request(config, "GET", "/this", scopes=scopes)
    assert validate_request(config, "GET", "/that", scopes=scopes)
    assert not validate_request(config, "GET", "/notthat", scopes=scopes)
    assert not validate_request(config, "POST", "/this", scopes=scopes)

    assert validate_request(config, "GET", "/this", scopes=scopes)
    assert validate_request(config, "GET", "/that", scopes=scopes)
    assert not validate_request(config, "GET", "/notthat", scopes=scopes)
    assert not validate_request(config, "POST", "/this", scopes=scopes)


def test_request_multiple_scopes():
    config = Config(
        scopes={
            "this_scope": [
                Permission(method="GET", path="/this"),
                Permission(method="GET", path="/that"),
            ],
            "another_scope": [
                Permission(method="POST", path="/those"),
            ],
            "or_another_scope": [
                Permission(method="POST", path="/them"),
            ],
        }
    )

    scopes = ["this_scope"]
    other_scopes = ["another_scope", "or_another_scope"]

    assert validate_request(config, "GET", "/this", scopes=scopes)
    assert validate_request(config, "GET", "/that", scopes=scopes)
    assert not validate_request(config, "GET", "/those", scopes=scopes)

    assert validate_request(config, "POST", "/those", scopes=other_scopes)
    assert validate_request(config, "POST", "/them", scopes=other_scopes)
    assert not validate_request(config, "GET", "/those", scopes=other_scopes)
