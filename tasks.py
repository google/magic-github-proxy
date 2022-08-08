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

from magicproxy.config import PUBLIC_ACCESS
from magicproxy.crypto import generate_keys


@task
def create_token(c):
    import requests

    url = (
        PUBLIC_ACCESS
        if PUBLIC_ACCESS
        else input("Enter the URL for your proxy (https://example.com): ")
    )
    token = input("Enter your API Token: ")
    permissions = input("Enter a comma-separate list of permissions: ")

    url += "/__magictoken"
    permissions = [x.strip() for x in permissions.split(",") if x != ""]

    request_data = {"token": token, "permissions": permissions}

    resp = requests.post(url, json=request_data)
    resp.raise_for_status()

    print(resp.text)


@task
def generate_keys(c, url=None):
    if url is None and PUBLIC_ACCESS is None:
        url = input("Enter the URL for your proxy (https://example.com): ")
    generate_keys(url)


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
