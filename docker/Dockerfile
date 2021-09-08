FROM ubuntu:20.04
CMD ["jupyter", "notebook"]
RUN echo "deb http://nl.archive.ubuntu.com/ubuntu/ focal multiverse" >> /etc/apt/sources.list \
    && echo "deb http://nl.archive.ubuntu.com/ubuntu/ focal-updates multiverse" >> /etc/apt/sources.list \
    && apt-get update && apt-get install -y apt-utils debconf-utils && apt-get -y upgrade && apt-get clean

ENV DEBIAN_FRONTEND=noninteractive

ENV PYTHONPATH="/usr/local/lib/python3.8/dist-packages" \
    QT_X11_NO_MITSHM=1

# Setup enviroment
RUN echo deb http://nl.archive.ubuntu.com/ubuntu/ focal main restricted universe multiverse >/etc/apt/sources.list && \
    echo deb http://nl.archive.ubuntu.com/ubuntu/ focal-updates main restricted universe multiverse >>/etc/apt/sources.list && \
    export LC_ALL=C && \
    apt-get update && apt-get install -y apt-utils debconf-utils && apt-get upgrade -y && \
    apt-get install -y python3 python3-dev python3-pip libgfortran5 wget software-properties-common && \
    apt-get install -y git lsof xvfb fuse curl vim nano emacs-nox&& \
    pip3 install -U pip

#node.js
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash - && \
    apt-get install -y nodejs

# Jupyter notebook and -lab
RUN /usr/local/bin/pip install matplotlib astropy notebook widgetsnbextension ipywidgets jupyterhub jupyterlab && \
    jupyter nbextension enable --py widgetsnbextension --sys-prefix && \
    jupyter labextension install @jupyter-widgets/jupyterlab-manager
# Install casa
# NB: Plotms and Casaviewer are distributed as an appimage. Appimages use FUSE, to mount a FUSE 
# filesystem from within DOCKER requires the container to run in priviliged mode. To avoid this 
# we extract the images and modify the casa tasks to call the extracted images
RUN  /usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple casatools==6.3.0.48 && \
    /usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple casatasks==6.3.0.48 && \
    /usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple casashell==6.3.0.48 && \
    /usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple casadata==2021.8.23 && \
    /usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple casaplotms==1.2.8 && \
    cd /usr/local/lib/python3.8/dist-packages/casaplotms/__bin__ && \
    ./casaplotms-x86_64.AppImage --appimage-extract && \
    rm casaplotms-x86_64.AppImage && \
    find squashfs-root -type d | xargs chmod 775 && \
    cd .. && \
    sed -i -e 's/casaplotms-x86_64.AppImage/squashfs-root\/AppRun/' private/plotmstool.py && \
    /usr/local/bin/pip install --extra-index-url https://casa-pip.nrao.edu/repository/pypi-casa-release/simple casaviewer==1.2.14 && \
    cd /usr/local/lib/python3.8/dist-packages/casaviewer/__bin__ && \
    ./casaviewer-x86_64.AppImage --appimage-extract && \
    rm casaviewer-x86_64.AppImage && \
    find squashfs-root -type d | xargs chmod 775 && \
    cd .. && \
    sed -i -e 's/casaviewer-x86_64.AppImage/squashfs-root\/AppRun/' private/config.py

# Install WSCLEAN, AOFLAGGER, and CARTA
RUN apt-add-repository -y -s ppa:kernsuite/kern-7 \
    && apt-get install -y wsclean aoflagger carta

# Add VLBI scripts
RUN git clone https://github.com/jive-vlbi/casa-vlbi \
    && cp casa-vlbi/*py /usr/local/bin \
    && cp -r casa-vlbi/casavlbitools /usr/local/lib/python3.8/dist-packages \
    && rm -rf casa-vlbi

# Add plotcalng; regular plotcal is removed from CASA6
RUN git clone https://github.com/aardk/evn-tools \
    && cp -r evn-tools/python/evn_tools /usr/local/lib/python3.8/dist-packages/ \
    && rm -rf evn-tools \
    && /usr/local/bin/pip install pyvo

# Install jupyter casa wrapper and copy fixed casa tasked
RUN mkdir -p /usr/local/lib/python3.8/dist-packages
COPY python/start_casa /usr/local/lib/python3.8/dist-packages/start_casa
COPY jupyter /usr/local/share/jupyter

RUN groupadd -g 1000  jupyter && useradd -u 1000 -m -s /bin/bash -g jupyter jupyter
EXPOSE 8888
USER jupyter
WORKDIR /home/jupyter
RUN mkdir -p /home/jupyter/.jupyter /home/jupyter/work
COPY --chown=jupyter:jupyter docker/jupyter_notebook_config.py /home/jupyter/.jupyter
COPY --chown=jupyter:jupyter docker/create_font_cache.py /home/jupyter
RUN python3 create_font_cache.py
