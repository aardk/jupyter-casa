# jupyter-casa
A [Jupyter](http://jupyter.org/) kernel for [CASA](https://casa.nrao.edu/)

## Introduction

Jupyter is a web-based application which allows users to create interactive notebooks which can 
include annotated text and graphics as well as executable code. The notebook format also has the great advantage that all 
steps of the data reduction are preserved inside the notebook. This means that the whole data reduction process is 
self-documenting and fully repeatable. It also allows users to very easily make changes to their pipeline and then rerun 
the pipeline steps affected.

As part of the Obelics work-package of the EU funded [Asterics](https://www.asterics2020.eu/) project we have created a 
Jupyter kernel for CASA, a widely-used software package for processing astronomical data. 
The kernel allows all CASA tasks to be run from inside a Jupyter notebook, albeit non-interactively. Tasks which normally 
spawn a GUI window are wrapped so that their output is saved to an image instead, which is then displayed inside the notebook.

