# Development - Contributing

Issues and pull requests are more than welcome: https://github.com/developmentseed/eoAPI/issues

**dev install**

```bash
# Download the code
git clone https://github.com/developmentseed/eoAPI.git
cd eoAPI

# Create a virtual environment
python -m pip install --upgrade virtualenv
virtualenv .venv
source .venv/bin/activate

# Install eoapi modules
python -m pip install "psycopg[binary,pool]"
python -m pip install -e runtime/eoapi/raster["test"] -e runtime/eoapi/stac["test"] -e runtime/eoapi/vector["test"]
```

**pre-commit**

This repo is set to use `pre-commit` to run *isort*, *ruff*, *pydocstring*, *black* ("uncompromising Python code formatter") and mypy when committing new code.

```bash
$ pre-commit install
```
