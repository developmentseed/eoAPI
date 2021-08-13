"""Setup stac_tiler.tiler."""

from setuptools import find_namespace_packages, setup

with open("README.md") as f:
    long_description = f.read()

inst_reqs = [
    "titiler.core~=0.3",
    "titiler.mosaic~=0.3",
    "psycopg2-binary",
    "stac-pydantic~=2.0",
]

extra_reqs = {
    "test": ["pytest", "pytest-cov", "pytest-asyncio", "requests"],
}


setup(
    name="eoapi.tiler",
    description=u"",
    python_requires=">=3.6",
    packages=find_namespace_packages(exclude=["tests*"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
