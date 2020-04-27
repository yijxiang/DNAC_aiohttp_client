from helper import create_url
from request import async_get

site_health_tags_keys = [
    "siteName",
    "siteId",
    "parentSiteId",
    "parentSiteName",
    "siteType",
    "latitude",
    "longitude"
]


async def site_health(session, timestamp, dnac):
    """ Site health api get request
    """
    return await async_get(session, create_url(f'site-health?timestamp={timestamp}', dnac))


def site_health_data(data):
    """ Site health json response parse
        return all building with clients or network devices
    """
    site_has_clients = []
    _data = data["response"]
    if not _data:
        return []

    for one in _data:

        if one.get("siteType"):
            if "building" in one["siteType"] and one["numberOfNetworkDevice"]:
                if "All Buildings" not in one["siteName"]:
                    site_has_clients.append(one)

    return site_has_clients


def site_health_to_influx(data):
    _site_health = []
    for _data in data:
        _influx_data = {}
        _influx_data["tags"] = {k: _data[k] for k in site_health_tags_keys if k in _data.keys()}
        _influx_data["fields"] = {k: _data[k] for k in _data.keys() if k not in site_health_tags_keys}
        _influx_data["measurement"] = "site_health"
        _site_health.append(_influx_data)

    return _site_health
