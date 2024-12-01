# BigQuery utility library

Helps with setting up datasets and tables with reusable fail-safe logic.

The infrastructure code to setup the project and enabling APIs is out of scope.
Permissions on the final runner is assumed on the node or working runner e.g. K8s pod.
Though adding in options to pass in a service account json file is possible in the future.