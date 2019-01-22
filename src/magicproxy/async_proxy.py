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

import aiohttp
import aiohttp.web

import os

from . import magictoken
from . import scopes
from . import headers
from . import queries

GITHUB_API_ROOT = "https://api.github.com"

routes = aiohttp.web.RouteTableDef()

query_params_to_clean = set()
custom_request_headers_to_clean = set()

@routes.post("/magictoken")
async def create_magic_token(request):
    params = await request.json()

    if not params:
        raise aiohttp.web.HTTPInvalidRequest("Request must be json.")

    if not isinstance(params.get("scopes"), list):
        raise aiohttp.web.HTTPInvalidRequest("Scopes must be a list.")

    token = magictoken.create(keys, params["github_token"], params["scopes"])

    return aiohttp.web.Response(body=token, headers={"Content-Type": "application/jwt"})


async def _proxy_request(request, url, headers=None, **kwargs):
    clean_headers = headers.clean_request_headers(request.headers, custom_request_headers_to_clean)

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
            response_headers = headers.clean_response_headers(proxied_response.headers)

            response = aiohttp.web.StreamResponse(
                status=proxied_response.status, headers=response_headers
            )

            await response.prepare(request)

            async for data, last in proxied_response.content.iter_chunks():
                await response.write(data)

            await response.write_eof()

            return response


@routes.route("*", "/{path:.*}")
async def proxy_api(request):
    path = request.match_info["path"]

    auth_token = request.headers["Authorization"]

    # strip out "Bearer " if needed
    if auth_token.startswith("Bearer "):
        auth_token = auth_token[len("Bearer ") :]

    # Validate the magic token
    token_info = magictoken.decode(keys, auth_token)

    # Validate scopes againt URL and method.
    if not scopes.validate_request(request.method, request.path, token_info.scopes):
        raise aiohttp.web.HTTPForbidden(
            f"Disallowed by GitHub proxy. Allowed scopes: {', '.join(token_info.scopes)}"
        )

    path = queries.clean_path_queries(query_params_to_clean, path)

    return await _proxy_request(
        request=request,
        url=f"{GITHUB_API_ROOT}/{path}",
        headers={"Authorization": f"Bearer {token_info.github_token}"},
    )


async def build_app(argv):
    global keys
    keys = magictoken.Keys.from_env()

    app = aiohttp.web.Application()
    app.add_routes(routes)
    return app


if __name__ == "__main__":
    aiohttp.web.run_app(build_app([]))
