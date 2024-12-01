# Persistent store / state manager for metrics projects

An interface and different implementations on how to store state for metrics projects.
Projects can be a few different types:

* Event driven where the project is always running and subscribes to some event. It then pushes into a data lake of some sort
* Long polling where the project is always running and pulls some diff or state (not recommended)
* A cron-like job where it runs periodically

The cron like job will want to store things like its last run date so that whatever tooling it's calling e.g. a buildkite or gitlab or something, it only gets the changes since the last run date for obvious reasons.

This state manager library provides an interface and different implementations including options like storing last run dates in AWS S3 or GCP cloud storage as a cost effective and highly available option suitable for many metrics applications.

Interfaces can be extended to use databases though if necessary.

## Layout

* `interfaces.py` contains the main interfaces
* `gcs.py` is the GCP cloud storage implementation
* `s3.py` is the AWS S3 implementation
