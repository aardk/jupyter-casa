#!/bin/bash
if [ ! -e 3c391_ctm_mosaic_20s_4mhz_spw0.ms.tgz ]
then
  wget ftp://ftp.astron.nl/outgoing/jive/keimpema/3c391_ctm_mosaic_20s_4mhz_spw0.ms.tgz
fi
docker build -t jupytercasa-demo .
