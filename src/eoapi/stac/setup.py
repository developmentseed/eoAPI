"""Setup stac_tiler.stac."""

from setuptools import find_namespace_packages, setup

with open("README.md") as f:
    long_description = f.read()

inst_reqs = [
    "stac-fastapi.api~=2.0",
    "stac-fastapi.types~=2.0",
    "stac-fastapi.extensions~=2.0",
    "stac-fastapi.pgstac~=2.0",
]

extra_reqs = {
    "test": ["pytest", "pytest-cov", "pytest-asyncio", "requests"],
}


setup(
    name="eoapi.stac",
    description=u"",
    python_requires=">=3.6",
    packages=find_namespace_packages(exclude=["tests*"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
