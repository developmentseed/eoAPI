"""Setup eoapi.features."""

from setuptools import find_namespace_packages, setup

with open("README.md") as f:
    long_description = f.read()

inst_reqs = [
    "asyncpg>=0.23.0",
    "buildpg>=0.3",
    "fastapi>=0.73.0",
    "jinja2>=2.11.2,<4.0.0",
    "starlette-cramjam>=0.1.0,<0.2",
    "geojson_pydantic",
    "orjson",
]

extra_reqs = {
    "test": ["pytest", "pytest-cov", "pytest-asyncio", "requests"],
}


setup(
    name="eoapi.features",
    description="",
    python_requires=">=3.7",
    packages=find_namespace_packages(exclude=["tests*"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
