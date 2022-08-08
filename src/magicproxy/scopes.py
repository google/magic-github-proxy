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
from typing import List, Union, Optional

from magicproxy.config import SCOPES
from magicproxy.types import Permission

logger = logging.getLogger(__name__)


def is_request_allowed(permission: Permission, method, path):
    logger.debug(f"validating request {method} {path} on permission {permission}")

    if method != permission.method and permission.method != "*":
        return False

    if re.match(permission.path, path, re.I):
        return True


def validate_request(
    method: str,
    path: str,
    scopes: List[str] = None,
    allowed: List[str] = None,
) -> bool:
    """Basic scope validation routine.

    Args:
        method: The request HTTP method.
        path: The request path.
        scopes: allowed named scopes.
        allowed: The list of allowed requests.

    The named scope(s) must be configured in the proxy
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

    if not path.startswith("/"):
        path = f"/{path}"

    for scope_key in scopes:
        scope_element: Union[List[Permission], types.ModuleType] = SCOPES[scope_key]
        if isinstance(scope_element, list):
            for scope in scope_element:
                if is_request_allowed(scope, method, path):
                    return True
        elif isinstance(scope_element, types.ModuleType):
            if hasattr(scope_element, "is_request_allowed"):
                return scope_element.is_request_allowed(method=method, path=path)

    for allowed_item in allowed:
        allowed_method, allowed_path = allowed_item.split(" ", 1)
        if is_request_allowed(
            Permission(method=allowed_method, path=allowed_path), method, path
        ):
            return True

    return False


def response_callback(method, path, content, code, headers, scopes: Optional[List[str]] =None):
    """Response callback, for dynamic proxies

    Args:
        scopes: The allowed named scopes.

    The named scope must be configured in the proxy

    Would allow the proxy to process the response of a request
    e.g. can allow a DELETE on a resource once its :id: is known in the JSON of the reponse
    """
    if scopes is None:
        scopes = []

    if not path.startswith("/"):
        path = f"/{path}"

    for scope in scopes:
        scope_element: Union[List[Permission], types.ModuleType] = SCOPES[scope]
        if isinstance(scope_element, types.ModuleType):
            if hasattr(scope_element, "response_callback"):
                return scope_element.response_callback(
                    method=method,
                    path=path,
                    content=content,
                    code=code,
                    headers=headers,
                )
