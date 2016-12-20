import tensorflow as tf
from tensorflow.python.client import device_lib
import time
import sys
import time
from os import path
import yaml

LOG = '/fathom/log/'


if __name__ == '__main__':
    print('******************************************')
    with open('/job.yaml') as f:
        job_spec = yaml.load(f)

    print('CPU {}'.format(sys.argv[1]))
    print('model {}'.format(job_spec['job']['model']))
    print('input {}'.format(job_spec['job']['input']))
    print('basedir {}'.format(job_spec['job']['basedir']))
    print('task {}'.format(job_spec['job']['tasks'][int(sys.argv[1])]))
    print('Start tensorflow')

    # dummy tensorflow test job
    sess = tf.Session(config=tf.ConfigProto(log_device_placement=True))
    devices = device_lib.list_local_devices()

    cpus = [i for i in devices if i.device_type == 'CPU']
    gpus = [i for i in devices if i.device_type == 'GPU']

    info = '{} CPUs, {} GPUs'.format(len(cpus), len(gpus))
    print(info)
    filename = path.join(LOG, '%s-p%s.txt'% (time.strftime('%y%m%m%S'), sys.argv[1]))
    with open(filename, 'w') as f:
        f.write(info)
    print('******************************************')


    print('Sleeping')
    # sleep
    time.sleep(5)
    print('Done.')
    print('******************************************')

