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


DEFAULT_REMOVED_REQUEST_HEADERS = {"Host", "Connection", "Authorization"}

DEFAULT_REMOVED_RESPONSE_HEADERS = {
    "Content-Length",
    "Content-Encoding",
    "Transfer-Encoding",
}


def clean_request_headers(headers, custom_clean_headers):
    """Removes HTTP Headers for a Request

    Args:
      headers: the HTTP headers of the request
      custom_clean_headers: a list of additional headers to remove

    Returns:
      HTTP headers that have been cleaned of unwanted values
    """
    headers = dict(headers)
    for rmv in DEFAULT_REMOVED_REQUEST_HEADERS.union(custom_clean_headers):
        headers.pop(rmv, None)
    return headers


def clean_response_headers(headers):
    """Removes HTTP Headers for a Response

    Args:
      headers: the HTTP headers of the response

    Returns:
      HTTP headers that have been cleaned of unwanted values
    """
    headers = dict(headers)
    for rmv in DEFAULT_REMOVED_RESPONSE_HEADERS:
        headers.pop(rmv, None)
    headers["X-Thea-Codes-GitHub-Proxy"] = "1.1"
    return headers
