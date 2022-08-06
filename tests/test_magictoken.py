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

from magicproxy import magictoken

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "data")
KEYS = magictoken.Keys.from_files(
    private_key_file=os.path.join(DATA, "private.pem"),
    certificate_file=os.path.join(DATA, "public.x509.cer"),
)


def test_create_and_decode():
    api_token = "this is a token"
    scopes = ["a", "b", "c"]

    result = magictoken.create(KEYS, api_token, scopes)

    # Make sure that the api token does not appear in plaintext
    assert api_token not in result

    decoded = magictoken.decode(KEYS, result)

    assert decoded.token == api_token
    assert scopes == scopes


def test_get_from_env_and_decode():
    local_keys = magictoken.Keys.from_files(
        os.path.join(DATA, "private.pem"), os.path.join(DATA, "public.x509.cer")
    )

    token = "this is a token"
    scopes = ["a", "b", "c"]

    result = magictoken.create(local_keys, token, scopes)

    # Make sure that the token does not appear in plaintext
    assert token not in result

    decoded = magictoken.decode(local_keys, result)

    assert decoded.token == token
    assert scopes == scopes
