# Builds

Productivity metrics on things like build times.

The default example here uses: 
- GCP's GCS to save state. The libraries also support AWS S3.
- BigQuery for storing build metrics + Looker Studio for the dashboard
- GitHub Actions and workflows as the CI/CD tool.

# Requirements
- GCP or AWS account with their CLI tool installed and the appropriate credentials.
- A bucket already created. Infrastructure code is outside the scope of this example runner.
- a GCP project and dataset already created

## settings.toml
Contains the default settings. They should be self explanatory. Though to get the workflow ID, you may need to curl:
```bash
https://api.github.com/repos/<owner>/<repo>/actions/workflows
```

## .secrets.toml
This isn't checked in so your infrastructure code needs to add/mount it.

```toml
dynaconf_merge = true
access_token = "your github access token"
```

## Running it manually
```bash
# only once to set default project
gcloud config set project $MY_PROJECT_ID 
gcloud auth application-default login
uv run --no-cache main.py
```
