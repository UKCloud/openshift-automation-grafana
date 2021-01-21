#!/usr/bin/env python3
"""
    Create Grafana dashboards in Grafana in the management cluster for
    all customer clusters.
"""

try:
    from utils import get_env_vars, grafana_request, create_customer_template, create_admin_template
    from requests_toolbelt import sessions
    from requests import HTTPError
    import yaml
    import logging
    import os
    from sys import stdout
    from time import sleep
except ImportError as err:
    raise ImportError("Failed to import required modules: {}".format(err))


def main():
    logging.basicConfig(filename="grafana_setup.log", level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler(stdout))

    dashboard_sources = yaml.safe_load(os.environ['DASHBOARD_SOURCES'])

    session = sessions.BaseUrlSession(base_url=os.environ['GRAFANA_URL'])
    session.headers.update(
        {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ['GRAFANA_API_TOKEN']}",
        }
    )

    for customer in dashboard_sources["Customers"]:
        datasource_info = []
        for cluster in dashboard_sources["Customers"][customer]:
            # v3 urls like https://prometheus.<domainSuffix>
            # v4 urls like https://prometheus-k8s-openshift-monitoring.apps.<domainSuffix>
            # domainSuffix like 1234-567890.reg00001-1.cna.ukcloud.com
            clustername = ".".join(cluster["ClusterDataSourceUrl"].split(".")[-5:])
            name = "{}-{}".format(customer, clustername)
            datasource_info.append([name, clustername])

            logging.debug(f"Creating data source for customer: {customer} cluster: {clustername}")
            datasource = {
                "name": name,
                "type": "prometheus",
                "url": cluster["ClusterDataSourceUrl"],
                "access": "proxy",
                "basicAuth": True,
                "basicAuthUser": cluster["BasicAuthUsername"],
                "basicAuthPassword": cluster["BasicAuthPassword"],
                "isDefault": False
            }
            try:
                resp = grafana_request(session, sub_endpoint="/api/datasources", method="POST", json=datasource)
                logging.debug(f"JSON response for data source creation: data source: {cluster['ClusterDataSourceUrl']}\n"
                              f"JSON payload: {resp}")
                # Sleep for a second to avoid Grafana raising 409 conflict error.
                sleep(1)
            except HTTPError as err:
                logging.debug(f"Failed to create Grafana data source: {err}\n"
                              f"JSON payload: {datasource}")
        dashboard = create_customer_template(datasource_info, customer)
        try:
            resp = grafana_request(session, sub_endpoint="/api/dashboards/db", method="POST", data=dashboard)
            logging.debug(f"JSON response for dashboard creation: dashboard: {customer}\n"
                          f"JSON payload: {resp}")
        except HTTPError as err:
            logging.debug(f"Failed to create Grafana dashboard: {err}\n"
                          f"JSON payload: {dashboard}")
    admin_dashboard = create_admin_template()
    try:
        resp = grafana_request(session, sub_endpoint="/api/dashboards/import", method="POST", data=admin_dashboard)
        logging.debug(f"JSON response for admin dashboard creation \n"
                      f"JSON payload: {resp}")
    except HTTPError as err:
        logging.debug(f"Failed to create Grafana dashboard: {err}\n"
                      f"JSON payload: {dashboard}")
    session.close()


if __name__ == "__main__":
    __version__ = "1.0.0"
    main()
