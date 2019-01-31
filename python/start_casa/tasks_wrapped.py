from recipe import casatasks as c
from functools import wraps
import inspect
import IPython

# NB: The tasks which are wrapped by the minimal recomputation framework only
# have the function style invocation, so no go() style syntax.

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
        # Disable the gui (unless exiplicitly enabled)
        set_parameter_if_not_exists(task, 'showgui' , False, args, kwargs)

        # Run task and print results to the screen, 
        # NB: recipe wrapped task returns name of plotfile
        plotfile = task(*args, **kwargs)
        if plotfile:
            # FIXME Getting IPython from the stack
            IPython = inspect.stack()[1][0].f_locals['IPython']
            imfmt = get_parameter(task, 'expformat', args, kwargs)
            if imfmt == None:
                imfmt = 'png'
            i = IPython.display.Image(plotfile, format=imfmt)
            IPython.display.display(i)
        return plotfile

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

from listobs import listobs
listobs = wrap_listfile(listobs)
from viewer import viewer
viewer = wrap_viewer(viewer)
plotms = wrap_plotms(c.plotms)
ft = c.ft
gaincal = c.gaincal
gencal = c.gencal
bandpass = c.bandpass
fringefit = c.fringefit
applycal = c.applycal
split = c.split
importuvfits = c.importuvfits
importfitsidi = c.importfitsidi
fixvis = c.fixvis
flagdata = c.flagdata
clean = c.clean
concat = c.concat
setjy = c.setjy
