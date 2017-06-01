FROM ubuntu:16.04
RUN echo "deb http://nl.archive.ubuntu.com/ubuntu/ xenial multiverse" >> /etc/apt/sources.list \
    && echo "deb http://nl.archive.ubuntu.com/ubuntu/ xenial-updates multiverse" >> /etc/apt/sources.list \
    && apt-get update && apt-get install -y apt-utils
#RUN apt-get install -y debconf-utils
#COPY debconf-preseed.cfg /tmp/debconf-preseed.cfg
#RUN debconf-set-selections /tmp/debconf-preseed.cfg
RUN apt-get install -y python2.7 python-dev python-numpy python-matplotlib python-scipy python-pip \
                       libboost-regex1.58.0 libwcs5 libqt4-dbus libqwt6abi1 pgplot5 libpgsbox5 \
                       libxerces-c3.1 libsqlite3-0 swig libdbus-c++-1-0v5 libboost-program-options1.58.0 \
                       libgsl2 libfftw3-single3 libfftw3-double3 liblog4cxx10v5 libcfitsio2 \
                       libboost-filesystem1.58.0 libboost-system1.58.0 libboost-python1.58.0 libxslt1.1 \
                       python-nose dbus-x11 libdbus-glib-1-2 libdbusmenu-glib4 python-dbus xvfb\
    && apt-get clean
RUN apt-get install -y gfortran build-essential python-numpy-dev \
    && pip install --upgrade pip \
    && /usr/local/bin/pip install jupyter \
    && apt-get remove -y gfortran build-essential python-numpy-dev \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /root/.cache/pip
ADD casadeps.tar.bz2 casa-4.7.tar.bz2 casa-data.tar.bz2 casa-patch.tar.bz2 /usr/local/
RUN sed -i -e "s/usr\/lib64\/casapy/usr/" /usr/local/casa/linux64/bin/casa \
    && sed -i -e "s/2\.6/2\.7/" /usr/local/casa/linux64/bin/casa \
    && sed -i -e "s/home\/keimpema/usr\/local/g" /usr/local/casa/linux64/bin/casa-config \
    && sed -i -e "s/home\/keimpema/usr\/local/g" /usr/local/casa/linux64/makedefs
RUN groupadd -g 1000  jupyter && useradd -u 1000 -m -g jupyter jupyter
EXPOSE 8888
USER jupyter
WORKDIR /home/jupyter
ENV PYTHONPATH="/home/jupyter/.local/lib/python2.7/site-packages/:/usr/local/lib/python2.7/site-packages:/usr/local/casa/linux64/python/2.7" \
    LD_LIBRARY_PATH="/usr/local/casa/linux64/lib" \
    CASAPATH="/usr/local/casa/ linux64" \
    PATH="/usr/local/casa/linux64/bin:$PATH" \
    QT_X11_NO_MITSHM=1
RUN mkdir -p /home/jupyter/.jupyter \
    && mkdir -p /home/jupyter/.local/lib/python2.7/site-packages \
    && mkdir -p /home/jupyter/.local/share/jupyter/kernels/casapy \
    && mkdir -p /home/jupyter/.local/share/jupyter/runtime \
    && mkdir -p /home/jupyter/.local/share/jupyter/nbextensions
ADD casapy.tar.gz /home/jupyter/.local/lib/python2.7/site-packages/
COPY kernel.json /home/jupyter/.local/share/jupyter/kernels/casapy
COPY jupyter_notebook_config.py /home/jupyter/.jupyter
COPY create_font_cache.py /home/jupyter/
RUN python create_font_cache.py 
