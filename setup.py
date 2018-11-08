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

from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="github-magic-proxy",
    version="2018.11.08",
    description="A stateless GitHub proxy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/theacodes/magic-github-proxy",
    author="Alethea Katherine Flowers",
    author_email="me@thea.codes",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    keywords="github proxy",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=["google-auth", "flask", "cryptography", "attrs", "requests"],
    python_requires=">=3.6",
    project_urls={
        "Bug Reports": "https://github.com/theacodes/magic-github-proxy/issues",
        "Source": "https://github.com/theacodes/magic-github-proxy",
    },
)
