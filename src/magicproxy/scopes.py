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
import logging
import re
import types
from typing import List, Union

from magicproxy.config import SCOPES
from magicproxy.types import Scope

logger = logging.getLogger(__name__)


def is_request_allowed(scope: Scope, method, path):
    logger.debug(f"validating request {method} {path} on scope {scope}")

    if method != scope.method and scope.method != "*":
        return False

    if not path.startswith("/"):
        path = f"/{path}"

    if re.match(scope.path, path, re.I):
        return True


def validate_request(
    method: str, path: str, scopes: List[str] = None, allowed: List[str] = None
) -> bool:
    """Basic scope validation routine.

    Args:
        method: The HTTP method.
        path: The request path.
        scopes: The list of allowed named scopes.
        allowed: The list of allowed requests.

    The named scope must be configured in the proxy
    Or allowed passed through a METHOD path string like this:

        METHOD path

    For example:

        GET /user
        POST /repos/+?/+?/issues/+?/labels

    Would allow getting the user info and updating labels on issues on a GitHub repo
    """
    if allowed is None:
        allowed = []

    if scopes is None:
        scopes = []

    for scope_key in scopes:
        scope_list: List[Scope] = SCOPES[scope_key]
        for scope in scope_list:
            if is_request_allowed(scope, method, path):
                return True

    for allowed_item in allowed:
        allowed_method, allowed_path = allowed_item.split(" ", 1)
        if is_request_allowed(
            Scope(method=allowed_method, path=allowed_path), method, path
        ):
            return True

    return False
