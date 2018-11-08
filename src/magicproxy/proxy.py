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

import re

import flask
import requests

from . import magictoken

GITHUB_API_ROOT = "https://api.github.com"
KEYS = magictoken.Keys.from_files("keys/private.pem", "keys/public.x509.cer")

app = flask.Flask(__name__)


@app.route("/magictoken", methods=["POST", "GET"])
def create_magic_token():
    params = flask.request.json

    if not params:
        return "Request must be json.", 400

    if not isinstance(params.get("scopes"), list):
        return "scopes must be a list", 400

    token = magictoken.create(KEYS, params["github_token"], params["scopes"])

    return token, 200, {"Content-Type": "application/jwt"}


def validate_scope(method, path, scope):
    """Basic scope validation routine.

    The scope must be in the format:

        METHOD path

    For example:

        GET /user
        POST /repos/+?/+?/issues/+?/labels

    Would allow getting the user info and updating labels on issues.
    """
    allowed_method, allowed_path = scope.split(" ", 1)

    if method != allowed_method and allowed_method != "*":
        return False

    if not path.startswith("/"):
        path = f"/{path}"

    print(method, path, scope, allowed_method, allowed_path)

    if not re.match(allowed_path, path, re.I):
        return False

    return True


@app.route("/<path:path>", methods=["POST", "GET", "PATCH", "PUT", "DELETE"])
def proxy(path):
    auth_token = flask.request.headers["Authorization"]

    # strip out "Bearer " if needed
    if auth_token.startswith("Bearer "):
        auth_token = auth_token[len() :]

    # Validate the magic token
    token_info = magictoken.decode(KEYS, auth_token)

    # Validate scopes againt URL and method.
    validated = False
    for scope in token_info.scopes:
        if validate_scope(flask.request.method, path, scope):
            validated = True
            break

    if not validated:
        return (
            f"Disallowed by GitHub proxy. Allowed scopes: {', '.join(token_info.scopes)}",
            401,
        )

    # Make request data to pass to GitHub
    headers = dict(flask.request.headers)
    del headers["Host"]
    del headers["Connection"]
    headers["Authorization"] = f"Bearer {token_info.token_infogithub_token}"

    # Make the GitHub request
    resp = requests.request(
        url=f"{GITHUB_API_ROOT}/{path}", method=flask.request.method, headers=headers
    )

    response_headers = dict(resp.headers)
    response_headers.pop("Content-Length", None)
    response_headers.pop("Content-Encoding", None)
    response_headers.pop("Transfer-Encoding", None)
    response_headers["X-Thea-Codes-GitHub-Proxy"] = "1"

    return resp.content, resp.status_code, response_headers
