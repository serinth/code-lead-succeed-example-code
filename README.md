# Reusable metrics code for Engineering departments

Written and open sourced by [Code Lead Succeed: Engineering Management in Practice](https://emplaybook.com/)

[![bigquery lib CI](https://github.com/serinth/code-lead-succeed-metrics/actions/workflows/bigquery-lib.yaml/badge.svg)](https://github.com/serinth/code-lead-succeed-metrics/actions/workflows/bigquery-lib.yaml)

[![State Manager CI](https://github.com/serinth/code-lead-succeed-metrics/actions/workflows/state-manager-lib.yaml/badge.svg)](https://github.com/serinth/code-lead-succeed-metrics/actions/workflows/state-manager-lib.yaml)

## Requirements
- Python ^3.13 for most projects (check individual pyproject.toml)
- [uv](https://docs.astral.sh/uv/)


## Running the main project
```bash
#example project for build times
cd /projects/builds
# create a .venv
uv venv
# update your venv and include the lib sources
uv sync --all-extras --dev --no-editable
source .venv/bin/activate
uv run --no-cache main.py
```

## Running tests
```bash
cd /libs/xxx # or /projects/xxx
uv run pytest
```


## Directory layout
- `libs/*` - Reusable libraries that can be published to an artifact store like AWS CodeArtifact or Nexus. Projects can reuse anything in `lib`
- `projects/*` - Everything under projects is a separate and isolated thing that can be deployed independently. They're all just put under this monorepo for easy reference. Projects can use one or more things under `lib`.

### Building packages in libs
```bash
cd /libs/xxx
uv build
```

## Creating configs for new projects
The projects generally use [dynaconf](https://www.dynaconf.com/). To generate your `config.py` with toml, run:
```bash
uvx dynaconf init -f toml
# generates settings.toml and .secrets.toml
```

Put your access token in `.secrets.toml` e.g.
```toml
access_token=<my token>
```

## Building a container
You can reuse the Dockerfile at the top level and just pass in the project path for the runnable.
```bash
# cd into the same directory as the Dockerfile then:
docker build --build-arg PROJECT_PATH="projects/builds" -t <your tag> .
```

## GitHub actions helpers
```bash
# get the workflow ids via the API for configs
# https://api.github.com/repos/<owner>/<repo>/actions/workflows
https://api.github.com/repos/serinth/code-lead-succeed-metrics/actions/workflows
```
