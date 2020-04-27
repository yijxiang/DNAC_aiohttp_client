[![published](https://static.production.devnetcloud.com/codeexchange/assets/images/devnet-published.svg)](https://developer.cisco.com/codeexchange/github/repo/yijxiang/DNAC_aiohttp_client)

# What is DNAC aiohttp client

This client demostrate to request async. API calls to cisco DNAC using aiohttp, runs as module "telegraf" in the TIG stack (telegraf/influx/grafana).

[Telegraf](https://github.com/influxdata/telegraf) is an agent for collecting, processing, aggregating, and writing metrics, the **DNAC aiohttp client** does:

- trigger to collect metric: periodically to run the api calls target to DNAC
- processing the collected JSON data
- write to influx database using python client: [ aioinflux ](https://aioinflux.readthedocs.io/en/stable/)

It was inspired by https://github.com/CiscoDevNet/DNAC-NOC.git. 

## Architecture

![Architecture](image/arch.png "aiohttp client architecture")

## HOW to run this client

### DNAC aiohttp client setup

#### Steps 1: Create folder and clone the project

- Create new folder
- Clone it and checkout using your favourite python IDE such as pycharm

#### Steps 2: Setup Python virtual enviroment

###### Enviroment preparing

Python version 3.6.x - 3.8.x was recommended in this client because of:

  - **asyncio** was introduced into after python 3.5.x.
  - aiohttp need python 3.5+
  - aioinflux need python 3.6+


Next, setup the python envir.

- Go into the application folder, create the python virtual enviroment usuing "virtualenv" and install all packages.

``` 
virtualenv venv --python=python3 --no-site-packages
source venv/bin/activate
pip install -r requirements.txt 
```

- Check the python and packages was installed successfully.

``` 
python
pip list
```

> **_INFO:_**  Python version 3.8.2 runs on my MAC OS, and all codes runs smoothly


###### Files description in the project
In your application folder after cloned, files structure listed as this table. Here is file description help you better understanding this project:

| File name        | description                                                  |
| ---------------- | ------------------------------------------------------------ |
| dnac_env.py      | DNAC config, **sandbox2** was selected by default            |
| logging.yaml     | python Logging setting                                       |
| requirements.txt | python package list                                          |
| client.py        | **main** entry module for this client                        |
| request.py       | module used for aiohttp request get and post                 |
| helper.py        | module used for helper function                              |
| sitehealth.py    | module used for specific api: /dna/intent/api/v1/site-health |


As required, you can add or edit files in your project, at least you should modify the file **dnac_env.py**:

- In *dnac_env.py*, please change the DNAC server as yours and **ENVIRONMENT_IN_USE** as *"customer"* or one different name which is not same as the existing list: *sandbox* or *sandbox2*:

``` python
ENVIRONMENT_IN_USE = "customer"

# "customer" Lab Backend, if you select "customer"
DNA_CENTER = {
    "host": "",
    "port": 443,
    "username": "",
    "password": ""
}

```

> **_Pay Attention:_**  *Please DO NOT change files name or delete*


#### Steps 3: influxdb and grafana install - OPTION STEP

If you do not want to write data to DB, please go ahead to step4 to run the python script directly , some information about site health from DNA Center server which has been setup in above step will be displayed in the console.

You can also install influxdb via [ link to InfluxDB latest:1.8 ](https://docs.influxdata.com/influxdb/v1.8/introduction/install/), and grafana via [ link to Grafana latest ](https://grafana.com/docs/grafana/latest/) in your server.

On _mac os_, you can using **brew** to install&run the open sourced influxdb and grafana for the demo purpose.

```
# install influxdb
brew install influxdb
brew install grafana

# runs influxdb
brew services start influxdb
brew services start grafana

# stop all services
brew services stop --all

# list all services
brew services list

```


#### Steps 4: Customize the config and run python app.

You should make some little change according to your requirement in *client.py* python file.

##### Changes to support influxDB

If you install the influx database to store data points as above option step, take the following modification:

In *client.py*, if you use **aioinflux** client to store time series data to Influx:
  - set the IP address of influx database server, by default *127.0.0.1* is used in local installation;
  - set the *influxdb_write_enable* to *True*;

``` python
influxdb_client_host_ip = "127.0.0.1"        # influx client host ip, should be modified according to your app
influxdb_write_enable = True                 # If you use influxDB to store data, please change it to True
```

During client runs, in the console logging, you should notify similar info included *write to influxdb points* :
```
2020-04-27 09:56:48,988 - INFO - write to influxdb points: 3
```

> **_INFO:_**  *write to influxdb points: 3* means total 3 data groups have been written into influx database


##### Period setting to above 60 seconds

- In *client.py*, you'd better change the *tasks_runs_every_seconds* to 60/120/300 seconds to satisfy your real requirements.

``` python
tasks_runs_every_seconds = 60                 # tasks periods, should be modified according to your app
```

##### Disable loop break setting by default

- In *client.py*, you should disable the loop break used for demo purpose.

``` python
        #if looping_no >= 5:
        #    break
```

##### Run it

Please goto *aio_client* folder, run your app.
``` 
python client.py

2020-04-27 09:46:46,517 - INFO - collect task runs every 10s
2020-04-27 09:46:46,518 - INFO - looping 1 start
2020-04-27 09:46:47,464 - INFO - Token alive: 0.00 min, refreshed successfully!
In building: NSYD5, for Network Device/Clients: Count- 1/1, Healthy Percent- 100/100, for Wireless/Wired Clients: Count- 1/None, Healthy Percent- 100/None
In building: MX14, for Network Device/Clients: Count- 1/8, Healthy Percent- 100/88, for Wireless/Wired Clients: Count- None/8, Healthy Percent- None/88
In building: HQ, for Network Device/Clients: Count- 3/None, Healthy Percent- 100/None, for Wireless/Wired Clients: Count- None/None, Healthy Percent- None/None
2020-04-27 09:46:48,848 - INFO - looping no.1 took: 2.33s, api failed/total: 0/2
2020-04-27 09:46:56,523 - INFO - looping 2 start

```



> **_INFO:_**  Please ignore the warning: 
> - UserWarning: Pandas/Numpy is not available. Support for 'dataframe' mode is disabled.
> - warnings.warn(no_pandas_warning)
 

### THE END: Happy coding with Cisco DNA Center