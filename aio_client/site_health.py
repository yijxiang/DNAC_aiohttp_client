from aio_client.helper import create_url
from aio_client.request import async_get


async def site_health(session, timestamp):
    """ Site health api call request
    """
    url = create_url(f'site-health?timestamp={timestamp}')
    return await async_get(session, url)


def site_health_data(data):
    """ Site health json response parse
        return all building with clients or network devices
    """
    site_has_clients = []
    _data = data["response"]
    if not _data:
        return []

    for one in _data:
        if ("siteType" in one.keys()) or ("numberOfClients" in one.keys()) or ("numberOfNetworkDevice" in one.keys()):
            if ("building" == one["siteType"]) and (one["numberOfClients"] or one["numberOfNetworkDevice"]):
                if "All Buildings" not in one["siteName"]:
                    site_has_clients.append(one)

    return site_has_clients
