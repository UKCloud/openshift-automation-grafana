try:
    from utils import get_env_vars, grafana_request, create_template
    from requests_toolbelt import sessions
    from requests import HTTPError
    import yaml
    import logging
    from sys import stdout
    from time import sleep
except ImportError as err:
    raise ImportError("Failed to import required modules: {}".format(err))


def main():
    # Setup logfile and stdout logging.
    logging.basicConfig(filename="grafana_setup.log", level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler(stdout))
    # Load required environment variables.
    ENV_VARS = get_env_vars()
    logging.debug("Environment variables are: {}".format(ENV_VARS))
    # Load env variable as YAML structure.
    customer_datasources = yaml.safe_load(ENV_VARS[0])
    # Init requests.Session() object.
    session = sessions.BaseUrlSession(base_url=ENV_VARS[2])
    # All subsequent requests will use these headers.
    session.headers.update(
        {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(ENV_VARS[1]),
        }
    )
    # Loop over data sources, creating a data source for the number of clusters in the YAML structure.
    # Also, create dashboard with panels.
    for customer in customer_datasources["Customers"]:
        # Define datasource_info list for template creation.
        datasource_info = []
        for cluster in customer_datasources["Customers"][customer]:
            clustername = cluster["ClusterDataSourceUrl"].split("prometheus.")[1].strip("/")
            name = "{}-{}".format(customer, clustername)
            # Add data source name to list.
            datasource_info.append([name, clustername])
            # Create data source.
            logging.debug("Creating data source for customer: {} cluster: {}".format(customer, clustername))
            datasource = {
                "name": name,
                "type": "prometheus",
                "url": cluster["ClusterDataSourceUrl"],
                "access": "server",
                "basicAuth": True,
                "basicAuthUser": cluster["BasicAuthUsername"],
                "basicAuthPassword": cluster["BasicAuthPassword"],
                "isDefault": False
            }
            try:
                # Send request to create Grafana data source.
                resp = grafana_request(session, sub_endpoint="/api/datasources", method="POST", json=datasource)
                logging.debug("JSON response for data source creation: data source: {}\n JSON payload: {}".format(cluster["ClusterDataSourceUrl"], resp))
                # Sleep for a second to avoid Grafana raising 409 conflict error.
                sleep(1)
            except HTTPError as err:
                logging.debug("Request to create Grafana data source failed: {}\nJSON payload: {}".format(err, datasource))
        # Create dashboard JSON using Jinja2 template engine.
        dashboard = create_template(datasource_info, customer)
        try:
            # Send request to create Grafana dashboard.
            resp = grafana_request(session, sub_endpoint="/api/dashboards/db", method="POST", data=dashboard)
            logging.debug("JSON response for dashboard creation: dashboard: {}\nJSON payload: {}".format(customer, resp))
        except HTTPError as err:
            logging.debug("Request to create Grafana dashboard failed: {}\nJSON payload: {}".format(err, dashboard))
    # Close HTTP session once finished.
    session.close()


if __name__ == "__main__":
    __version__ = "0.0.1"
    main()
