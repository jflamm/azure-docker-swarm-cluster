FROM nvidia/cuda:8.0-cudnn5-devel-ubuntu16.04

# Pick up some TF dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libfreetype6-dev \
        libpng12-dev \
        libzmq3-dev \
        pkg-config \
        python3.5 \
        python3.5-dev \
        rsync \
        software-properties-common \
        unzip \
        nvidia-modprobe \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN curl -O https://bootstrap.pypa.io/get-pip.py && \
    python3 get-pip.py && \
    rm get-pip.py

RUN pip3 --no-cache-dir install \
        ipykernel \
        jupyter \
        matplotlib \
        numpy \
        scipy \
        sklearn \
        pyyaml \
        && \
    python3 -m ipykernel.kernelspec

ENV TENSORFLOW_VERSION 0.12.0rc0

# Install TensorFlow GPU version from central repo
RUN pip3 --no-cache-dir install \
    http://storage.googleapis.com/tensorflow/linux/gpu/tensorflow_gpu-${TENSORFLOW_VERSION}-cp35-cp35m-linux_x86_64.whl

# Set up our notebook config.
COPY jupyter_notebook_config.py /root/.jupyter/

# Copy sample notebooks.
COPY ./notebooks /notebooks
COPY start.sh README.md /

# TensorBoard
EXPOSE 6006

# IPython
EXPOSE 8888

ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:/usr/local/cuda/lib64:/usr/local/cuda/extras/CUPTI/lib64
ENV CUDA_HOME /usr/local/cuda

WORKDIR "/"

RUN echo 'alias python=python3' >> ~/.bashrc

#CMD ["/start.sh"]
