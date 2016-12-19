# Fathom GPU cluster

A Docker cluster to run Tensorflow jobs.  This project is derived from rcarmo/azure-docker-swarm-cluster.

## What

This builds upon a basic Azure Resource Manager template that automatically deploys a [Docker][d] Swarm cluster atop Ubuntu 16.04. This cluster has 1 master VMs and a VM scaleset for workers/agents, plus the required network infrastructure.  The VMs in the scaleset are provisioned with Nvidia drivers, Nvidia-docker plugin, and an Azure fileshare is mounted at /fathom.  Upon running a job, a docker image in build and the containers are loaded and run.

TODO: There are some path assumptions regarding the locations of the fileshare and names for the scripts:

container.sh must be in /fathom/tensorflow
test_run.py must be in /fathom/tensorflow
jobs.yml must be in /fathom/jobs

TODO: With modest additional _you can add and remove agents at will_ simply by resizing the VM scaleset.  VMs should be deallocated upon job completion and then restarted and scaled to meet requirements of new job.
TODO: Mounting of fileshare needs to be put into script to execute on reboot. Now it is only in cloud-init.
TODO: Upon job completion signal shutdown and deallocation of VMs.

## Why

The GPU infrasture is designed to run a single tensorflow container on each GPU-enabled VM to parallelize running of experiments.

## How

* `inv keys` - generates an SSH key for provisioning
* `inv params job_spec.json` - generates ARM template parameters, number of cpus are derived from job yaml file.
* `inv ssh [-m] [-a]` - runs ssh to connect to master or agent VMs
* `make stop` - stops all worker VMs
* `make deallocate` - deallocates all worker VMs (also stops
* `make restart` - restarts all worker VMs
* `make clean` - cleans up key files


## Recommended Sequence

    create a yaml job description file (default: jobs.yml)
     
    inv deploy
    
    # You can go to the Azure portal and check the deployment progress
    
    # now run the job
    inv run
    
    # You can deallocate the VMs
    make deploy-replicated-service
    # Open the agent-lb endpoint in a browser, refresh to hit a different node (from outside Azure, Swarm is still quirky)
    make list-endpoints

    # Scale the service down
    make scale-service-4
    
    # Now scale the VM scale set and watch as new VMs join the cluster
    make scale-vmss-7
    # Add more service workers, and watch them spread through the cluster
    make scale-service-16
    
    # Now scale down the VM scale set and watch Swarm coping by re-scheduling workers
    make scale-vmss-3
     
    # Stop (but not de-allocate) worker VMs and watch all containers move to the master (because we have no scheduling rules)
    make stop-vmss
    # Now re-start them
    make start-vmss
    
    # Clean up after we're done working
    make destroy-cluster


## Requirements

* Azure account which must be logged into using MFA
* Fileshare expected to be in resource group "swarm-demo-storage"
* [Python][p]
* The new [Azure CLI](https://github.com/Azure/azure-cli) (`pip install -U -r requirements.txt` will install it)

## Internals

`master0` runs a very simple HTTP server (only accessible inside the cluster) that provides tokens for new VMs to join the swarm and an endpoint for them to signal that they're leaving. That server also cleans up the node table once agents are gone.

Upon provisioning, all agents try to obtain a worker token and join the swarm. Upon rebooting, they signal they're leaving the swarm and re-join it again.

This is done in the simplest possible way, by using `cloud-init` to bootstrap a few helper scripts that are invoked upon shutdown and (re)boot. Check the YAML files for details.

## Provisioning Flow

To avoid using VM extensions (which are nice, but opaque to most people used to using `cloud-init`) and to ensure each fresh deployment runs the latest Docker version, VMs are provisioned using `customData` in their respective ARM templates. 

`cloud-init` files and SSH keys are then packed into the JSON parameters file and submitted as a single provisioning transaction, and upon first boot Ubuntu takes the `cloud-init` file and provisions the machine accordingly.

If instantiation speed is a concern, this can be done once for each role and baked into a `.vhd` file - which then has to be pre-uploaded, and its location supplied to the cluster template. However, it might be much more efficient to just pause unneeded instances and restart them again when necessary.

## Improvements

There are several things that can be done to improve upon this:

* Ensure this works with multiple masters (cursory testing suggests it works just fine, although it can be fiddly for agents to re-try connecting to up to 5 possible masters, etc.)
* Strengthen the token exchange mechanism (adding SSL and/or a shared `nonce` to the registration/draining URLs is left as an exercise to the reader)

## Disclaimers

There's very little error checking.

The [Docker][d] way of achieving cluster self-provisioning relies on service-specific containers baked into their cloud images (and does not seem to allow for dynamically adding or removing nodes), so the approach in this repo is not canon - but it might be more interesting (and easier to expand upon) for people learning how to use [Docker][d] Swarm. 

Also, keep in mind that the load-balancer configuration does _not_ include TCP port probing or proactive failure detection.

[d]: http://docker.com
[p]: http://python.org
[dh]:https://hub.docker.com/r/rcarmo/demo-frontend-stateless/
