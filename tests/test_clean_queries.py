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

import os

from magicproxy import queries


def test_cleans_custom_queries():
    queries_to_clean = ['key']
    path = 'https://github.com/orthros?key=123212'
    actual = queries.clean_path_queries(queries_to_clean, path)
    assert actual == 'https://github.com/orthros'


def test_cleans_repeated_custom_queries():
    queries_to_clean = ['key']
    path = 'https://github.com/orthros?key=123212&key=someOtherKey21'
    actual = queries.clean_path_queries(queries_to_clean, path)
    assert actual == 'https://github.com/orthros'

def test_cleans_bare_queries():
    queries_to_clean = ['key']
    path = 'https://github.com/orthros?key='
    actual = queries.clean_path_queries(queries_to_clean, path)
    assert actual == 'https://github.com/orthros'

def test_cleans_repeated_bare_custom_queries():
    queries_to_clean = ['key']
    path = 'https://github.com/orthros?key=&key='
    actual = queries.clean_path_queries(queries_to_clean, path)
    assert actual == 'https://github.com/orthros'

def test_cleans_trailing_queries():
    queries_to_clean = ['key']
    path = 'https://github.com/orthros?someval=&key=123212'
    actual = queries.clean_path_queries(queries_to_clean, path)
    assert actual == 'https://github.com/orthros?someval='

def test_leaves_queries_alone_if_not_set():
    queries_to_clean = []
    path = 'https://github.com/orthros?someval=&key=123212'
    actual = queries.clean_path_queries(queries_to_clean, path)
    assert actual == 'https://github.com/orthros?someval=&key=123212'
