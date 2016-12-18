from base64 import b64encode
from os import environ
from json import dumps

params = {
    "adminUsername": {
        "value": "cluster"
    },
    "adminPublicKey": {
        "value": open("cluster.pub","r").read()
    },
    "masterCount": { 
        "value": int(environ.get('MASTER_COUNT',1))
    },
    "masterCustomData": {
        "value": b64encode(open("cloud-config-master.yml", "r").read())
    },
    "agentCount": {
        "value": int(environ.get('AGENT_COUNT', 1))
    },
    "agentCustomData": {
        "value": b64encode(open("cloud-config-agent.yml", "r").read())
    },
    "saType": {
        "value": "Standard_LRS"
    }
}

with open('parameters.json', 'w') as h:
    h.write(dumps(params))
