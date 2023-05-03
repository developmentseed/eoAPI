"""Setup eoapi.raster."""

from setuptools import find_namespace_packages, setup

with open("README.md") as f:
    long_description = f.read()

inst_reqs = [
    "titiler.pgstac==0.3.2",
    "starlette-cramjam>=0.3,<0.4",
    "importlib_resources>=1.1.0;python_version<'3.9'",
]

extra_reqs = {
    # https://www.psycopg.org/psycopg3/docs/api/pq.html#pq-module-implementations
    "psycopg": ["psycopg[pool]"],  # pure python implementation
    "psycopg-c": ["psycopg[c,pool]"],  # C implementation of the libpq wrapper
    "psycopg-binary": ["psycopg[binary,pool]"],  # pre-compiled C implementation
    "test": ["pytest", "pytest-cov", "pytest-asyncio", "requests"],
}


setup(
    name="eoapi.raster",
    description="",
    python_requires=">=3.7",
    packages=find_namespace_packages(exclude=["tests*"]),
    package_data={"eoapi": ["raster/templates/*.html"]},
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
