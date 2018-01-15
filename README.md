# jupyter-casa
A [Jupyter](http://jupyter.org/) kernel for [CASA](https://casa.nrao.edu/)

## Introduction

Jupyter is a web-based application which allows users to create interactive notebooks which can 
include annotated text and graphics as well as executable code. The notebook format has the great advantage that all 
steps of the data reduction are preserved inside the notebook. This means that the whole data reduction process is 
self-documenting and fully repeatable. It also allows users to very easily make changes to their pipeline and then rerun 
the pipeline steps affected.

As part of the Obelics work-package of the EU funded [Asterics](https://www.asterics2020.eu/) project we have created a 
Jupyter kernel for CASA, a widely-used software package for processing astronomical data. 
The kernel allows all CASA tasks to be run from inside a Jupyter notebook, albeit non-interactively. Tasks which normally 
spawn a GUI window are wrapped so that their output is saved to an image instead, which is then displayed inside the notebook.

## Installation

Because Jupyter requires a much more current python distibution than what is provided in NRAO's CASA releases, a custom build
of CASA is required. We distribute a [DOCKER](https://www.docker.com/) image containing a version of CASA which uses the
most recent (I)python, matplotlib, etc. Note that this version of CASA can only be used from within Jupyter.

Installation is as simple as executing:
`
docker pull penngwyn/jupytercasa
`

Alternatively there is also a [SINGULARITY](http://singularity.lbl.gov/index.html) image which may be a bit easier to use, it can be downloaded by executing:

`
singularity pull --name jupyter-casa.simg shub://aardk/jupyter-casa
`

## Usage
### Singularity
The simplest way to start the Jupyter server is to execute:

`
singularity run jupyter-casa.simg
`

Unlike DOCKER, a SINGULARITY containter runs with UID of the current user (i.e. the user executing `singularity run`).
The home directory of the user on the local filesystem will also be accessible inside the container, but by default
only the home directory is shared with the container. Therefore any symbolic links which point to locations outside of the
home directory will not be valid inside the container.

Fortunately, it is fairly straigthforward to make your local filesystem accessible to the container using the *-B* option.
For example to mount a directory called */data* inside the container execute:

`
singularity run -B /data:$HOME/data jupyter-casa.simg
`

### Docker
Even though we wrap all CASA tasks so that they will not launch a GUI window, the QT based CASA tasks still require X11, unfortunately.
Tasks such as *plotms* won't start unless X11 is working even when it doesn't even open a window.
Therefore the local X11 socket needs to be shared with Docker container.

The simplest incantation to start JUPYTER on a recent Ubuntu:

`
docker run --rm -p 8888:8888 -i -t -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY penngwyn/jupytercasa /bin/sh -c "jupyter notebook"
`

Note that the `'--rm'` option will make DOCKER delete the container after use.

Of course the above example is not very useful as the container will not be able to access locally stored *measurement sets*.
To add a data directory to the DOCKER container is, fortunately, very simple using the `-v` option:

`
docker run --rm -p 8888:8888 -i -t -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY -v PATH_TO_DATA_DIR:/home/jupyter/data penngwyn/jupytercasa /bin/sh -c "jupyter notebook"
`

Where `PATH_TO_DATA_DIR` should be replaced with the full path to your local data directory.

The above examples use a JUPYTER kernel which is baked into the DOCKER image. It is also possible to use the GITHUB development version
within the CASA container, from the root of the source tree run:

`
docker run --rm -p 8888:8888 -i -t -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY -v $PWD/jupyter:/home/jupyter/.local/share/jupyter -v $PWD/python/casapy:/home/jupyter/.local/lib/python2.7/site-packages/casapy -v PATH_TO_DATA_DIR:/home/jupyter/data penngwyn/jupytercasa /bin/sh -c "jupyter notebook"
` 

## Examples

In the *examples* directory there is a notebook which contains the NRAO continuum VLA tutorial. To run that code locally
be sure to download the data files from the [NRAO wiki](https://casaguides.nrao.edu/index.php?title=VLA_Continuum_Tutorial_3C391).

Also don't forget to make the directory available to the DOCKER container using the `-v` option as is explained above.
