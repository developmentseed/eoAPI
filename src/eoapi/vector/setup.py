"""Setup eoapi.vector."""

from setuptools import find_namespace_packages, setup

with open("README.md") as f:
    long_description = f.read()

inst_reqs = [
    "fastapi>=0.65,<0.68",
    "morecantile>=3.0.0a0,<4.0",
    "psycopg2-binary",
    "buildpg",
    "asyncpg",
    "stac-pydantic~=2.0",
    "geojson-pydantic>=0.3.1,<0.4",
    "jinja2>=3.0,<4.0",
    "importlib_resources>=1.1.0;python_version<'3.9'",
]

extra_reqs = {
    "test": ["pytest", "pytest-cov", "pytest-asyncio", "requests"],
}


setup(
    name="eoapi.vector",
    description=u"",
    python_requires=">=3.7",
    packages=find_namespace_packages(exclude=["tests*"]),
    package_data={"eoapi": ["vector/templates/*.html"]},
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
