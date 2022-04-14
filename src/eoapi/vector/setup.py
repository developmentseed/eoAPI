"""Setup eoapi.vector."""

from setuptools import find_namespace_packages, setup

with open("README.md") as f:
    long_description = f.read()

inst_reqs = ["timvt>=0.6.0,<0.7"]


setup(
    name="eoapi.vector",
    description="",
    python_requires=">=3.7",
    packages=find_namespace_packages(exclude=["tests*"]),
    package_data={"eoapi": ["vector/sql/*.sql"]},
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
)
