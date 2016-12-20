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
def ssh(ctx, master=False, agent=False, id=0):
    with open('cluster-template.json') as json_data:
        d = json.load(json_data)
        user = d['parameters']['adminUsername']['defaultValue']
        start_port = d['variables']['natStartPort']
        end_port = d['variables']['natEndPort']

    if agent:
        ctx.run('ssh -o StrictHostKeyChecking=no {}@{} -i {}.pem -p {}'.\
            format(user, LB_FQDN, CLUSTER_KEY, start_port + id), pty=True)
    elif master:
        ctx.run('ssh -o StrictHostKeyChecking=no {}@{} -i {}.pem'.
              format(user, MASTER_FQDN, CLUSTER_KEY), pty=True)
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


@task(help={"run job."})
def run(ctx, job_spec_file='job.yaml'):
    with open(job_spec_file, 'r') as f:
        job_spec = yaml.load(f)
        num_tasks = len(job_spec['job']['tasks'])
        num_machines = job_spec['job']['ncpus']
        machines = min(num_tasks, num_machines)
        tasks = job_spec['job']['tasks'][:machines]
    with open('cluster-template.json') as json_data:
        d = json.load(json_data)
        user = d['parameters']['adminUsername']['defaultValue']
        start_port = d['variables']['natStartPort']
        for i, task in enumerate(tasks):
            port = str(int(start_port) + i)
            cmd1 = 'ssh -o StrictHostKeyChecking=no {}@{} -i {}.pem -p {}'.format(user, LB_FQDN, CLUSTER_KEY, port)
            cmd2 = 'sh /fathom/tensorflow/container.sh {} {}'.format(job_spec_file, i)
            print('{} \\ {}'.format(cmd1, cmd2))
            ctx.run('{} \\\n {}'.format(cmd1, cmd2), pty=True)


@task(help={"Make ssh keys."})
def keys(ctx):
    print('making ssh keys')
    ctx.run('ssh-keygen -b 2048 -t rsa -f {} -q -N \"\"'.format(CLUSTER_KEY))
    ctx.run('mv {0} {0}.pem'.format(CLUSTER_KEY))


@task(help={"Make Azure json parameters."})
def params(ctx, job_spec_file='job.yaml'):
    with open(job_spec_file) as f:
        d = yaml.load(f)
        num_tasks = len(d['job']['tasks'])
        num_machines = d['job']['ncpus']
        machines = min(num_tasks, num_machines)
        if num_machines != num_tasks:
            print('Warning number of tasks ({}) != number of machines ({}), using minimum ({}) for configuration'.
                  format(num_tasks, num_machines, machines))

        print('making parameters.json: {} machines from "{}" spec'.format(machines, job_spec_file))
        gen_params(machines)


@task(keys, params, aliases=['deploy-cluster'])
def deploy(ctx, job_spec_file='job.yaml'):
    print('deploying cluster \"{}\" in region \"{}\"'.format(RESOURCE_GROUP, LOCATION))
    ctx.run('az group create --name {} --location {} --output table'.format(RESOURCE_GROUP, LOCATION))
    ctx.run('az group deployment create --template-file cluster-template.json --parameters "@parameters.json" \
             --resource-group {} --name cli-deployment-{} --output table'.format(RESOURCE_GROUP, LOCATION))

@task(aliases=['ls-vms'])
def ls(ctx):
    ctx.run('az vmss list-instances --resource-group {} --name {} --output table'.format(RESOURCE_GROUP, VMSS_NAME))


@task(aliases=['stop-vms'])
def stop(ctx):
    print('stopping \"{}\" vms in \"{}\"'.format(VMSS_NAME, RESOURCE_GROUP))
    ctx.run('az vmss stop --resource-group {} --name {} --output table'.format(RESOURCE_GROUP, VMSS_NAME))


@task(aliases=['deallocate-vms'])
def deallocate(ctx):
    print('deallocating \"{}\" vms in \"{}\"'.format(VMSS_NAME, RESOURCE_GROUP))
    ctx.run('az vmss deallocate --resource-group {} --name {} --output table'.format(RESOURCE_GROUP, VMSS_NAME))


@task(help={"Delete resources."})
def delete(ctx):
    print('deleting resource group {}'.format(RESOURCE_GROUP))
    ctx.run('az resource delete {} --output table'.format(RESOURCE_GROUP))


@task(aliases=['restart-vms'])
def restart(ctx):
    print('restarting \"{}\" vms in \"{}\"'.format(VMSS_NAME, RESOURCE_GROUP))
    ctx.run('az vmss restart --resource-group {} --name {} --output table'.format(RESOURCE_GROUP, VMSS_NAME))

@task(aliases=['reimage-vms'])
def reimage(ctx):
    print('reimage \"{}\" vms in \"{}\"'.format(VMSS_NAME, RESOURCE_GROUP))
    ctx.run('az vmss reimage --resource-group {} --name {} --output table'.
            format(RESOURCE_GROUP, VMSS_NAME))
    # --custom-data ./custom-data.txt


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
    with open('parameters.json', 'w') as h:
        h.write(json.dumps(params))

