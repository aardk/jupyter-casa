FROM ubuntu:22.04
CMD ["jupyter", "lab"]

ENV DEBIAN_FRONTEND=noninteractive

ENV PYTHONPATH="/usr/local/lib/python3.10/dist-packages" \
    QT_X11_NO_MITSHM=1

# Setup enviroment
RUN export LC_ALL=C && \
    apt-get update && apt-get install -y apt-utils debconf-utils && apt-get -y upgrade && \
    apt-get install -y python3 python3-dev python3-pip libgfortran5 wget software-properties-common && \
    apt-get install -y git lsof xvfb fuse curl vim nano emacs-nox&& \
    apt-get clean &&\
    pip3 install -U pip

#node.js
RUN curl -sL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

# Jupyter notebook and -lab
RUN /usr/local/bin/pip install matplotlib astropy notebook==7.2.2 widgetsnbextension==4.0.13 ipywidgets==8.1.5 jupyterhub==5.1.0 jupyterlab==4.2.5 && \
    #jupyter nbextension enable --py widgetsnbextension --sys-prefix && \
    jupyter labextension install @jupyter-widgets/jupyterlab-manager
# Install casa
# NB: Plotms and Casaviewer are distributed as an appimage. Appimages use FUSE, to mount a FUSE 
# filesystem from within DOCKER requires the container to run in priviliged mode. To avoid this 
# we extract the images and modify the casa tasks to call the extracted images

RUN /usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple casatools==6.6.5.31 && \
    /usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple casatasks==6.6.5.31 && \
    /usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple casashell==6.6.5.31 && \
    /usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple casatestutils==6.6.5.31 && \
    /usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple casaplotserver==1.8.2 && \
    #/usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple almatasks==1.7.1 && \
    /usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple casatablebrowser==0.0.35 && \
    /usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple casafeather==0.0.22 && \
    /usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple casadata==2024.8.26 && \
    /usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple casalogger==1.0.19 && \
    cd /usr/local/lib/python3.10/dist-packages/casalogger/__bin__ && \
    ./casalogger-x86_64.AppImage --appimage-extract && \
    rm casalogger-x86_64.AppImage && \
    find squashfs-root -type d | xargs chmod 775 && \
    cd .. && \
    sed -i -e 's/casalogger-x86_64.AppImage/squashfs-root\/AppRun/' casalogger.py && \
    /usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple casaplotms==2.5.2 && \
    cd /usr/local/lib/python3.10/dist-packages/casaplotms/__bin__ && \
    ./casaplotms-x86_64.AppImage --appimage-extract && \
    rm casaplotms-x86_64.AppImage && \
    find squashfs-root -type d | xargs chmod 775 && \
    cd .. && \
    sed -i -e 's/casaplotms-x86_64.AppImage/squashfs-root\/AppRun/' private/plotmstool.py && \
    /usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple casaviewer==2.2.3 && \
    cd /usr/local/lib/python3.10/dist-packages/casaviewer/__bin__ && \
    ./casaviewer-x86_64.AppImage --appimage-extract && \
    rm casaviewer-x86_64.AppImage && \
    find squashfs-root -type d | xargs chmod 775 && \
    cd .. && \
    sed -i -e 's/casaviewer-x86_64.AppImage/squashfs-root\/AppRun/' private/config.py

# Most recent protobuf breaks plotms
RUN pip install protobuf==3.20.*

# Install WSCLEAN, AOFLAGGER
RUN apt-add-repository -y -s ppa:kernsuite/kern-9 \
    && apt-get update \
    && apt-get install -y wsclean aoflagger

# Install CARTA
RUN add-apt-repository -y ppa:cartavis-team/carta \
    && apt-get update \
    && apt-get install -y carta

# Add VLBI scripts
RUN git clone https://github.com/jive-vlbi/casa-vlbi \
    && cp casa-vlbi/*py /usr/local/bin \
    && cp -r casa-vlbi/casavlbitools /usr/local/lib/python3.10/dist-packages \
    && rm -rf casa-vlbi

# Add plotcalng; regular plotcal is removed from CASA6
RUN git clone https://github.com/aardk/evn-tools \
    && cp -r evn-tools/python/evn_tools /usr/local/lib/python3.10/dist-packages/ \
    && rm -rf evn-tools \
    && /usr/local/bin/pip install 'pyvo<=1.5.99'

# Add some useful python packages
RUN pip install natsort

# Install jupyter casa wrapper and copy fixed casa tasked
RUN mkdir -p /usr/local/lib/python3.10/dist-packages
COPY python/start_casa /usr/local/lib/python3.10/dist-packages/start_casa
RUN mkdir -p /opt/casa
COPY casasiteconfig.py /opt/casa
COPY jupyter /usr/local/share/jupyter

RUN groupadd -g 1000  jupyter && useradd -u 1000 -m -s /bin/bash -g jupyter jupyter
EXPOSE 8888
USER jupyter
WORKDIR /home/jupyter
RUN mkdir -p /home/jupyter/.jupyter /home/jupyter/work
COPY --chown=jupyter:jupyter docker/jupyter_notebook_config.py /home/jupyter/.jupyter
COPY --chown=jupyter:jupyter docker/create_font_cache.py /home/jupyter
RUN python3 create_font_cache.py
