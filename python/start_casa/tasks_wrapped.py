import inspect
import IPython
from casashell.private.stack_manip import find_frame

# Decorate wrapper classes such that the __call__ method signiture matches the CASA task
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
    argdef = ','.join(sp[0][:n] + ['{}={}'.format(sp[0][n+i], sp[3][i]) for i in range(ndef)])
    func_def = 'def {name}({argdef}):\n  return task({args})'.format(name = self.name, argdef = argdef, args=','.join(sp[0]))
    func_ns = {'task': task}
    exec(func_def, func_ns)
    wrapped_task = func_ns[self.name]
    wrapped_task.__doc__ = self.doc
    wrapped_task.__dict__ = task.__dict__
    wrapped_task.__module__ = task.__module__
    return wrapped_task

class wrapper_parameters(object):
    __SET_NONE, __SET_GLOBAL, __REPLACE_GLOBAL, __SET_ARG = list(range(4))

    def __init__(self, task, args):
        self.task = task
        self.args = list(args)
        self.aips_style = all([x == None for x in args])
        if self.aips_style:
            self.frame = find_frame()
        self.results = {}
        
    def __getitem__(self, key):
        return self.results[key][0]

    def set_parameter(self, key, value, overwrite, conditional = []):
        task = self.task
        results = self.results
        parameter_set = overwrite
        if self.aips_style:
            # CASA6 tasks will get their parameters from two locations (#1 has priority)
            # Note that the parameters structure from CASA 5.* is gone
            # 1. Go up the stack to the IPython stack frame and check if the
            #    parameter exists as a variable in that context
            # 2. From self.__TASKNAME_dflt
            frame = self.frame 
            if key in frame and (frame[key] not in ("", None)):
                if overwrite:
                    results[key] = (value, self.__REPLACE_GLOBAL, frame[key])
                    frame[key] = value
                else:
                    results[key] = (frame[key], self.__SET_NONE, frame[key])
            else:
                # parameter not already set
                parameter_set = True
                frame[key] = value
                self.results[key] = (value, self.__SET_GLOBAL, None)
        else:
            args = self.args
            sp = inspect.getargspec(task.__call__)[0][1:]
            i = sp.index(key)
            if (args[i] == None) or overwrite:
                parameter_set = True
                results[key] = (value, self.__SET_ARG, args[i])
                args[i] = value
            else:
                results[key] = (args[i], self.__SET_NONE, args[i])

        if parameter_set:
            for par in conditional:
                self.set_parameter(*par)

    def restore_parameters(self):
        # Put back parameters altered by set_parameter 
        # (only needed for aips_style task invocation)
        if self.aips_style:
            frame = self.frame
            for key, (newval, changed, oldval) in self.results.items():
                if (changed == self.__REPLACE_GLOBAL):
                    frame[key] = oldval
                elif (changed == self.__SET_GLOBAL):
                    del frame[key]

from casashell.private.listobs import _listobs
class listobs_wrapped(_listobs, object):
    def print_logfile(self, filename):
        f = open(filename, 'r')
        line = f.readline()
        while line != "":
            print(line, end=' ')
            line = f.readline()
        f.close()

    @wrap_casa(_listobs.__call__)
    def __call__(self, *args):
        params = wrapper_parameters(self, args)
        # Set 'listfile' if not already set, and if we set 'listfile' then also set 'overwrite'
        default_listfile = 'casapy_temp.txt'
        params.set_parameter('listfile', default_listfile, False, [('overwrite', True, True)])
        try:
            retval = super(listobs_wrapped, self).__call__(*params.args)
        finally:
            params.restore_parameters()
        listfile = params['listfile']
        if retval:
            self.print_logfile(listfile)
        return retval

# Unless explicitly enabled we also disable the gui
from casaplotms.gotasks.plotms import _plotms
class plotms_wrapped(_plotms, object):
    @wrap_casa(_plotms.__call__)
    def __call__(self, *args):
        params = wrapper_parameters(self, args)
        # Set 'plotfile' if not already set, and if we set 'plotfile' then also set 'overwrite'
        default_plotfile = 'plotms_temp.png'
        params.set_parameter('plotfile', default_plotfile, False, [('overwrite', True, True)])
        plotfile = params['plotfile']
        
        # Disable gui unless explicitly enabled
        params.set_parameter('showgui', False, False)
        try:
            retval = super(plotms_wrapped, self).__call__(*params.args)
        finally:
            params.restore_parameters()
        if retval:
            i = IPython.display.Image(plotfile)
            IPython.display.display(i)
        return retval

# Wrap viewer to inline the output plot into the notebook.
# Unless explicitly enabled we also disable the gui
from casaviewer.gotasks.imview import _imview
class imview_wrapped(_imview, object):
    @wrap_casa(_imview.__call__)
    def __call__(self, *args):
        params = wrapper_parameters(self, args)

        # Set 'outfile' if not already set, and if we set 'outfile' then set the output
        # format to png
        default_outfile = 'viewer_temp.png'
        params.set_parameter('out', default_outfile, False)
        outfile = params['out']
        
        # Disable gui unless explicitly enabled
        # params.set_parameter('gui', False, False)
        try:
            retval = super(imview_wrapped, self).__call__(*params.args)
        finally:
            params.restore_parameters()

        # NB: The viewer task returns None on success
        if retval != False:
            i = IPython.display.Image(outfile)
            IPython.display.display(i)
        return retval

listobs = listobs_wrapped()
plotms = plotms_wrapped()
imview = imview_wrapped()
viewer = imview
