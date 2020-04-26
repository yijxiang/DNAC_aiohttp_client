# Please input the DNAC server used in this client.
# Options is : sandbox  sandbox2 customer
ENVIRONMENT_IN_USE = "sandbox2"

# "customer" Lab Backend, if you select "customer"
DNA_CENTER = {
    "host": "",
    "port": 443,
    "username": "",
    "password": ""
}

# End User Input
###################

# Set the 'Environment Variables' based on the lab environment in use
if ENVIRONMENT_IN_USE == "sandbox":
    DNA_CENTER = {
        "host": "sandboxdnac.cisco.com",
        "port": 443,
        "username": "devnetuser",
        "password": "Cisco123!"
    }


elif ENVIRONMENT_IN_USE == "sandbox2":
    DNA_CENTER = {
        "host": "sandboxdnac2.cisco.com",
        "port": 443,
        "username": "devnetuser",
        "password": "Cisco123!"
    }

