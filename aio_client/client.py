import aiohttp
import asyncio
import time
import yaml
import logging.config

from aio_client.sitehealth import site_health, site_health_data
from aio_client.helper import get_current_time
from aio_client.request import async_get_auth_token

from aio_client.dnac_env import ENVIRONMENT_IN_USE, DNA_CENTER as dnac

# get the setting of DNAC server in file named "dnac_env.py".
dnac["name"] = str(ENVIRONMENT_IN_USE).strip()

# logging setting
logging.config.dictConfig(yaml.load(open('logging.yaml'), Loader=yaml.FullLoader))
logconsole = logging.getLogger('console')

# -------------------------------------------------------------------
# Global Var.
# -------------------------------------------------------------------
session = None  # aiohttp session
tasks_runs_every_seconds = 10
token_start_time = time.time()
token_renew_seconds = 60 * 60
api_failure_count = 0
api_count = 0


# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------


async def api_failure(response):
    """ In case of api calls failure, do logging and api failure count
    """
    global api_failure_count
    api_failure_count += 1
    logconsole.error(
        f'api failed no.: {api_failure_count}, method: {response["method"]} , status: {response["status"]}, url: {response["url"]}, elapsed: {response["elapsed"]:0.2f}s')
    return


async def get_token_refresh(renew_seconds=(token_renew_seconds - 2 * 60)):
    """ Renew token every hour by setting in DNAC
    """
    global token_start_time, session, api_failure_count, api_count

    # if token alive is above the timeout of renew , refresh the token
    # or session has not created in the beginning
    renew = time.time() - token_start_time
    if (renew > renew_seconds) or not session:
        if session:
            await session.close()
        response = await async_get_auth_token(dnac["host"], dnac["username"], dnac["password"], dnac["port"])
        if response["status"] == 200:
            api_count += 1
            headers = {'X-auth-token': response['token']}
            session = aiohttp.ClientSession(headers=headers)

            token_start_time = time.time()
            logconsole.info(f"Token alive: {renew / 60:0.2f} min, refreshed successfully!")
        else:
            api_failure_count += 1
            logconsole.info(
                f'Token alive: {renew / 60:0.2f} min, refreshed failed, status: {response["status"]}, url: {response["url"]}')

    return


async def get_site_health(s, t):
    """ get the site health, print healthy info about the network device and clients
    """
    global api_count

    response = await site_health(s, t, dnac)

    if response["status"] != 200:
        await api_failure(response)
        return

    api_count += 1
    site_building_list = site_health_data(response["data"])
    if not site_building_list:
        print("NO site with clients or network devices")
        return

    # Do some action after got the site health from DNAC
    # In this demo, print the information only for those site where there are network devices and clients in
    # You can using database client ie. mysql, influx to write this data into database.
    for site in site_building_list:
        print(
            f'In building: {site["siteName"]}, for Network Device/Clients: Count- '
            f'{site["numberOfNetworkDevice"]}/{site["numberOfClients"]}, Healthy Percent- '
            f'{site["healthyNetworkDevicePercentage"]}/{site["healthyClientsPercentage"]}, '
            f'for Wireless/Wired Clients: Count- {site["numberOfWiredClients"]}/{site["numberOfWirelessClients"]}'
            f', Healthy Percent- {site["clientHealthWired"]}/{site["clientHealthWireless"]}')


async def api_task(s, t):
    """ detail tasks runs in each periods
    """
    tasks = []
    tasks.append(get_site_health(s, t))

    if tasks:
        await asyncio.wait(tasks)

    return


async def periodic(timeout):
    """ Tasks runs every periods setting by the global Variable "tasks_runs_every_seconds"
    """
    global session, api_failure_count, api_count, token_start_time
    looping_no = 0
    token_start_time = time.time()

    while True:
        looping_no += 1

        # If you need runs infinitely, delete following 2 lines
        if looping_no >= 5:
            break

        logconsole.info(f"looping {str(looping_no)} start")
        task_run_start_time = time.time()

        await get_token_refresh()
        await api_task(session, get_current_time())

        elapsed = time.time() - task_run_start_time
        logconsole.info(
            f"looping no.{str(looping_no)} took: {elapsed:0.2f}s, api failed/total: {api_failure_count}/{api_count}")
        if timeout > elapsed:
            await asyncio.sleep(timeout - elapsed)

    if session:
        await session.close()

    return


if __name__ == "__main__":
    """ main program
    """
    logconsole.info(f'collect task runs every {tasks_runs_every_seconds}s')
    #time.sleep(math.ceil(time.time() / 60) * 60 - time.time())
    asyncio.run(periodic(tasks_runs_every_seconds))
