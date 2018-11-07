import os

import nox


@nox.session(py=False)
def get_magic_token(session):
    import requests

    url = input("Enter the URL for your github proxy (https://example.com): ")
    github_token = input("Enter your GitHub API Token: ")
    scopes = input("Enter a comma-separate list of scopes: ")

    url += "/magictoken"
    scopes = [x.strip() for x in scopes.split(",")]

    request_data = {"github_token": github_token, "scopes": scopes}

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

    session.run(
        openssl,
        "genpkey",
        "-algorithm",
        "RSA",
        "-out",
        "keys/private.pem",
        "-pkeyopt",
        "rsa_keygen_bits:2048",
    )

    session.run(
        openssl, "rsa", "-pubout", "-in", "keys/private.pem", "-out", "keys/public.pem"
    )

    session.run(
        openssl,
        "req",
        "-batch",
        "-subj",
        "/C=US/CN=github-proxy.thea.codes",
        "-new",
        "-x509",
        "-key",
        "keys/private.pem",
        "-out",
        "keys/public.x509.cer",
        "-days",
        "1825",
    )
