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

from magicproxy import headers


def test_clean_request_headers_strips_custom_headers():
    request_headers_to_clean = ["X-Custom-Me"]
    hdrs = dict()
    hdrs["X-Custom-Me"] = "A Custom Value"
    actual = headers.clean_request_headers(hdrs, request_headers_to_clean)
    assert "X-Custom-Me" not in actual


def test_strips_custom_headers():
    request_headers_to_clean = ["X-Custom-Me"]
    hdrs = dict()
    hdrs["X-Custom-Me"] = "A Custom Value"
    actual = headers.clean_request_headers(hdrs, request_headers_to_clean)
    assert "X-Custom-Me" not in actual


def test_leaves_headers_alone_if_undefined():
    request_headers_to_clean = []
    hdrs = dict()
    hdrs["X-Custom-Me"] = "A Custom Value"
    actual = headers.clean_request_headers(hdrs, request_headers_to_clean)
    assert hdrs == actual
