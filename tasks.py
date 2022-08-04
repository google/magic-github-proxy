# Copyright 2018 Google LLC and 2022 Matthieu Berthomé
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
import sys

from invoke import task

import os
from urllib.parse import urlparse

from magicproxy.config import PRIVATE_KEY_LOCATION, PUBLIC_KEY_LOCATION, PUBLIC_ACCESS


@task
def create_token(c):
    import requests

    url = (
        PUBLIC_ACCESS
        if PUBLIC_ACCESS
        else input("Enter the URL for your proxy (https://example.com): ")
    )
    token = input("Enter your API Token: ")
    scopes = input("Enter a comma-separate list of scopes: ")

    url += "/__magictoken"
    scopes = [x.strip() for x in scopes.split(",") if x != ""]

    request_data = {"token": token, "scopes": scopes}

    resp = requests.post(url, json=request_data)
    resp.raise_for_status()

    print(resp.text)


@task
def generate_keys(c):
    # Preferentially use Homebrew OpenSSL, as MacOS version is horrifically out
    # of date.
    if os.path.exists("/usr/local/opt/openssl/bin/openssl"):
        openssl = "/usr/local/opt/openssl/bin/openssl"
    else:
        openssl = "openssl"

    os.makedirs(os.path.dirname(PRIVATE_KEY_LOCATION), exist_ok=True)
    os.makedirs(os.path.dirname(PUBLIC_KEY_LOCATION), exist_ok=True)

    url = (
        PUBLIC_ACCESS
        if PUBLIC_ACCESS
        else input("Enter the URL for your proxy (https://example.com): ")
    )

    parsed = urlparse(url)
    if not parsed.hostname:
        raise ValueError("need an url")
    hostname = str(parsed.hostname)

    c.run(
        openssl,
        "genpkey",
        "-algorithm",
        "RSA",
        "-out",
        PRIVATE_KEY_LOCATION,
        "-pkeyopt",
        "rsa_keygen_bits:2048",
    )

    c.run(
        openssl,
        "rsa",
        "-pubout",
        "-in",
        PRIVATE_KEY_LOCATION,
        "-out",
        PUBLIC_KEY_LOCATION,
    )

    c.run(
        openssl,
        "req",
        "-batch",
        "-subj",
        "/CN=" + hostname,
        "-new",
        "-x509",
        "-key",
        PRIVATE_KEY_LOCATION,
        "-out",
        PUBLIC_KEY_LOCATION,
        "-days",
        "1825",
    )


@task
def blacken(c):
    c.run("black src/magicproxy tests setup.py tasks.py")


@task
def lint(c):
    c.run("flake8 src/magicproxy tests")
    c.run("mypy --no-strict-optional --ignore-missing-imports src/magicproxy")


@task
def test(c):
    c.run("pip install -e .")
    args = tuple()
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1 :]

    c.run("pytest tests " + " ".join(args))
