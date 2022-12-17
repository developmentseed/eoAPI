"""Setup stac_tiler.stac."""

from setuptools import find_namespace_packages, setup

with open("README.md") as f:
    long_description = f.read()

inst_reqs = [
    "stac-fastapi.api~=2.4",
    "stac-fastapi.types~=2.4",
    "stac-fastapi.extensions~=2.4",
    "stac-fastapi.pgstac~=2.4",
    "jinja2>=2.11.2,<4.0.0",
    "pygeoif==0.7",
    "starlette-cramjam>=0.3,<0.4",
    "importlib_resources>=1.1.0;python_version<'3.9'",
    "psycopg_pool",
]

extra_reqs = {
    "test": ["pytest", "pytest-cov", "pytest-asyncio", "requests"],
}


setup(
    name="eoapi.stac",
    description="",
    python_requires=">=3.7",
    packages=find_namespace_packages(exclude=["tests*"]),
    package_data={"eoapi": ["stac/templates/*.html"]},
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
