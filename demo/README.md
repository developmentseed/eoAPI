# Demo Runner

The demos can be run from a Docker Compose service instead of from your host
Python environment. The container includes Jupyter, `pypgstac`, `rio-stac`,
AWS/S3 clients, and the Python libraries used by the notebooks.

Start the main stack and the demo notebook server:

```bash
docker compose --profile demo up -d --build demo-runner
```

Open Jupyter at:

```text
http://127.0.0.1:8888
```

The repository's `demo/` directory is bind-mounted at `/workspace/demo` in the
demo containers, so notebook edits and generated demo files are visible without
rebuilding the image.

Load demo data into the local pgSTAC database with the named Compose targets:

```bash
docker compose run --rm demo-noaa
docker compose run --rm demo-facebook
docker compose run --rm demo-cmip6
docker compose run --rm demo-oam
```

Load every available demo dataset:

```bash
docker compose run --rm demo-all
```

You can also call the loader directly from the notebook image:

```bash
docker compose run --rm demo-runner load-demos noaa facebook
```

`all` loads the static NOAA and Facebook data and also loads generated CMIP6
or OAM data if the corresponding item files already exist. Generate those files
from their notebooks first, or use the existing checked-out generated files when
available.

Inside the demo container, use Compose service URLs:

```text
DATABASE_URL=postgresql://username:password@database:5432/postgis
STAC_API_URL=http://stac-fastapi:8080
TITILER_URL=http://titiler-pgstac
```

From your host browser, keep using the published ports:

```text
STAC API: http://127.0.0.1:8081
TiTiler:  http://127.0.0.1:8082
Browser:  http://127.0.0.1:8085
```
