
Issues and pull requests are more than welcome: https://github.com/developmentseed/eoAPI/issues

You can also start **Discussions** in https://github.com/developmentseed/eoAPI/discussions

**dev install**

```bash
# Download the code
git clone https://github.com/developmentseed/eoAPI.git
cd eoAPI

# Create a virtual environment
python -m pip install --upgrade virtualenv
virtualenv .venv
source .venv/bin/activate

# Install eoapi module
python -m pip install "psycopg[binary,pool]"
python -m pip install -e runtime/eoapi/raster["test"] # or -e runtime/eoapi/stac["test"]  | -e runtime/eoapi/vector["test"]
```

!!! danger

    Python applications might have incompatible dependencies which you can resolve by using virtual environment *per application*

**pre-commit**

This repo is set to use `pre-commit` to run *isort*, *ruff*, *pydocstring*, *black* ("uncompromising Python code formatter") and mypy when committing new code.

```bash
$ pre-commit install
```

### Open Source

You can also contribute indirectly to eoAPI by helping on the sub-modules:

- **PgSTAC** database https://github.com/stac-utils/pgstac
- **stac-fastapi**: https://github.com/stac-utils/stac-fastapi
- **titiler-pgstac**:  https://github.com/stac-utils/titiler-pgstac
- **TiTiler**: https://github.com/developmentseed/titiler
- **TiPg**: https://github.com/developmentseed/tipg
