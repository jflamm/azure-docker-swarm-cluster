import yaml
from invoke import task
import json

RESOURCE_GROUP = 'swarm-demo'
LOCATION = 'eastus'
MASTER_FQDN = RESOURCE_GROUP + '-master0.' + LOCATION + '.cloudapp.azure.com'
VMSS_NAME = 'agent'
CLUSTER_KEY='cluster'

@task
def ssh(ctx):
    with open('cluster-template.json') as json_data:
        d = json.load(json_data)
        print('master: {}:22'.format(MASTER_FQDN))
        start_port = d['variables']['natStartPort']
        end_port = d['variables']['natEndPort']
        print('agents: {}:{}-{}'.
              format(MASTER_FQDN, start_port, end_port))
        user = d['parameters']['adminUsername']['defaultValue']
        print('agent0: ssh {}@{} -i {}.pem -p {}'.
              format(user, MASTER_FQDN, CLUSTER_KEY, start_port))


@task
def keys(ctx):
    print('making ssh keys')
    ctx.run('ssh-keygen -b 2048 -t rsa -f {} -q -N \"\"'.format(CLUSTER_KEY))
    ctx.run('mv {0} {0}.pem'.format(CLUSTER_KEY))


@task
def params(ctx):
    print('making parameters.json')
    ctx.run('python genparams.py')


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
