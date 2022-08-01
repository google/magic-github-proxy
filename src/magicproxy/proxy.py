# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Tuple, Set

import flask
import requests

import magicproxy
import magicproxy.types
from .config import API_ROOT, SCOPES
from .headers import clean_request_headers, clean_response_headers
from . import magictoken
from . import scopes
from . import queries

app = flask.Flask(__name__)

query_params_to_clean: Set[str] = set()

custom_request_headers_to_clean: Set[str] = set()


@app.route("/__magictoken", methods=["POST", "GET"])
def create_magic_token():
    if flask.request.method == "GET":
        return "magic API proxy for " + API_ROOT + " version " + magicproxy.__version__
    params = flask.request.json

    if not params:
        return "Request must be json.", 400

    if "scopes" in params and "allowed" in params:
        return (
            "allowed (spelling out the allowed requests)"
            "OR scopes (naming a scope configured on the proxy, not both",
            400,
        )

    if "scopes" in params:
        if not isinstance(params.get("scopes"), list):
            return "scopes must be a list", 400
        params_scopes = params.get("scopes", [])
        if not all(isinstance(r, str) for r in params_scopes):
            return "scopes must be a list of strings", 400
        if not all(r in SCOPES for r in params_scopes):
            return (
                f"scopes must be configured on the proxy (valid: {' '.join(SCOPES)})",
                400,
            )

    elif "allowed" in params:
        if not isinstance(params.get("allowed"), list):
            return "allowed must be a list of ", 400
        if not all(isinstance(r, str) for r in params.get("allowed", [])):
            return "allowed must be a list of strings", 400

    token = magictoken.create(
        keys, params["token"], params.get("scopes"), params.get("allowed")
    )

    return token, 200, {"Content-Type": "application/jwt"}


def _proxy_request(
    request: flask.Request, url: str, headers=None, **kwargs
) -> Tuple[bytes, int, dict]:
    clean_headers = clean_request_headers(
        request.headers, custom_request_headers_to_clean
    )

    if headers:
        clean_headers.update(headers)

    print(
        f"Proxying to {request.method} {url}\nHeaders: {clean_headers}\nQuery: {request.args}\nContent: {request.data!r}"
    )

    # Make the GitHub request
    resp = requests.request(
        url=url,
        method=request.method,
        headers=clean_headers,
        params=dict(request.args),
        data=request.data,
        **kwargs,
    )

    response_headers = clean_response_headers(resp.headers)

    print(resp, resp.headers, resp.content)

    return resp.content, resp.status_code, response_headers


@app.route("/<path:path>", methods=["POST", "GET", "PATCH", "PUT", "DELETE"])
def proxy_api(path):
    auth_token = flask.request.headers["Authorization"]
    # strip out "Bearer " if needed
    if auth_token.startswith("Bearer "):
        auth_token = auth_token[len("Bearer ") :]

    # Validate the magic token
    token_info = magictoken.decode(keys, auth_token)

    # Validate scopes against URL and method.
    if not scopes.validate_request(
        flask.request.method, path, token_info.scopes, token_info.allowed
    ):
        return (
            f"Disallowed by API proxy. Allowed scopes: {', '.join(token_info.scopes)}",
            401,
        )

    path = queries.clean_path_queries(query_params_to_clean, path)

    return _proxy_request(
        request=flask.request,
        url=f"{API_ROOT}/{path}",
        headers={"Authorization": f"Bearer {token_info.token}"},
    )


def run_app():
    global keys
    keys = magictoken.Keys.from_env()
    app.run()


if __name__ == "__main__":
    run_app()
