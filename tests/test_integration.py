import json
import os
import shlex
import subprocess
import sys
import time
from collections import namedtuple
from socket import create_connection

import pytest
import requests

import magicproxy


def run(cmd):
    print(" ".join(shlex.quote(s) for s in cmd))
    return (
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        .decode("utf-8")
        .rstrip("\n")
    )


API_ROOT = "http://api:5000"


def wait_for_port(port: int, host: str = "localhost", timeout: float = 5.0):
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


Integration = namedtuple("Integration", ["proxy_port"])


@pytest.fixture(scope="module")
def api_network_integration():
    api_docker_image = run(
        [
            "docker",
            "build",
            "-q",
            os.path.join(os.path.dirname(__file__), "data", "integration_api"),
        ]
    )
    network = "integration-test-magic-api-proxy"
    try:
        run(["docker", "network", "create", network])
    except subprocess.CalledProcessError as e:
        if f"{network} already exists" not in e.output.decode():
            raise

    api_container = run(
        [
            "docker",
            "run",
            "-d",
            "--rm",
            "--network",
            network,
            "--network-alias",
            "api",
            api_docker_image,
        ]
    )

    subprocess.Popen(["docker", "logs", "-f", api_container], stdout=sys.stdout)

    def cleanup():
        print(run(["docker", "stop", api_container]))
        print(run(["docker", "rmi", api_docker_image]))
        print(run(["docker", "network", "remove", network]))

    try:
        yield network
    finally:
        cleanup()


@pytest.fixture(scope="module")
def integration(api_network_integration, request):
    image_under_test = run(
        ["docker", "build", "-q", os.path.join(os.path.dirname(__file__), "..")]
    )

    cmd = [
        "docker",
        "run",
        "--rm",
        "-d",
        "-P",
        "--expose",
        "5000",
        "-e",
        f"API_ROOT={API_ROOT}",
        "-e",
        "PUBLIC_ACCESS=http://localhost:5000",
        "--network",
        api_network_integration,
        "--network-alias",
        "proxy",
        image_under_test,
        "python",
        "-m",
        "magicproxy",
        "--host",
        "0.0.0.0",
        "--port",
        "5000",
    ]
    if request.param:
        cmd.append("--async")

    proxy_container = run(cmd)

    inspect = json.loads(run(["docker", "inspect", proxy_container]))
    proxy_port = int(inspect[0]["NetworkSettings"]["Ports"]["5000/tcp"][0]["HostPort"])

    def cleanup():
        print(run(["docker", "logs", proxy_container]))
        print(run(["docker", "stop", proxy_container]))

    try:
        wait_for_port(port=proxy_port, timeout=15)
    except TimeoutError:
        cleanup()

    try:
        yield Integration(proxy_port=proxy_port)
    finally:
        cleanup()


@pytest.mark.integration
@pytest.mark.parametrize(
    "integration", [True, False], ids=["async", "sync"], indirect=True
)
def test_api_get___magictoken(integration: Integration):
    response = requests.get(f"http://localhost:{integration.proxy_port}/__magictoken")
    assert response.ok
    assert response.status_code == 200

    assert magicproxy.__version__ in response.text
    assert API_ROOT in response.text


@pytest.mark.integration
@pytest.mark.parametrize(
    "integration", [True, False], ids=["async", "sync"], indirect=True
)
def test_api_authorized(integration: Integration):
    response = requests.post(
        f"http://localhost:{integration.proxy_port}/__magictoken",
        json={"allowed": ["GET /.*"], "token": "fake_token"},
    )
    assert response.ok
    assert response.status_code == 200

    proxy_token = response.text

    response = requests.get(
        f"http://localhost:{integration.proxy_port}/",
        headers={"Authorization": f"Bearer {proxy_token}"},
    )
    assert response.ok
    assert response.status_code == 200
    assert response.text == "authorized by API"


@pytest.mark.integration
@pytest.mark.parametrize(
    "integration", [True, False], ids=["async", "sync"], indirect=True
)
def test_api_unauthorized(integration: Integration):
    response = requests.post(
        f"http://localhost:{integration.proxy_port}/__magictoken",
        json={"allowed": ["GET /.*"], "token": "wrong_token"},
    )
    assert response.ok
    assert response.status_code == 200

    proxy_token = response.text

    response = requests.get(
        f"http://localhost:{integration.proxy_port}/",
        headers={"Authorization": f"Bearer {proxy_token}"},
    )
    assert not response.ok
    assert response.status_code == 401
    assert response.text == "not authorized by API"
