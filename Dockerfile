FROM ubuntu:22.04
# Install packages.
ENV TZ=US
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update
RUN apt-get install -y software-properties-common libsm6 libxext6 libxrender-dev curl gfortran
# RUN add-apt-repository -y ppa:deadsnakes/ppa
# RUN apt-get install -y python3 python3-dev python3-pip python3-pyqt5 gfortran
RUN apt-get install -y '^libxcb.*-dev' libx11-xcb-dev libglu1-mesa-dev libxrender-dev libxi-dev libxkbcommon-dev libxkbcommon-x11-dev

RUN echo "**** Installing Python ****" && \
    add-apt-repository ppa:deadsnakes/ppa &&  \
    apt-get install -y build-essential python3 python3-distutils python3-dev python3-pip && \
    curl -O https://bootstrap.pypa.io/get-pip.py && \
    python3 get-pip.py && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip
RUN pip3 install --upgrade distro
RUN pip3 install --upgrade pyopencl
RUN pip3 install --upgrade cython
RUN pip3 install --upgrade numpy
RUN pip3 install --upgrade opencv-python-headless
RUN pip3 install --upgrade pyfai
RUN pip3 install --upgrade PyQt5
RUN pip3 install --upgrade musclexflibs
RUN pip3 install --upgrade hdf5plugin
RUN pip3 install --upgrade numba
RUN pip3 install --upgrade fisx
RUN pip3 install --upgrade future

RUN pip3 install --upgrade musclex
#RUN pip3 install git+https://github.com/biocatiit/musclex.git@v1.15.7

#ADD musclex /musclex/musclex
#
#ADD LICENSE.txt /musclex/LICENSE.txt
#ADD MANIFEST /musclex/MANIFEST
#ADD README.md /musclex/README.md
#ADD setup.cfg /musclex/setup.cfg
#ADD setup.py /musclex/setup.py
#ENV TMP_PATH $PYTHONPATH
#ENV PYTHONPATH /musclex/:$TMP_PATH
#WORKDIR /musclex/
#RUN python /musclex/setup.py install
#
