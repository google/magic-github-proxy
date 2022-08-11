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
import argparse

import aiohttp.web

import logging

logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)

parser = argparse.ArgumentParser(description="magicproxy server")
parser.add_argument(
    "--async",
    action="store_true",
    dest="run_async",
    help="run async using aiohttp (single process)",
)
parser.add_argument("--port", type=int, default=5000)
parser.add_argument("--host", type=str, default="127.0.0.1")


if __name__ == "__main__":
    from magicproxy import proxy, async_proxy

    args = parser.parse_args()
    if args.run_async:
        aiohttp.web.run_app(async_proxy.build_app([]), host=args.host, port=args.port)
    else:
        proxy.run_app(host=args.host, port=args.port)
