#!/bin/bash

wget ftp://ftp.astron.nl/outgoing/jive/keimpema/casadeps.tar.bz2
wget ftp://ftp.astron.nl/outgoing/jive/keimpema/casa-4.7.tar.bz2
wget ftp://ftp.astron.nl/outgoing/jive/keimpema/casa-data.tar.bz2
wget ftp://ftp.astron.nl/outgoing/jive/keimpema/casa-patch.tar.bz2
cp ../jupyter/kernels/casapy/kernel.json .
cd ../python/ && tar czf ../docker/casapy.tar.gz casapy && cd ../docker
docker build -t jupytercasa .
