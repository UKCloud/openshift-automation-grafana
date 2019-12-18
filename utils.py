try:
    import os
    import requests
    import jinja2
except ImportError as err:
    raise ImportError("Failed to import required modules: {}".format(err))


def create_template(datasource_info: list, customer: str):
    """
    Create the Grafana dashboard JSON given a nested list of data source information.
    :param datasource_info: A nested list containing information about the data sources.
    :param customer: The name of the customer, used in dashboard generation.
    :rtype: u'str'.
    """
    template_loader = jinja2.FileSystemLoader("./templates")
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template("dashboardfinal.j2")
    # Create dashboard JSON using Jinja2 template engine.
    dashboard = template.render(title=customer, datasource_names=datasource_info)
    return dashboard


def get_env_vars():
    """
    Get OS environment variables for setup.
    :rtype: A tuple object.
    """
    # This variable contains data sources for customer clusters to add to Grafana.
    openshift_secret = os.environ.get("OPENSHIFT_SECRET", None)
    grafana_api_key = os.environ.get("GRAFANA_API_KEY", None)
    grafana_hostname = os.environ.get("GRAFANA_HOST", None)
    # Check variables are not None.
    ENV_VARS = (openshift_secret, grafana_api_key, grafana_hostname)
    if not all(ENV_VARS):
        raise ValueError("Required environment variables are not defined.")
    return ENV_VARS


def grafana_request(session: requests.Session, sub_endpoint: str, method: str = "POST", **kwargs):
    """
    Helper function to make requests to the Grafana API.
    :param session: A requests.Session() class.
    :param sub_endpoint: The specific Grafana API endpoint.
    :param method: The request method to use.
    :rtype: A JSON response.
    """
    if method == "POST":
        resp = session.post(sub_endpoint, **kwargs)
    elif method == "GET":
        resp = session.get(sub_endpoint, **kwargs)
    else:
        raise ValueError("Invalid request method.")
    if resp.status_code == 200:
        return resp.json()
    else:
        # Raise HTTPError exception.
        raise resp.raise_for_status()
