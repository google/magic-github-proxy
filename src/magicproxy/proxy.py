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

from typing import Tuple

import flask
import requests

from . import magictoken
from . import scopes

GITHUB_API_ROOT = "https://api.github.com"

app = flask.Flask(__name__)


@app.route("/magictoken", methods=["POST", "GET"])
def create_magic_token():
    params = flask.request.json

    if not params:
        return "Request must be json.", 400

    if not isinstance(params.get("scopes"), list):
        return "scopes must be a list", 400

    token = magictoken.create(keys, params["github_token"], params["scopes"])

    return token, 200, {"Content-Type": "application/jwt"}


def _clean_request_headers(headers):
    headers = dict(headers)
    headers.pop("Host", None)
    headers.pop("Connection", None)
    # Drop the existing authorization header, it'll only cause problems.
    headers.pop("Authorization", None)
    return headers


def _clean_response_headers(headers):
    headers = dict(headers)
    headers.pop("Content-Length", None)
    headers.pop("Content-Encoding", None)
    headers.pop("Transfer-Encoding", None)
    headers["X-Thea-Codes-GitHub-Proxy"] = "1"
    return headers


def _proxy_request(
    request: flask.Request, url: str, headers=None, **kwargs
) -> Tuple[bytes, int, dict]:
    clean_headers = _clean_request_headers(request.headers)

    if headers:
        clean_headers.update(headers)

    print(
        f"Proxying to {request.method} {url}\nHeaders: {clean_headers}\nQuery: {request.args}\nContent: {request.data}"
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

    response_headers = _clean_response_headers(resp.headers)

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
    if not scopes.validate_request(flask.request.method, path, token_info.scopes):
        return (
            f"Disallowed by GitHub proxy. Allowed scopes: {', '.join(token_info.scopes)}",
            401,
        )

    return _proxy_request(
        request=flask.request,
        url=f"{GITHUB_API_ROOT}/{path}",
        headers={"Authorization": f"Bearer {token_info.github_token}"},
    )

def run_app():
    keys = magictoken.Keys.from_env()
    app.run()

if __name__ == "__main__":
    run_app()
