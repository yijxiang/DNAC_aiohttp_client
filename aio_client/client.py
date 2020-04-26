import os
import sys
import json
import aiohttp
import asyncio
import time
import yaml
from datetime import datetime
from urllib.parse import urlparse
import math
import logging
import logging.config

from aio_client.site_health import site_health, site_health_data
from aio_client.helper import get_current_time
from aio_client.request import async_get_auth_token

from aio_client.dnac_env import ENVIRONMENT_IN_USE, DNA_CENTER as dnac
# get the setting of DNAC server in file.
# Dict of dnac KEYs: host port username password
dnac["name"] = str(ENVIRONMENT_IN_USE).strip()


# Reading logging file
logging.config.dictConfig(yaml.load(open('logging.yaml'), Loader=yaml.FullLoader))
logconsole = logging.getLogger('console')

# -------------------------------------------------------------------
# Global Var.
# -------------------------------------------------------------------
session = None  # aiohttp session
tasks_runs_every_seconds = 60
token_start_time = time.time()
token_renew_seconds = 60*60
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


async def get_token_refresh(renew_seconds=(token_renew_seconds-2*60)):
    """ Renew token every hour by setting in DNAC
    """
    global token_start_time, session, api_failure_count, api_count

    # if token alive is above the timeout of renew , refresh the token
    # or session has not created in the beginning
    renew = time.time() - token_start_time
    if (renew > renew_seconds) or not session:
        if session:
            await session.close()
        response = await async_get_auth_token(dnac["host"],dnac["username"],dnac["password"],dnac["port"])
        if response["status"] == 200:
            api_count += 1
            headers = {'X-auth-token': response['token']}
            session = aiohttp.ClientSession(headers=headers)

            token_start_time = time.time()
            logconsole.info(f"Token alive: {renew/60:0.2f} min, refreshed successfully!")
        else:
            api_failure_count += 1
            logconsole.info(
                f'Token alive: {renew/60:0.2f} min, refreshed failed, status: {response["status"]}, url: {response["url"]}')

    return


async def get_site_health(session, timestamp):
    """ get the site health
    """
    global api_count

    response = await site_health(session, timestamp)
    if response["status"] != 200:
        await api_failure(response)
        return

    api_count += 1
    logconsole.info(
        f'api no.: {api_count}, method: {response["method"]} , status: {response["status"]}, url: "site health", elapsed: {response["elapsed"]:0.2f}s')

    site_building_list = site_health_data(response["data"])
    if not site_building_list:
        logconsole.warning("NO site with clients or network devices")
        return

    logconsole.info(f'{}')


async def api_task(session, timestamp):
    """ detail tasks runs in each periods
    """
    tasks = []
    tasks.append(get_site_health(session, timestamp))

    if tasks:
        await asyncio.wait(tasks)


async def periodic(timeout):
    """ Tasks runs every periods setting by the global Variable "tasks_runs_every_seconds"
    """
    global session, api_failure_count, api_count
    looping_no = 0

    while True:
        looping_no += 1
        logconsole.info(f"looping {str(looping_no)} start")
        task_run_start_time = time.time()

        await get_token_refresh()
        await api_task(session, get_current_time())

        elapsed = time.time() - task_run_start_time
        logconsole.info(f"looping no: {str(looping_no)} took: {elapsed:0.2f}s, api failed/total: {api_failure_count}/{api_count}")
        if timeout > elapsed:
            await asyncio.sleep(timeout - elapsed)

    if session:
        await session.close()

    return


if __name__ == "__main__":
    """ main program
    """
    logconsole.info(f'collect task runs every {tasks_runs_every_seconds}s')
    time.sleep(math.ceil(time.time() / 60) * 60 - time.time())
    asyncio.run(periodic(tasks_runs_every_seconds))

