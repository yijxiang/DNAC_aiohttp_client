import time
import aiohttp
import json


async def async_get_auth_token(controller_ip, username, password, DNAC_PORT):
    """ Authenticates with controller and returns a token to be used in subsequent API invocations
    """
    login_url = f"https://{controller_ip}:{DNAC_PORT}/dna/system/api/v1/auth/token"
    async with aiohttp.ClientSession() as session:
        async with session.post(login_url, ssl=False, auth=aiohttp.BasicAuth(username, password)) as resp:
            raw_data = await resp.read()
            json_raw_data = json.loads(raw_data)

            return {
                "token": json_raw_data["Token"],
                "status": resp.status,
                "url": resp.url,
                "method": "post"
            }


async def async_get(session, url, headers={}):
    """ Using aiohttp client to get API calls
    """
    start = time.time()
    async with session.get(url, ssl=False, headers=headers) as resp:
        raw_data = await resp.read()
        elapsed = time.time() - start

        return {
            "status": resp.status,
            "data": json.loads(raw_data),
            "url": resp.url,
            "elapsed": f'{elapsed:0.2f}s',
            "method": "get"
        }


async def async_post(session, url, data):
    """ Using aiohttp client to POST API calls
    """
    start = time.time()
    async with session.post(url, ssl=False, json=data) as resp:
        raw_data = await resp.read()
        elapsed = time.time() - start

        return {
            "status": resp.status,
            "data": json.loads(raw_data),
            "url": resp.url,
            "elapsed": f'{elapsed:0.2f}s',
            "method": "post"
        }


