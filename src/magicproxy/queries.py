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

from urllib.parse import  parse_qsl, urlencode, urlparse, urlunparse


def clean_path_queries(query_params_to_clean, path) -> str:
    parts = urlparse(path)
    queries = parse_qsl(parts.query, keep_blank_values=True, strict_parsing=True)
    cln = [q for q in queries if q[0] not in query_params_to_clean]
    return urlunparse((parts.scheme, parts.netloc, parts.path, parts.params, urlencode(cln), parts.fragment))
