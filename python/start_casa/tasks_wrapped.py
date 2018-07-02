import inspect
import decorator
from functools import wraps

class wrap_casa(object):
  def __init__(self, casatask):
    self.name = casatask.__name__
    self.doc = casatask.__doc__
    self.argspec = inspect.getargspec(casatask)

  def __call__(self, task):
    sp = self.argspec
    narg = len(sp[0])
    ndef = len(sp[3])
    n = narg - ndef # parameters without defaults
    print narg, ndef, n
    argdef = ','.join(sp[0][:n] + ['{}={}'.format(sp[0][n+i], sp[3][i]) for i in range(ndef)])
    func_def = 'def {name}({argdef}):\n  return task({args})'.format(name = self.name, argdef = argdef, args=','.join(sp[0]))
    print func_def
    func_ns = {'task': task}
    exec func_def in func_ns
    wrapped_task = func_ns[self.name]
    wrapped_task.__doc__ = self.doc
    wrapped_task.__dict__ = task.__dict__
    wrapped_task.__module__ = task.__module__
    return wrapped_task

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

    #@wraps(task)
    def wrapped_task(*args, **kwargs):
	print 'args = {}, kwargs = {}'.format(args, kwargs)
        # the first argument to task.__call__ is self
	#args = (task,) + args
        tempfile = 'casapy_temp.txt'
        doprint = set_parameter_if_not_exists(task, 'listfile', tempfile, args, kwargs)
        set_parameter(task, 'overwrite', True, args, kwargs)
        # Run task and optionally print results to the screen
	print 'args = {}, kwargs = {}'.format(args, kwargs)
        retval = task(*args, **kwargs)
        if retval and doprint:
            print_logfile(tempfile)
        return retval
    return wrapped_task

from listobs_cli import listobs_cli_
class listobs_wrapped(listobs_cli_, object):
    def print_logfile(self, filename):
        f = open(filename, 'r')
        line = f.readline()
        while line != "":
            print line,
            line = f.readline()
        f.close()

    # TODO: For the parent __call__ to infer the correct function signiture we reproduce it here
    # When casa switches to python3 this can be achieved using functools.wraps
    def __call__(self, *args):
        aips_style = all([x == None for x in args])
	listfile = 'casapy_temp.txt'
        if aips_style:
            # TODO check with tput if we should restore listfile, and overwrite
	    if (self.parameters['overwrite'] != True) or \
               (self.parameters['listfile'] == None):
                print 'overwrite! new = ', listfile
	        self.parameters['listfile'] =  listfile
   	        self.parameters['overwrite'] = True
	    else:
	        listfile = self.parameters['listfile']
	else:
	    sp = inspect.getargspec(self.__call__)[0][1:]
            ilistfile = sp.index('listfile')
            ioverwrite = sp.index('overwrite')
	    if (args[ioverwrite] != True) or (args[ilistfile] == None):
	      newargs = list(args)
              newargs[ilistfile] = listfile
	      newargs[ioverwrite] = True
              args = newargs
            else:
	      listfile = newargs[ilistfile]
        ## Run task and optionally print results to the screen
	print 'pre call parameters:', self.parameters
        retval = super(listobs_wrapped, self).__call__(*args)
	print retval, listfile
        if retval:
            self.print_logfile(listfile)
        return retval

# Wrap plotms to inline the output plot into the notebook.
# Unless explicitly enabled we also disable the gui
def wrap_plotms(task):
    @wraps(task)
    def wrapped_task(*args, **kwargs):
        # the first argument to task.__call__ is self
	args = (task,) + args
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
        # the first argument to task.__call__ is self
	args = (task,) + args
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

listobs = listobs_wrapped()
#listobs.__call__ = wrap_listfile(listobs.__call__)
plotms.__call__ = wrap_plotms(plotms.__call__)
viewer.__call__ = wrap_viewer(viewer.__call__)
