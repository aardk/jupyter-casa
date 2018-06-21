import inspect
from functools import wraps

# A few utility functions needed because an argument can be either positional
# or named
def set_parameter_if_not_exists(task, param, value, args, kwargs):
    pos = inspect.getargspec(task)[0].index(param)
    if (len(args) <= pos) and (param not in kwargs):
        kwargs[param] = value
        return True
    return False

def set_parameter(task, param, value, args, kwargs):
    pos = inspect.getargspec(task)[0].index(param)
    if (len(args) > pos):
        args[pos] = value
    else:
        kwargs[param] = value

def get_parameter(task, param, args, kwargs):
    pos = inspect.getargspec(task)[0].index(param)
    if (len(args) > pos):
        return args[pos]
    elif param in kwargs:
        return kwargs[param]
    return None

# Wraps tasks which have the 'listfile' argument. If the user has not already
# set 'listfile' then we supply our own and print the result to the screen.
def wrap_listfile(task):
    def print_logfile(filename):
        f = open(filename, 'r')
        line = f.readline()
        while line != "":
            print line,
            line = f.readline()
        f.close()

    @wraps(task)
    def wrapped_task(*args, **kwargs):
        tempfile = 'casapy_temp.txt'
        doprint = set_parameter_if_not_exists(task, 'listfile', tempfile, args, kwargs)
        set_parameter(task, 'overwrite', True, args, kwargs)
        # Run task and optionally print results to the screen
        retval = task(*args, **kwargs)
        if retval and doprint:
            print_logfile(tempfile)
        return retval
    return wrapped_task

# Wrap plotms to inline the output plot into the notebook.
# Unless explicitly enabled we also disable the gui
def wrap_plotms(task):
    @wraps(task)
    def wrapped_task(*args, **kwargs):
        # Set temporary plot if the user didn't already supply a plotfile
        if set_parameter_if_not_exists(task, 'plotfile', 'plotms_temp.png', args, kwargs):
            set_parameter(task, 'overwrite', True, args, kwargs)
        else:
            set_parameter_if_not_exists(task, 'overwrite', True, args, kwargs)
        # Disable the gui (unless exiplicitly enabled)
        set_parameter_if_not_exists(task, 'showgui' , False, args, kwargs)

        # Run task and print results to the screen
        retval = task(*args, **kwargs)
        if retval:
            plotfile = get_parameter(task, 'plotfile', args, kwargs)
            # FIXME Getting IPython from the stack
            IPython = inspect.stack()[1][0].f_locals['IPython']
            i = IPython.display.Image(plotfile)
            IPython.display.display(i)
        return retval

    return wrapped_task

# Wrap viewer to inline the output plot into the notebook.
# Unless explicitly enabled we also disable the gui
def wrap_viewer(task):
    @wraps(task)
    def wrapped_task(*args, **kwargs):
        # Set temporary plot if the user didn't already supply an outputfile
        if set_parameter_if_not_exists(task, 'outfile', 'viewer_temp.png', args, kwargs):
            set_parameter(task, 'outformat', 'png', args, kwargs)
        # Disable the gui (unless exiplicitly enabled)
        set_parameter_if_not_exists(task, 'gui' , False, args, kwargs)

        # Run task and print results to the screen
        # NB: Oddly the viewer task returns None on success
        retval = task(*args, **kwargs)
        if retval != False:
            outfile = get_parameter(task, 'outfile', args, kwargs)
            # FIXME Getting IPython from the stack
            IPython = inspect.stack()[1][0].f_locals['IPython']
            i = IPython.display.Image(outfile)
            IPython.display.display(i)
        return retval

    return wrapped_task

from accum import  accum
from applycal import  applycal
from asdmsummary import  asdmsummary
from autoclean import  autoclean
from bandpass import  bandpass
from blcal import  blcal
from boxit import  boxit
from browsetable import  browsetable
from calstat import  calstat
from caltabconvert import  caltabconvert
from clean import  clean
from clearcal import  clearcal
from clearplot import  clearplot
from clearstat import  clearstat
from concat import  concat
from conjugatevis import  conjugatevis
from csvclean import  csvclean
from cvel import  cvel
from cvel2 import  cvel2
from deconvolve import  deconvolve
from delmod import  delmod
from exportasdm import  exportasdm
from exportfits import  exportfits
from exportuvfits import  exportuvfits
from feather import  feather
from fixplanets import  fixplanets
from fixvis import  fixvis
from flagcmd import  flagcmd
from flagdata import  flagdata
from flagmanager import  flagmanager
from fluxscale import  fluxscale
from fringefit import fringefit
from ft import  ft
from gaincal import  gaincal
from gencal import  gencal
from hanningsmooth import  hanningsmooth
from imcollapse import  imcollapse
from imcontsub import  imcontsub
from imfit import  imfit
from imdev import  imdev
from imhead import  imhead
from imhistory import  imhistory
from immath import  immath
from immoments import  immoments
from impbcor import  impbcor
from importatca import  importatca
from importasap import  importasap
from importasdm import  importasdm
from importevla import  importevla
from importfits import  importfits
from importfitsidi import  importfitsidi
from importgmrt import  importgmrt
from importmiriad import  importmiriad
from importnro import  importnro
from importuvfits import  importuvfits
from importvla import  importvla
from imrebin import  imrebin
from imreframe import  imreframe
from imregrid import  imregrid
from imsmooth import  imsmooth
from imstat import  imstat
from imsubimage import  imsubimage
from imtrans import  imtrans
from imval import  imval
from imview import  imview
from initweights import  initweights
from listcal import  listcal
from listhistory import  listhistory
from listfits import  listfits
from listobs import  listobs
listobs = wrap_listfile(listobs)
from listpartition import  listpartition
from listsdm import  listsdm
from listvis import  listvis
from makemask_cli import  makemask_cli as makemask
from mosaic import  mosaic
from msview import  msview
from mstransform import  mstransform
from msuvbin import  msuvbin
from oldhanningsmooth import  oldhanningsmooth
from oldplotants import oldplotants
from oldsplit import  oldsplit
from plotants import  plotants
from plotbandpass import  plotbandpass
from plotcal import  plotcal
from plotms import  plotms
plotms = wrap_plotms(plotms)
from plotuv import  plotuv
from plotweather import  plotweather
from plotprofilemap import  plotprofilemap
from partition import  partition
from polcal import  polcal
from predictcomp import  predictcomp
from impv import  impv
from rerefant import  rerefant
from rmfit import  rmfit
from rmtables import  rmtables
from sdbaseline import  sdbaseline
from sdcal import  sdcal
from sdfit import  sdfit
from sdfixscan import  sdfixscan
from sdgaincal import  sdgaincal
from sdimaging import  sdimaging
from tsdimaging import tsdimaging
from sdsidebandsplit import sdsidebandsplit
from sdsmooth import  sdsmooth
from setjy import  setjy
from ssoflux import  ssoflux
from simalma import  simalma
from simobserve import  simobserve
from simanalyze import  simanalyze
from slsearch import  slsearch
from smoothcal import  smoothcal
from specfit import  specfit
from specflux import  specflux
from specsmooth import  specsmooth
from splattotable import  splattotable
from split import  split
from spxfit import  spxfit
from statwt import  statwt
from statwt2 import  statwt2
from tclean import  tclean
from tclean2 import  tclean2
from testconcat import  testconcat
from uvcontsub import  uvcontsub
from uvcontsub3 import  uvcontsub3
from uvmodelfit import  uvmodelfit
from uvsub import  uvsub
from viewer import  viewer
viewer = wrap_viewer(viewer)
from wvrgcal import  wvrgcal
from virtualconcat import  virtualconcat
from vishead import  vishead
from visstat import  visstat
from widebandpbcor import  widebandpbcor
from widefield import  widefield

from split import  split
from hanningsmooth import  hanningsmooth
from tget import *
