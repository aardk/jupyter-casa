# jupyter-casa
A [Jupyter](http://jupyter.org/) kernel for [CASA](https://casa.nrao.edu/)

## Introduction

Jupyter is a web-based application which allows users to create interactive notebooks which can 
include annotated text and graphics as well as executable code. The notebook format has the great advantage that all 
steps of the data reduction are preserved inside the notebook. This means that the whole data reduction process is 
self-documenting and fully repeatable. It also allows users to very easily make changes to their pipeline and then rerun 
the pipeline steps affected.

As part of the EU funded [ESCAPE](https://projectescape.eu/) project we have created a 
Jupyter kernel for CASA, a widely-used software package for processing astronomical data. 
The kernel allows all CASA tasks to be run from inside a Jupyter notebook, albeit non-interactively. Tasks which normally 
spawn a GUI window are wrapped so that their output is displayed inside the notebook instead.

The Jupyter kernel is distributed as a [Docker](https://hub.docker.com/r/penngwyn/jupytercasa) image which includes the latest
version of CASA and a number of additional software (see below).

## Installation

The Docker images can be pulled using:
```
docker pull penngwyn/jupytercasa
```

While it is possible to use this Docker image directly, for end users it is recommended to use the Docker images through 
either [Vagrant](https://www.vagrantup.com/) or [Apptainer/Singularity](https://apptainer.org/). 

### Vagrant

Vagrant is a front-end for various containerization and virtualization technologies, including Docker.
Installation instructions for Vagrant can he found here: https://www.vagrantup.com/downloads

After cloning this Git repository, change to the Vagrant directory inside the repository
```
git clone https://github.com/aardk/jupyter-casa.git
cd jupyter-casa/vagrant
```

Before jupyter-casa can launched, you first need to tell Vagrant where your data lives.
Vagrant is controlled through a file called [Vagrantfile](vagrant/Vagrantfile). 
In the provided Vagrantfile there is one line which is commented out:
```
 #config.vm.synced_folder "/path/to/data", "/home/jupyter/work"
```

This line needs to be uncommented (remove the #), and `/path/to/data' has to be replaced by the absolute path to where your data is stored.
For example:
```
  config.vm.synced_folder "/opt/shared-data", "/home/jupyter/work"
```

Then Vagrant can be started by executing (still inside the vagrant directory)
```
vagrant up
```
After the Vagrant virtual machine has been started you can connect to it via *ssh* by executing (still inside the vagrant directory)
```
vagrant ssh
```
This will give you a shell within a Vagrant VM, jupyter can then be started by executing
```
jupyter lab
```
## Usage
### Apptainer/Singularity

Apptainer is the new name for the Singularity container system. All commands below use Apptainer, but if you still have
Singularity installed then you can simply replace apptainer with singularity in each command.

First the Docker image needs to be converted to an Apptainer container by executing

`
apptainer pull docker://penngwyn/jupytercasa:latest
`

Unlike Docker, an Apptainer container runs with UID of the current user (i.e. the user executing `singularity run`).
The home directory of the user on the local filesystem will also be accessible inside the container, but by default
only the home directory is shared with the container. Therefore any symbolic links which point to locations outside of the
home directory will not be valid inside the container.

Fortunately, it is fairly straightforward to make your local filesystem accessible to the container using the *-B* option.
For example to mount a directory called */data* inside the container execute:

`
apptainer run -B /data:$HOME/data jupytercasa_latest.sif
`

### Docker
Even though we wrap all CASA tasks so that they will not launch a GUI window, the QT based CASA tasks still require X11, unfortunately.
Tasks such as *plotms* won't start unless X11 is working even when it doesn't even open a window.
Therefore the local X11 socket needs to be shared with Docker container.

The simplest incantation to start JUPYTER on a recent Ubuntu:

`
docker run --rm -p 8888:8888 -i -t -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY penngwyn/jupytercasa 
`

Note that the `'--rm'` option will make DOCKER delete the container after use.

Of course the above example is not very useful as the container will not be able to access locally stored *measurement sets*.
To add a data directory to the DOCKER container is, fortunately, very simple using the `-v` option:

`
docker run --rm -p 8888:8888 -i -t -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY -v PATH_TO_DATA_DIR:/home/jupyter/data penngwyn/jupytercasa
`

Where `PATH_TO_DATA_DIR` should be replaced with the full path to your local data directory.

The above examples use a JUPYTER kernel which is baked into the DOCKER image. It is also possible to use the GITHUB development version
within the CASA container, from the root of the source tree run:

`
docker run --rm -p 8888:8888 -i -t -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY -v $PWD/jupyter:/home/jupyter/.local/share/jupyter -v $PWD/python/casapy:/home/jupyter/.local/lib/python2.7/site-packages/casapy -v PATH_TO_DATA_DIR:/home/jupyter/data penngwyn/jupytercasa 
` 

## Examples

In the *examples* directory there is a notebook which contains the NRAO continuum VLA tutorial. To run that code locally
be sure to download the data files from the [NRAO wiki](https://casaguides.nrao.edu/index.php?title=VLA_Continuum_Tutorial_3C391).

Also don't forget to make the directory available to the DOCKER container using the `-v` option as is explained above.
