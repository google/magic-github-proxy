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
import logging
from typing import Set

import aiohttp
import aiohttp.web

import magicproxy
from magicproxy.magictoken import magictoken_params_validate
from . import magictoken
from . import queries
from . import scopes
from .config import Config, load_config
from .headers import clean_request_headers, clean_response_headers

routes = aiohttp.web.RouteTableDef()
logger = logging.getLogger(__name__)

query_params_to_clean: Set[str] = set()
custom_request_headers_to_clean: Set[str] = set()


@routes.get("/__magictoken")
async def magic_token_version(request):
    CONFIG = request.app["CONFIG"]
    return aiohttp.web.Response(
        body="magic API proxy for "
        + CONFIG.api_root
        + " version "
        + magicproxy.__version__
    )


@routes.post("/__magictoken")
async def create_magic_token(request):
    CONFIG = request.app["CONFIG"]
    params = await request.json()

    try:
        magictoken_params_validate(CONFIG, params)
    except ValueError as e:
        raise aiohttp.web.HTTPBadRequest(body=str(e))

    token = magictoken.create(
        CONFIG.keys, params["token"], params.get("scopes"), params.get("allowed")
    )

    return aiohttp.web.Response(body=token, headers={"Content-Type": "application/jwt"})


async def _proxy_request(request, url, headers=None, **kwargs):
    clean_headers = clean_request_headers(
        request.headers, custom_request_headers_to_clean
    )

    if headers:
        clean_headers.update(headers)

    print(f"Proxying to {request.method} {url}\n")

    async with aiohttp.ClientSession() as session:
        proxied_request = session.request(
            url=url,
            method=request.method,
            headers=clean_headers,
            params=request.query,
            data=request.content,
            **kwargs,
        )
        async with proxied_request as proxied_response:
            response_headers = clean_response_headers(proxied_response.headers)

            response = aiohttp.web.StreamResponse(
                status=proxied_response.status, headers=response_headers
            )

            await response.prepare(request)

            async for data, last in proxied_response.content.iter_chunks():
                await response.write(data)

            await response.write_eof()

            return data, proxied_response.status, proxied_response.headers


@routes.route("*", "/{path:.*}")
async def proxy_api(request):
    CONFIG = request.app["CONFIG"]
    path = request.match_info["path"]

    auth_token = request.headers.get("Authorization")
    if auth_token is None:
        raise aiohttp.web.HTTPForbidden(body="No authorization token presented")

    # strip out "Bearer " if needed
    if auth_token.startswith("Bearer "):
        auth_token = auth_token[len("Bearer ") :]

    # Validate the magic token
    token_info = magictoken.decode(CONFIG.keys, auth_token)

    # Validate scopes againt URL and method.
    if not scopes.validate_request(
        CONFIG, request.method, request.path, token_info.scopes, token_info.allowed
    ):
        raise aiohttp.web.HTTPForbidden(body="Disallowed by API proxy.")

    path = queries.clean_path_queries(query_params_to_clean, path)

    response = await _proxy_request(
        request=request,
        url=f"{CONFIG.api_root}/{path}",
        headers={"Authorization": f"Bearer {token_info.token}"},
    )

    try:
        scopes.response_callback(request.method, path, *response, token_info.scopes)
    except Exception as e:
        logger.error(e)
    return response


async def build_app(config: Config = None):
    app = aiohttp.web.Application()
    if config is None:
        config = load_config()
    app["CONFIG"] = config
    app.add_routes(routes)
    return app


def run_app(host, port, config: Config = None):
    app = build_app(config)
    aiohttp.web.run_app(app, host=host, port=port)
    return app
