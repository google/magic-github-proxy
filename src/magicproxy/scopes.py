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
from typing import List


def validate_request(method: str, path: str, scopes: List[str]) -> bool:
    """Basic scope validation routine.

    Args:
        method: The HTTP method.
        path: The request path.
        scopes: The list of allowed scopes.

    The scope must be in the format:

        METHOD path

    For example:

        GET /user
        POST /repos/+?/+?/issues/+?/labels

    Would allow getting the user info and updating labels on issues.
    """
    validated = False
    for scope in scopes:
        allowed_method, allowed_path = scope.split(" ", 1)

        if method != allowed_method and allowed_method != "*":
            continue

        if not path.startswith("/"):
            path = f"/{path}"

        if re.match(allowed_path, path, re.I):
            validated = True
            break

    return validated
