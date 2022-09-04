import os
import shlex
import subprocess
import sys
import time
from random import randrange
from socket import create_connection

import pytest
import requests
from xprocess import ProcessStarter

import magicproxy

API_PORT = randrange(50000, 55000)
API_HOST = "localhost"
API_ROOT = f"http://{API_HOST}:{API_PORT}"
PROXY_PORT = randrange(55000, 60000)
PROXY_HOST = "localhost"
PROXY_ROOT = f"http://{PROXY_HOST}:{PROXY_PORT}"
TIMEOUT = 15

print("API_PORT %s" % API_PORT)
print("PROXY_PORT %s" % PROXY_PORT)


def run(cmd):
    print(" ".join(shlex.quote(s) for s in cmd))
    return (
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        .decode("utf-8")
        .rstrip("\n")
    )


def wait_for_port(host: str, port: int, timeout: float = 5.0):
    start_time = time.perf_counter()
    while True:
        try:
            with create_connection((host, port), timeout=timeout):
                time.sleep(2)
                break
        except Exception as ex:
            time.sleep(0.01)
            if time.perf_counter() - start_time >= timeout:
                raise TimeoutError(
                    "Waited too long for the port {} on host {} to start accepting "
                    "connections.".format(port, host)
                ) from ex


@pytest.fixture(scope="module")
def api_integration(xprocess):
    class ApiStarter(ProcessStarter):
        args = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), "app_integration_test.py"),
            "localhost",
            API_PORT,
        ]

        def startup_check(self):
            try:
                create_connection((API_HOST, API_PORT), timeout=1)
                return True
            except TimeoutError:
                return False

        pattern = rf"Running on {API_ROOT}"

    xprocess.ensure("api", ApiStarter)
    yield
    xprocess.getinfo("api").terminate()


@pytest.fixture(scope="module")
def integration(api_integration, xprocess, request):
    run_async = request.param
    run_args = [sys.executable]
    rcfile = None
    if "COVERAGE_RUN" in os.environ:
        root_dir = os.path.join(os.path.dirname(__file__), "..")
        rcfile = os.path.join(root_dir, ".coveragerc")
        covfile = os.path.join(root_dir, ".coverage")
        omitted = os.path.join(root_dir, "tests/*")
        run_args.extend(
            [
                "-m",
                "coverage",
                "run",
                f"--rcfile={rcfile}",
                f"--data-file={covfile}",
                "-p",
                f"--omit={omitted}",
            ]
        )

    run_args.extend(
        [
            "-m",
            "magicproxy",
            "--host",
            "localhost",
            "--port",
            PROXY_PORT,
        ]
    )
    if run_async:
        run_args.append("--async")
    print(" ".join(str(e) for e in run_args))
    run_env = {
        "API_ROOT": API_ROOT,
        "PYTHONUNBUFFERED": "1",
        "PUBLIC_ACCESS": PROXY_ROOT,
    }
    if "COVERAGE_RUN" in os.environ:
        run_env["COVERAGE_PROCESS_START"] = rcfile

    class ProxyStarter(ProcessStarter):
        args = run_args
        env = run_env
        timeout = 15

        def startup_check(self):
            try:
                create_connection((PROXY_HOST, PROXY_PORT), timeout=1)
                return True
            except TimeoutError:
                return False

        pattern = rf"Running on {PROXY_ROOT}"

    xprocess.ensure("proxy", ProxyStarter)
    yield
    xprocess.getinfo("proxy").terminate()


@pytest.mark.integration
@pytest.mark.parametrize(
    "integration", [True, False], ids=["async", "sync"], indirect=True
)
def test_api_get___magictoken(integration):
    response = requests.get(f"{PROXY_ROOT}/__magictoken")
    assert response.ok
    assert response.status_code == 200

    assert magicproxy.__version__ in response.text
    assert API_ROOT in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    "integration", [True, False], ids=["async", "sync"], indirect=True
)
def test_extra_keys(integration):
    response = requests.post(
        f"{PROXY_ROOT}/__magictoken",
        json={"allowed": ["GET /.*"], "token_": "fake_token"},
    )
    assert not response.ok
    assert response.status_code == 400

    response = requests.post(
        f"{PROXY_ROOT}/__magictoken",
        json={"allowed_": ["GET /.*"], "token": "fake_token"},
    )
    assert not response.ok
    assert response.status_code == 400


@pytest.mark.integration
@pytest.mark.parametrize(
    "integration", [True, False], ids=["async", "sync"], indirect=True
)
def test_api_authorized(integration):
    response = requests.post(
        f"{PROXY_ROOT}/__magictoken",
        json={"allowed": ["GET /.*"], "token": "fake_token"},
    )
    assert response.ok
    assert response.status_code == 200

    proxy_token = response.text

    response = requests.get(
        PROXY_ROOT,
        headers={"Authorization": f"Bearer {proxy_token}"},
    )
    assert response.ok
    assert response.status_code == 200
    assert response.text == "authorized by API"


@pytest.mark.integration
@pytest.mark.parametrize(
    "integration", [True, False], ids=["async", "sync"], indirect=True
)
def test_api_unauthorized(integration):
    response = requests.post(
        f"{PROXY_ROOT}/__magictoken",
        json={"allowed": ["GET /.*"], "token": "wrong_token"},
    )
    assert response.ok
    assert response.status_code == 200

    proxy_token = response.text

    response = requests.get(
        f"{PROXY_ROOT}/",
        headers={"Authorization": f"Bearer {proxy_token}"},
    )
    assert not response.ok
    assert response.status_code == 401
    assert response.text == "not authorized by API"
