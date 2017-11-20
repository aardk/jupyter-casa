Bootstrap: docker
From: ubuntu:16.04
IncludeCmd: no

%runscript
    echo "Starting Jupyter"
    jupyter notebook

%environment
  export PYTHONPATH="/usr/local/lib/python2.7/dist-packages:/usr/local/casa/linux64/python/2.7" 
  export LD_LIBRARY_PATH="/usr/local/casa/linux64/lib"
  export CASAPATH="/usr/local/casa/ linux64"
  export PATH="/usr/local/casa/linux64/bin:$PATH"
  export QT_X11_NO_MITSHM=1
  unset XDG_RUNTIME_DIR 

%post
    # Setup enviroment
    echo deb http://nl.archive.ubuntu.com/ubuntu/ xenial main restricted universe multiverse >/etc/apt/sources.list
    echo deb http://nl.archive.ubuntu.com/ubuntu/ xenial-updates main restricted universe multiverse >>/etc/apt/sources.list

    apt-get update && apt-get install -y apt-utils debconf-utils && apt-get upgrade -y
    apt-get install -y python2.7 python-dev python-numpy python-matplotlib python-scipy python-pip xorg-dev\
                       libboost-regex1.58.0 libwcs5 libqt4-dbus libqwt6abi1 pgplot5 libpgsbox5 \
                       libxerces-c3.1 libsqlite3-0 swig libdbus-c++-1-0v5 libboost-program-options1.58.0 \
                       libgsl2 libfftw3-single3 libfftw3-double3 liblog4cxx10v5 libcfitsio2 \
                       libboost-filesystem1.58.0 libboost-system1.58.0 libboost-python1.58.0 libxslt1.1 \
                       python-nose dbus-x11 libdbus-glib-1-2 libdbusmenu-glib4 python-dbus xvfb git wget bzip2
    apt-get clean

    # install jupyter
    apt-get install -y gfortran build-essential python-numpy-dev
    pip install --upgrade pip
    /usr/local/bin/pip install jupyter

    # Some cleanup TODO: We could remove much more
    apt-get remove -y gfortran build-essential python-numpy-dev
    apt-get autoremove -y
    apt-get clean
    rm -rf /root/.cache/pip

    # Install casa wrapper
    git clone https://github.com/aardk/jupyter-casa.git
    mkdir -p /usr/local/lib/python2.7/dist-packages
    mv jupyter-casa/python/casapy /usr/local/lib/python2.7/dist-packages/
    cp -r jupyter-casa/jupyter /usr/local/share/

    # Install pre-build casa
    wget ftp://ftp.astron.nl/outgoing/jive/keimpema/casadeps.tar.bz2
    tar jxvpf casadeps.tar.bz2 -C /usr/local
    rm casadeps.tar.bz2
    wget ftp://ftp.astron.nl/outgoing/jive/keimpema/casa-4.7.tar.bz2
    tar jxvpf casa-4.7.tar.bz2 -C /usr/local
    rm casa-4.7.tar.bz2
    wget ftp://ftp.astron.nl/outgoing/jive/keimpema/casa-data.tar.bz2
    tar jxvpf casa-data.tar.bz2 -C /usr/local
    rm casa-data.tar.bz2
    wget ftp://ftp.astron.nl/outgoing/jive/keimpema/casa-patch.tar.bz2
    tar jxvpf casa-patch.tar.bz2 -C /usr/local
    rm casa-patch.tar.bz2
    sed -i -e "s/usr\/lib64\/casapy/usr/" /usr/local/casa/linux64/bin/casa
    sed -i -e "s/2\.6/2\.7/" /usr/local/casa/linux64/bin/casa
    sed -i -e "s/home\/keimpema/usr\/local/g" /usr/local/casa/linux64/bin/casa-config
    sed -i -e "s/home\/keimpema/usr\/local/g" /usr/local/casa/linux64/makedefs
    python jupyter-casa/docker/create_font_cache.py 
    rm -rf jupyter-casa
