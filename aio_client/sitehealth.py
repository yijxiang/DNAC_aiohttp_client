from aio_client.helper import create_url
from aio_client.request import async_get


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
