# Development - Contributing

Issues and pull requests are more than welcome: https://github.com/developmentseed/eoAPI/issues

**dev install**

```bash
$ git clone https://github.com/developmentseed/eoAPI.git
$ cd eoAPI
$ pip install \
   pre-commit \
   -e src/eoapi/stac["test"] \
   -e src/eoapi/tiler["test"] \
```

**pre-commit**

This repo is set to use `pre-commit` to run *isort*, *flake8*, *pydocstring*, *black* ("uncompromising Python code formatter") and mypy when committing new code.

```bash
$ pre-commit install
```
