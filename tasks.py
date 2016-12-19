from invoke import task
import json
from base64 import b64encode
import yaml


RESOURCE_GROUP = 'swarm-demo'
LOCATION = 'eastus'
MASTER_FQDN = RESOURCE_GROUP + '-master0.' + LOCATION + '.cloudapp.azure.com'
LB_FQDN = RESOURCE_GROUP + '-agent' + '-lb.' + LOCATION + '.cloudapp.azure.com'
VMSS_NAME = 'agent'
CLUSTER_KEY = 'cluster'


@task(help={"ssh command info."})
def ssh(ctx, agent=False):
    with open('cluster-template.json') as json_data:
        d = json.load(json_data)
        user = d['parameters']['adminUsername']['defaultValue']
        start_port = d['variables']['natStartPort']
        end_port = d['variables']['natEndPort']

        if int(agent) > 0 and int(agent) < 100:
            print(int(agent))
        else:
            print('Addresses:')
            print('master: {}:22'.format(MASTER_FQDN))

            print('agents: {}:{}-{}'.
                  format(LB_FQDN, start_port, end_port))

            print('\nTo connect:')
            print('ssh -o StrictHostKeyChecking=no {}@{} -i {}.pem'.
                  format(user, MASTER_FQDN, CLUSTER_KEY))
            print('ssh -o StrictHostKeyChecking=no {}@{} -i {}.pem -p {}'.
                  format(user, LB_FQDN, CLUSTER_KEY, start_port))

@task(help={"run agents."})
def run(ctx):
    with open('cluster-template.json') as json_data:
        d = json.load(json_data)
        user = d['parameters']['adminUsername']['defaultValue']
        start_port = d['variables']['natStartPort']
        for i in range(2):
            port = str(int(start_port) + i)
            cmd1 = 'ssh -o StrictHostKeyChecking=no {}@{} -i {}.pem -p {}'.format(user, LB_FQDN, CLUSTER_KEY, port)
            cmd2 = 'sh /fathom/tensorflow/container.sh agent{}'.format(i)
            print('{} \\ {}'.format(cmd1, cmd2))
            ctx.run('{} \\\n {}'.format(cmd1, cmd2), pty=True)


@task(help={"Make ssh keys."})
def keys(ctx):
    print('making ssh keys')
    ctx.run('ssh-keygen -b 2048 -t rsa -f {} -q -N \"\"'.format(CLUSTER_KEY))
    ctx.run('mv {0} {0}.pem'.format(CLUSTER_KEY))


@task
def params(ctx):
    print('making parameters.json')
    gen_params('2')


@task(keys, params, aliases=['deploy-cluster'])
def deploy(ctx):
    print('deploying cluster \"{}\" in region \"{}\"'.format(RESOURCE_GROUP, LOCATION))
    ctx.run('az group create --name {} --location {} --output table'.format(RESOURCE_GROUP, LOCATION))
    ctx.run('az group deployment create --template-file cluster-template.json --parameters "@parameters.json" \
             --resource-group {} --name cli-deployment-{} --output table'.format(RESOURCE_GROUP, LOCATION))


@task(aliases=['stop-vms'])
def stop(ctx):
    print('stopping \"{}\" vms in \"{}\"'.format(VMSS_NAME, RESOURCE_GROUP))
    ctx.run('az vmss stop --resource-group {} --name {} --output table'.format(RESOURCE_GROUP, VMSS_NAME))


@task(aliases=['deallocate-vms'])
def deallocate(ctx):
    print('deallocating \"{}\" vms in \"{}\"'.format(VMSS_NAME, RESOURCE_GROUP))
    ctx.run('az vmss deallocate --resource-group {} --name {} --output table'.format(RESOURCE_GROUP, VMSS_NAME))


@task(aliases=['restart-vms'])
def restart(ctx):
    print('restarting \"{}\" vms in \"{}\"'.format(VMSS_NAME, RESOURCE_GROUP))
    ctx.run('az vmss restart --resource-group {} --name {} --output table'.format(RESOURCE_GROUP, VMSS_NAME))


@task(help={"Clean out ssh keys."})
def clean(ctx, docs=False, bytecode=False, extra=''):
    patterns = []
    patterns.append('*.pem')
    patterns.append('*.pub')
    for pattern in patterns:
        ctx.run("rm -rf %s" % pattern)


def gen_params(ncpus=1):
    params = {
        "adminUsername": {
            "value": "cluster"
        },
        "adminPublicKey": {
            "value": open("cluster.pub", "r").read()
        },
        "masterCount": {
            "value": 1
        },
        "masterCustomData": {
            "value": b64encode((open("cloud-config-master.yml", "r").read()).encode('utf-8')).decode('utf-8')
        },
        "agentCount": {
            "value": int(ncpus)
        },
        "agentCustomData": {
            "value": b64encode((open("cloud-config-agent.yml", "r").read()).encode('utf-8')).decode('utf-8')
        },
        "saType": {
            "value": "Standard_LRS"
        }
    }
    a = b64encode((open("cloud-config-master.yml", "r").read()).encode('utf-8'))
    print(type(a), len(a))
    with open('parameters.json', 'w') as h:
        h.write(json.dumps(params))

