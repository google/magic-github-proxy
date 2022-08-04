from magicproxy.config import SCOPES
from magicproxy.scopes import is_request_allowed, validate_request
from magicproxy.types import Scope


def test_valid_scopes():
    assert is_request_allowed(Scope(method="GET", path="/this"), "GET", "/this")
    assert is_request_allowed(
        Scope(method="GET", path="/subpath/*"), "GET", "/subpath/works"
    )
    assert is_request_allowed(
        Scope(method="GET", path="/subpath*"), "GET", "/subpath/works/also/that/way"
    )
    assert is_request_allowed(Scope(method="GET", path="/this*"), "GET", "this")

    assert not is_request_allowed(Scope(method="GET", path="/this"), "GET", "/that")
    assert not is_request_allowed(
        Scope(method="GET", path="/subpath*"), "PUT", "/different/method/fails"
    )


def test_request_allowed():
    allowed = ["GET /this", "GET /that"]
    assert validate_request("GET", "/this", allowed=allowed)
    assert validate_request("GET", "/that", allowed=allowed)
    assert not validate_request("GET", "/notthat", allowed=allowed)
    assert not validate_request("POST", "/this", allowed=allowed)


def test_request_scopes():
    SCOPES["this_scope"] = [
        Scope(method="GET", path="/this"),
        Scope(method="GET", path="/that"),
    ]
    scopes = ["this_scope"]
    assert validate_request("GET", "/this", scopes=scopes)
    assert validate_request("GET", "/that", scopes=scopes)
    assert not validate_request("GET", "/notthat", scopes=scopes)
    assert not validate_request("POST", "/this", scopes=scopes)

    assert validate_request("GET", "/this", scopes=scopes)
    assert validate_request("GET", "/that", scopes=scopes)
    assert not validate_request("GET", "/notthat", scopes=scopes)
    assert not validate_request("POST", "/this", scopes=scopes)

    del SCOPES["this_scope"]


def test_request_multiple_scopes():
    SCOPES["this_scope"] = [
        Scope(method="GET", path="/this"),
        Scope(method="GET", path="/that"),
    ]
    SCOPES["another_scope"] = [
        Scope(method="POST", path="/those"),
    ]
    scopes = ["this_scope", "another_scope"]
    assert validate_request("GET", "/this", scopes=scopes)
    assert validate_request("GET", "/that", scopes=scopes)
    assert not validate_request("GET", "/notthat", scopes=scopes)
    assert validate_request("POST", "/those", scopes=scopes)
    assert not validate_request("GET", "/those", scopes=scopes)

    del SCOPES["this_scope"]
    del SCOPES["another_scope"]
