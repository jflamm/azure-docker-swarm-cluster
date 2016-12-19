#!/usr/bin/env bash
nvidia-docker build /fathom/tensorflow -t tensorflow
nvidia-docker run -v /fathom:/fathom \
                  -v /fathom/tensorflow/test_job.py:/run.py \
                  -v /fathom/jobs/$1:/job.yaml \
                  tensorflow python3 run.py $2
