FROM ubuntu:18.04
CMD ["jupyter", "notebook"]
RUN echo "deb http://nl.archive.ubuntu.com/ubuntu/ bionic multiverse" >> /etc/apt/sources.list \
    && echo "deb http://nl.archive.ubuntu.com/ubuntu/ bionic-updates multiverse" >> /etc/apt/sources.list \
    && apt-get update && apt-get install -y apt-utils debconf-utils && apt-get -y upgrade && apt-get clean

ENV DEBIAN_FRONTEND=noninteractive

ENV PYTHONPATH="/usr/local/lib/python3.6/dist-packages" \
    QT_X11_NO_MITSHM=1

# Setup enviroment
RUN echo deb http://nl.archive.ubuntu.com/ubuntu/ bionic main restricted universe multiverse >/etc/apt/sources.list && \
    echo deb http://nl.archive.ubuntu.com/ubuntu/ bionic-updates main restricted universe multiverse >>/etc/apt/sources.list && \
    export LC_ALL=C && \
    apt-get update && apt-get install -y apt-utils debconf-utils && apt-get upgrade -y && \
    apt-get install -y python3 python3-dev python3-pip libgfortran3 wget && \
    apt-get install -y iproute2 lsof xvfb fuse curl && \
    pip3 install -U pip

#node.js
RUN curl -sL https://deb.nodesource.com/setup_13.x | bash - && \
    apt-get install -y nodejs

# Jupyter notebook and -lab
RUN /usr/local/bin/pip install matplotlib astropy notebook widgetsnbextension ipywidgets jupyterhub jupyterlab && \
    jupyter nbextension enable --py widgetsnbextension --sys-prefix && \
    jupyter labextension install @jupyter-widgets/jupyterlab-manager
# Install casa
# NB: Plotms and Casaviewer are distributed as an appimage. Appimages use FUSE, to mount a FUSE 
# filesystem from within DOCKER requires the container to run in priviliged mode. To avoid this 
# we extract the images and modify the casa tasks to call the extracted images
RUN  /usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple casatools && \
    /usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple casatasks && \
    /usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple casashell && \
    /usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple casaplotms && \
    cd /usr/local/lib/python3.6/dist-packages/casaplotms/__bin__ && \
    ./casaplotms-x86_64.AppImage --appimage-extract && \
    rm casaplotms-x86_64.AppImage && \
    find squashfs-root -type d | xargs chmod 775 && \
    cd .. && \
    sed -i -e 's/casaplotms-x86_64.AppImage/squashfs-root\/AppRun/' private/plotmstool.py && \
    /usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple casaviewer && \
    cd /usr/local/lib/python3.6/dist-packages/casaviewer/__bin__ && \
    ./casaviewer-x86_64.AppImage --appimage-extract && \
    rm casaviewer-x86_64.AppImage && \
    find squashfs-root -type d | xargs chmod 775 && \
    cd .. && \
    sed -i -e 's/casaviewer-x86_64.AppImage/squashfs-root\/AppRun/' private/config.py
# carta
ENV CARTAVERSION=1.4
Run cd /usr/local && \
    wget https://github.com/CARTAvis/carta/releases/download/v${CARTAVERSION}/CARTA-v${CARTAVERSION}-remote.tgz && \
    apt-get install -y libnss3 libgdk-pixbuf2.0-0 libgtk-3-0 #libx11-xcb1 libxss1 libasound2 && \
    tar zxf CARTA-v${CARTAVERSION}-remote.tgz

# Install CASACORE
ENV CASACORE_VERSION=3.3.0
RUN apt-get install -y libboost-all-dev build-essential libpython3-dev python3-dev python3-numpy gfortran \
                       libsofa1-dev flex bison libbison-dev libatlas-base-dev liblapack-dev libcfitsio-dev \
                       wcslib-dev cmake libreadline-dev libncurses5-dev libgsl-dev libfftw3-dev libhdf5-dev \
    && cd /usr/local \
    && wget https://github.com/casacore/casacore/archive/v${CASACORE_VERSION}.tar.gz \
    && tar xvf v${CASACORE_VERSION}.tar.gz \
    && mkdir casacore-${CASACORE_VERSION}/build \
    && cd casacore-${CASACORE_VERSION}/build \
    && cmake -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_BUILD_TYPE=Release -DBUILD_DEPRECATED=ON -DBUILD_PYTHON=OFF -DBUILD_PYTHON3=ON ../ \
    && make -j4 \
    && make install \
    && cd ../.. \
    && rm -rf v${CASACORE_VERSION}.tar.gz casacore-${CASACORE_VERSION}

# Add Wsclean
RUN apt-get install -y git \
    && cd /usr/local \
    && git clone https://github.com/lofar-astron/LOFARBeam.git \
    && cd LOFARBeam \
    && git checkout v4.1.1 \
    && mkdir -p build \
    && cd build \
#    && cmake -DCASACORE_ROOT_DIR=$workDir/linux64 .. \
    && cmake -DPYTHON_EXECUTABLE=$(which python3) .. \
    && make -j4 \
    && make install \
    && cd /usr/local \
    && rm -rf LOFARBeam \
    && git clone https://gitlab.com/aroffringa/wsclean.git wsclean-code \
    && cd wsclean-code \
    && git checkout v2.10.1 \
    && mkdir build \
    && cd build \
    && cmake .. \
#    && cmake -DCASACORE_ROOT_DIR=$workDir/linux64 .. \
    && make -j4 \
    && make install \
    && /usr/local/bin/pip install python-casacore \
    && cd /usr/local \
    && rm -rf wsclean-code

# Add AOFLAGGER
RUN apt-get install -y libboost-test-dev libgtkmm-3.0-dev liblua5.3-dev libpng-dev libxml2-dev\
    && /usr/local/bin/pip install pytest \
    && git clone https://github.com/pybind/pybind11.git \
    && cd pybind11 \
    && git checkout v2.6.0 \
    && mkdir build \
    && cd build \
    && cmake -DDOWNLOAD_CATCH=1 .. \
    && make -j4 \
    && make install \
    && cd .. \
#    && python setup.py install \
    && cd .. \
    && rm -rf pybind11 \
    && git clone https://gitlab.com/aroffringa/aoflagger.git \
    && mkdir -p aoflagger/build \
    && cd aoflagger/build \
#    && cmake -DCASACORE_ROOT_DIR=$workDir/linux64 .. \
    && cmake .. \
    && make -j4 \
    && make install \
#    && cp /usr/local/lib/aoflagger.so /usr/local/lib/python3.6/dist-packages \
    && cd ../.. \
    && rm -rf aoflagger

# Install jupyter casa wrapper and copy fixed casa tasked
RUN mkdir -p /usr/local/lib/python3.6/dist-packages
COPY python/start_casa /usr/local/lib/python3.6/dist-packages/start_casa
COPY jupyter /usr/local/share/jupyter

RUN groupadd -g 1000  jupyter && useradd -u 1000 -m -g jupyter jupyter
EXPOSE 8888
USER jupyter
WORKDIR /home/jupyter
RUN mkdir -p /home/jupyter/.jupyter /home/jupyter/work
COPY --chown=jupyter:jupyter docker/jupyter_notebook_config.py /home/jupyter/.jupyter
COPY --chown=jupyter:jupyter docker/create_font_cache.py /home/jupyter
RUN python3 create_font_cache.py
