# openshift-automation-grafana

Automation of the data source and dashboard creation process for OpenShift clusters.

* This script is written for Python 3.6.

* The Python app is deployed using OpenShift's source to image (S2i) build process.

* Entrypoint for the app is [app.py](app.py)

The purpose of this script is to automate the creation of dashboards and their respective data sources, for the number of OpenShift clusters which the customer has.

## Prerequisites

1. Have a Grafana instance deployed which has a route exposed as well as a [API key](https://grafana.com/docs/grafana/latest/http_api/auth/#create-api-token) generated.

2. Ensure that the router IP of the cluster which this pod will be running in is whitelisted on the Grafana route in the destination cluster.

3. Create a new OpenShift project using the following command: `oc new-project grafana-automation`

4. Create an OpenShift secret using the following command: `oc create -f secret.yaml`

    Example secret.yaml:

    ```yaml
    apiVersion: v1
    kind: Secret
    metadata:
      name: customer-secret
      namespace: grafana-automation
    type: Opaque
    stringData:
      customer_clusters.yaml: |-
        ---
        Customers:
          CustomerA:
          - ClusterDataSourceUrl: https://cluster1.prometheus.com
            BasicAuthUsername: xxxxx
            BasicAuthPassword: xxxxx
          - ClusterDataSourceUrl: https://cluster2.prometheus.com
            BasicAuthUsername: xxxxx
            BasicAuthPassword: xxxxx
          CustomerB:
          - ClusterDataSourceUrl: https://cluster3.prometheus.com
            BasicAuthUsername: xxxxx
            BasicAuthPassword: xxxxx
          - ClusterDataSourceUrl: https://cluster4.prometheus.com
            BasicAuthUsername: xxxxx
            BasicAuthPassword: xxxxx
          - ClusterDataSourceUrl: https://cluster5.prometheus.com
            BasicAuthUsername: xxxxx
            BasicAuthPassword: xxxxx
    ```

5. Deploy this app in OpenShift using the following command:

    ```bash
    Secret=$(oc get secret customer-secret -o "jsonpath={.data['customer_clusters\.yaml']}" | base64 --decode) && oc new-app python:3.6~https://github.com/UKCloud/openshift-automation-grafana.git \
        -e OPENSHIFT_SECRET=$Secret \
        -e GRAFANA_API_KEY="API key here." \
        -e GRAFANA_HOST="https://grafanahost.com"
    ```
