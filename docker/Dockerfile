FROM ubuntu:16.04
CMD ["jupyter", "notebook"]
RUN echo "deb http://nl.archive.ubuntu.com/ubuntu/ xenial multiverse" >> /etc/apt/sources.list \
    && echo "deb http://nl.archive.ubuntu.com/ubuntu/ xenial-updates multiverse" >> /etc/apt/sources.list \
    && apt-get update && apt-get install -y apt-utils debconf-utils && apt-get -y upgrade && apt-get clean

RUN apt-get install -y python2.7 python-dev python-numpy python-matplotlib python-scipy python-pip python-nose python-dbus \
                       build-essential git wget cmake flex bison g++ xvfb libcfitsio-dev libreadline6-dev libncurses5-dev \
                       libhdf5-serial-dev libpython3.5-dev libboost-python-dev libblas-dev liblapacke-dev libfftw3-dev \
                       libcfitsio3-dev wcslib-dev libboost-program-options1.58-dev libboost-filesystem1.58-dev \
                       libboost-system1.58-dev libboost-python1.58-dev libboost-thread1.58-dev libboost-regex1.58-dev \
                       libqt4-dev pgplot5 libpgsbox-dev openjdk-8-jre libdbus-1-dev libdbus-c++-dev libxml2-dev libxslt1-dev \
                       libqwt-dev libxerces-c-dev libsqlite3-dev liblog4cxx-dev doxygen swig \
    && apt-get clean

# Libgsl from 16.04 is too old for CASA, get the version from 18.04
RUN for i in libgslcblas0_2.4+dfsg-6_amd64.deb libgsl23_2.4+dfsg-6_amd64.deb libgsl-dev_2.4+dfsg-6_amd64.deb; \
    do wget http://nl.archive.ubuntu.com/ubuntu/pool/universe/g/gsl/$i; dpkg -i $i; rm $i; done

# We need an older version of libeigen3 for libsakura
RUN wget http://launchpadlibrarian.net/165141962/libeigen3-dev_3.2.0-8_all.deb \
    && dpkg -i libeigen3-dev_3.2.0-8_all.deb \
    && rm libeigen3-dev_3.2.0-8_all.deb

# install jupyter
RUN apt-get install -y gfortran build-essential python-numpy-dev \
    && pip install --upgrade pip \
    && /usr/local/bin/pip install "ipykernel<4.9.0" "notebook<5.5" widgetsnbextension \
    # Enable ipywidgets
    && jupyter nbextension enable --py widgetsnbextension --sys-prefix

# Dependencies - RPFITS
RUN wget ftp://ftp.atnf.csiro.au/pub/software/rpfits/rpfits-2.25.tar.gz \
    && tar zxvf rpfits-2.25.tar.gz \
    && cd rpfits/linux64 \
    && make install \
    && cd ../.. \
    && rm -rf rpfits*

# Dependencies - LIBSAKURA
RUN git clone https://github.com/aardk/libsakura \
    && cd libsakura \
    && wget https://github.com/google/googletest/archive/release-1.7.0.tar.gz \
    && tar zxvf release-1.7.0.tar.gz \
    && ln -s googletest-release-1.7.0 gtest \
    && mkdir build \
    && cd build \
    && cmake .. \
    && make \
    && make apidoc \
    && make install \
    && cd ../.. \
    && rm -rf libsakura

# casa data needs git lfs support
RUN wget https://github.com/git-lfs/git-lfs/releases/download/v2.3.4/git-lfs-linux-amd64-2.3.4.tar.gz \
    && tar zxvf git-lfs-linux-amd64-2.3.4.tar.gz \
    && git-lfs-2.3.4/install.sh \
    && rm -rf git-lfs-2.3.4 git-lfs-linux-amd64-2.3.4.tar.gz

ENV HOST_CPU_CORES=8 \
    CASA_BUILD_TYPE=Release \
    CASA_ARCH=linux64 \
    CASA_BRANCH=release/5.3.0 \
    workDir=/usr/local/casa \
    CASAPATH="$workDir $CASA_ARCH"

# ASAP need this patch to compile
COPY asap.patch /root

# Build casa
RUN git clone -b $CASA_BRANCH https://open-bitbucket.nrao.edu/scm/casa/casa.git $workDir \
    && cd $workDir \
    && git submodule update --init casacore \
    && git clone https://open-bitbucket.nrao.edu/scm/casa/casa-asap.git \
    && git clone --no-checkout https://open-bitbucket.nrao.edu/scm/casa/casa-data.git $workDir/data \
    && cd data \
    && git show HEAD:distro | bash \
    # cleanup git, saves ~600MB
    && rm -rf .git ../git\
    # Build casacore
    && mkdir $workDir/casacore/build \
    && cd $workDir/casacore/build \
    && cmake .. -DCMAKE_BUILD_TYPE=$CASA_BUILD_TYPE -DCMAKE_INSTALL_PREFIX=$workDir/$CASA_ARCH -DDATA_DIR=$workDir/data -DUSE_THREADS=ON -DCFITSIO_INCLUDE_DIR=/usr/include/cfitsio -DCXX11=ON -DUSE_FFTW3=ON -DCFITSIO_INCLUDE_DIR=/usr/include -DCASA_BUILD=ON -DUSE_HDF5=ON -DBUILD_PYTHON=ON \
    && make -j$HOST_CPU_CORES \
    && make install \
    && cd $workDir \
    && rm -rf casacore \
    # build casa code
    && mkdir $workDir/code/build \
    && cd $workDir/code/build \
    && mkdir gtest breakpad \
    && cd gtest \
    # For some reason automatic download of googletest and breakpad fails on my system
    && wget https://svn.cv.nrao.edu/casa/devel/googletest/googletest-release-1.7.0.tar.gz \
    && tar zxvf googletest-release-1.7.0.tar.gz \
    && cd ../breakpad \
    && wget https://casa.nrao.edu/download/devel/breakpad/breakpad-from-google-180213-patch2.tgz \
    && tar zxvf breakpad-from-google-180213-patch2.tgz \
    && cd .. \
    && cmake .. -DCMAKE_BUILD_TYPE=$CASA_BUILD_TYPE -DINTERACTIVE_ITERATION=1 -DCMAKE_INSTALL_PREFIX=$workDir/$CASA_ARCH \
    && make -j$HOST_CPU_CORES \
    && cd $workDir \
    && rm -rf code/build \
    # build gcwrap
    && mkdir $workDir/gcwrap/build \
    && cd $workDir/gcwrap/build \
    && cmake .. -Darch=$CASA_ARCH -DCMAKE_INSTALL_PREFIX=$workDir/$CASA_ARCH -DPYTHON_LIBNAME=2.7 -DCMAKE_BUILD_TYPE=$CASA_BUILD_TYPE -DINTERACTIVE_ITERATION=1 \
    && make -j$HOST_CPU_CORES \
    && cd $workDir \
    && rm -rf gcWrap \ 
    # Build asap
    && cd $workDir/casa-asap \
    && ls -l \
    && patch -p1 < /root/asap.patch \
    && mkdir $workDir/casa-asap/build \
    && cd $workDir/casa-asap/build \
    && cmake .. -Darch=$CASA_ARCH -DCMAKE_INSTALL_PREFIX=$workDir/$CASA_ARCH -DPYTHON_LIBNAME=2.7 -DCMAKE_BUILD_TYPE=$CASA_BUILD_TYPE \
    && make -j$HOST_CPU_CORES \
    && cd $workDir \
    && rm -rf casa-asap \
    && rm -rf code 

# Install jupyter casa wrapper and copy fixed casa tasked
RUN mkdir -p /usr/local/lib/python2.7/dist-packages
COPY python/start_casa /usr/local/lib/python2.7/dist-packages/start_casa
COPY jupyter /usr/local/share/jupyter
COPY python/casa/TablePlotTkAgg.py python/casa/task_setjy.py $workDir/linux64/lib/python2.7/ 

# Disable ipv6
#RUN echo "net.ipv6.conf.all.disable_ipv6 = 1\n net.ipv6.conf.default.disable_ipv6 = 1\n net.ipv6.conf.lo.disable_ipv6 = 1" >> /etc/sysctl.d/99-sysctl.conf \
#    && cat /etc/sysctl.d/99-sysctl.conf 

RUN groupadd -g 1000  jupyter && useradd -u 1000 -m -g jupyter jupyter
EXPOSE 8888
USER jupyter
WORKDIR /home/jupyter
ENV PYTHONPATH="/usr/local/lib/python2.7/dist-packages:/usr/local/casa/linux64/lib/python2.7" \
    LD_LIBRARY_PATH="/usr/local/casa/linux64/lib" \
    CASAPATH="/usr/local/casa/ linux64" \
    PATH="/usr/local/casa/linux64/bin:$PATH" \
    QT_X11_NO_MITSHM=1
RUN mkdir -p /home/jupyter/.jupyter
COPY --chown=jupyter:jupyter docker/jupyter_notebook_config.py /home/jupyter/.jupyter
COPY --chown=jupyter:jupyter docker/create_font_cache.py /home/jupyter
RUN python create_font_cache.py
