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
Run cd /usr/local && \
    wget https://github.com/CARTAvis/carta/releases/download/v1.2.2/CARTA-v1.2.2-remote.tgz && \
    apt-get install -y libnss3 libgdk-pixbuf2.0-0 libgtk-3-0 #libx11-xcb1 libxss1 libasound2 && \
    tar zxf CARTA-v1.2.2-remote.tgz
# Install jupyter casa wrapper and copy fixed casa tasked
RUN mkdir -p /usr/local/lib/python3.6/dist-packages
COPY python/start_casa /usr/local/lib/python3.6/dist-packages/start_casa
#COPY python/casa/task_setjy.patch /usr/local/
COPY jupyter /usr/local/share/jupyter
#RUN  patch lib/python3.6/dist-packages/casatasks/private/task_setjy.py /usr/local/task_setjy.patch

RUN groupadd -g 1000  jupyter && useradd -u 1000 -m -g jupyter jupyter
EXPOSE 8888
USER jupyter
WORKDIR /home/jupyter
ENV PYTHONPATH="/usr/local/lib/python2.7/dist-packages:/usr/local/casa/linux64/lib/python2.7" \
    LD_LIBRARY_PATH="/usr/local/casa/linux64/lib" \
    CASAPATH="/usr/local/casa/ linux64" \
    PATH="/usr/local/casa/linux64/bin:$PATH" \
    QT_X11_NO_MITSHM=1
RUN mkdir -p /home/jupyter/.jupyter /home/jupyter/work
COPY --chown=jupyter:jupyter docker/jupyter_notebook_config.py /home/jupyter/.jupyter
COPY --chown=jupyter:jupyter docker/create_font_cache.py /home/jupyter
RUN python3 create_font_cache.py
