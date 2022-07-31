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
from urllib.parse import urlparse

import nox

from magicproxy.config import PRIVATE_KEY_LOCATION, PUBLIC_KEY_LOCATION


@nox.session(py=False)
def create_token(session):
    import requests

    if 'PUBLICLY_ACCESSIBLE' not in os.environ:
        url = input("Enter the URL for your API (https://example.com): ")
    else:
        url = os.environ['PUBLICLY_ACCESSIBLE']
    token = input("Enter your API Token: ")
    scopes = input("Enter a comma-separate list of scopes: ")

    url += "/__magictoken"
    scopes = [x.strip() for x in scopes.split(",") if x != ""]

    request_data = {"token": token, "scopes": scopes}

    resp = requests.post(url, json=request_data)
    resp.raise_for_status()

    print(resp.text)


@nox.session(py=False)
def generate_keys(session):
    # Preferentially use Homebrew OpenSSL, as MacOS version is horrifically out
    # of date.
    if os.path.exists("/usr/local/opt/openssl/bin/openssl"):
        openssl = "/usr/local/opt/openssl/bin/openssl"
    else:
        openssl = "openssl"

    os.makedirs(os.path.dirname(PRIVATE_KEY_LOCATION), exist_ok=True)
    os.makedirs(os.path.dirname(PUBLIC_KEY_LOCATION), exist_ok=True)

    if 'PUBLICLY_ACCESSIBLE' not in os.environ:
        url = input("Enter the URL for your API (https://example.com): ")
    else:
        url = os.environ['PUBLICLY_ACCESSIBLE']

    hostname = urlparse(url).hostname

    session.run(
        openssl,
        "genpkey",
        "-algorithm",
        "RSA",
        "-out",
        PRIVATE_KEY_LOCATION,
        "-pkeyopt",
        "rsa_keygen_bits:2048",
    )

    session.run(
        openssl, "rsa", "-pubout", "-in", PRIVATE_KEY_LOCATION, "-out", PUBLIC_KEY_LOCATION
    )

    session.run(
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


@nox.session(python="3.8")
def blacken(session):
    session.install("black")
    session.run("black", "src/magicproxy", "tests", "setup.py", "noxfile.py")


@nox.session(python="3.8")
def lint(session):
    session.install("mypy", "flake8", "black")
    session.run("pip", "install", "-e", ".")
    session.run("black", "--check", "src/magicproxy", "tests")
    session.run("flake8", "src/magicproxy", "tests")
    session.run(
        "mypy", "--no-strict-optional", "--ignore-missing-imports", "src/magicproxy"
    )


@nox.session(python="3.8")
def test(session):
    session.install("pytest")
    session.run("pip", "install", "-e", ".")
    session.run("pytest", "tests", *session.posargs)
