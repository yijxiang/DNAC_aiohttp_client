import aiohttp
import asyncio
import time
import yaml
import logging.config

from aioinflux import InfluxDBClient    # influx client
from sitehealth import site_health, site_health_data, site_health_to_influx
from helper import get_current_time
from request import async_get_auth_token
from dnac_env import DNA_CENTER as dnac, ENVIRONMENT_IN_USE

# DNAC server setting dict
dnac["name"] = str(ENVIRONMENT_IN_USE).strip()

# logging setting
logging.config.dictConfig(yaml.load(open('logging.yaml'), Loader=yaml.FullLoader))
logconsole = logging.getLogger('console')

# -------------------------------------------------------------------
# Global Var.
# -------------------------------------------------------------------
session = None                          # aiohttp session
token_start_time = time.time()
token_renew_seconds = 60 * 60           # token renew every 1 hour
api_failure_count = 0
api_count = 0
influxdb_client = None                  # influx client


# -------------------------------------------------------------------
# Var. NEED to modify:
# -------------------------------------------------------------------
tasks_runs_every_n_seconds = 30               # tasks periods, should be modified according to your app
influxdb_client_host_ip = "127.0.0.1"         # influx client host ip, should be modified according to your app
influxdb_write_enable = False                 # If you use influxDB to store data, please change it to True
runs_infinitely = False                       # False: exit after runs 3 times, True: runs infinitely


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

    # Do some action after got the site health data from DNAC
    # In this demo, print the information only for those site where there are network devices and clients in
    # If you use influx db insert data points, you can go ahead to disable the following for blocks
    for site in site_building_list:
        print(
            f'In building: {site["siteName"]}, for Network Device/Clients: Count- '
            f'{site["numberOfNetworkDevice"]}/{site["numberOfClients"]}, Healthy Percent- '
            f'{site["healthyNetworkDevicePercentage"]}/{site["healthyClientsPercentage"]}, '
            f'for Wireless/Wired Clients: Count- {site["numberOfWiredClients"]}/{site["numberOfWirelessClients"]}'
            f', Healthy Percent- {site["clientHealthWired"]}/{site["clientHealthWireless"]}')

    # You can using database client ie. influx to write this data point into database
    # if using influx client, run following if block
    if influxdb_write_enable:
        site_health_influx_data = site_health_to_influx(site_building_list)
        for data in site_health_influx_data:
            data.update({"time": time.time_ns()})
        await influxdb_client.write(site_health_influx_data)
        logconsole.info(f'write to influxdb points: {len(site_health_influx_data)}')


async def api_task(s, t):
    """ detail tasks runs in each periods
    """
    tasks = []
    tasks.append(get_site_health(s, t))

    if tasks:
        await asyncio.wait(tasks)

    return


async def periodic(timeout):
    """ Tasks runs every periods setting by the global Variable "tasks_runs_every_n_seconds"
    """
    global session, api_failure_count, api_count, token_start_time, influxdb_client
    looping_no = 0
    token_start_time = time.time()

    # if using influx client, run following if block
    if influxdb_write_enable:
        influxdb_client = InfluxDBClient(host=influxdb_client_host_ip, db=dnac["name"])
        await influxdb_client.create_database(db=dnac["name"])

    while True:
        looping_no += 1

        logconsole.info(f"looping {str(looping_no)} start")
        task_run_start_time = time.time()

        await get_token_refresh()
        await api_task(session, get_current_time())

        elapsed = time.time() - task_run_start_time
        logconsole.info(
            f"looping no.{str(looping_no)} took: {elapsed:0.2f}s, api failed/total: {api_failure_count}/{api_count}")

        # If you need runs infinitely, will NOT break the while loop
        if not runs_infinitely:
            if looping_no >= 3:
                break

        if timeout > elapsed:
            await asyncio.sleep(timeout - elapsed)

    if session:
        await session.close()

    return


if __name__ == "__main__":
    """ main program
    """
    logconsole.info(f'collect task runs every {tasks_runs_every_n_seconds}s')
    logconsole.info(f'The target DNAC Server is: {dnac["host"]}')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(periodic(tasks_runs_every_n_seconds))
    loop.run_until_complete(asyncio.sleep(0.25))
    loop.close()
