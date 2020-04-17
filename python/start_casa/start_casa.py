import os
import time
import sys
import traceback
from ipykernel.ipkernel import IPythonKernel
from IPython.core.getipython import get_ipython
import IPython
import ipywidgets

if 'LD_PRELOAD' in os.environ:
    del os.environ['LD_PRELOAD']

def __init_config(config,flags,args):
    if flags.datapath is not None:
        datap = list(map(os.path.abspath,filter(os.path.isdir,list(flags.datapath.split(':')))))
        config.datapath = datap
    if flags.logfile is not None:
        config.logfile = flags.logfile if flags.logfile.startswith("/") else os.path.realpath(os.path.join('.',flags.logfile))

    config.flags = flags
    config.args = args

###
### this will be used by inp/go which are introduced in init_subparam
###
casa_inp_go_state = { 'last': None }

###
### this will be used by register_builtin for making casa builtins immutable
###
casa_builtin_state = { }

##
## this is filled via add_shutdown_hook (from casa_shutdown.py)
##
casa_shutdown_handlers = [ ]

##
## filled when -c <args> is used
##
casa_eval_status = { 'code': 0, 'desc': 0 }

import casashell
__pylib = os.path.dirname(os.path.realpath(casashell.__file__)) + '/private/'
__init_scripts = [ "init_system.py",
                 "load_tasks.py",
                 "load_tools.py",
                 "init_subparam.py",
                 "init_doc.py",
                 "init_welcome.py",
                ]

startup_scripts = list(filter( os.path.isfile, [__pylib + '/' + f for f in __init_scripts] ))

from casashell.private import config
from argparse import Namespace
casa_config_master = config
args = []
flags = Namespace(logfile = None,
                  log2term = False,
                  nologger = False,
                  nologfile = False,
                  nogui = False,
                  prompt = 'NoColor',
                  trace = False,
                  pipeline = False,
                  agg = False,
                  ipython_log = False,
                  datapath = None,
                  crash_report = True,
                  telemetry = False,
                  execute = [])

__init_config(casa_config_master,flags,args)

class LogWidget(ipywidgets.ToggleButton):
        def __init__(self, logwidget, error):
            if error:
                value = True
                button_style = "danger"
                logwidget.layout.display = 'flex'
            else:
                value = False
                button_style = "success"
                logwidget.layout.display = 'none'
            super().__init__(
                    value=value,
                    description='Log',
                    disabled=False,
                    button_style=button_style, # 'success', 'info', 'warning', 'danger' or ''
                    tooltip='Description',
                    icon='' # (FontAwesome names without the `fa-` prefix)
            )
            self.logwidget = logwidget

        def disable_display(self):
            self.logwidget.layout.display = 'none'

        def enable_display(self):
            self.logwidget.layout.display = 'flex'

def loghandler(change):
    """ Show / Hide log messages """
    if change['new'] == False:
        change['owner'].disable_display()
    else:
        change['owner'].enable_display()

class CasapyKernel(IPythonKernel):
    implementation = 'Casapy'
    implementation_version = '1.0'
    language = 'casa'
    language_version = '1.0'
    language_info = {'mimetype': 'text/plain', 'name': 'Casa'}
    banner = "Jupyter wrapper for casa"

    def start(self):
        super(CasapyKernel, self).start()
        self.do_execute('%matplotlib inline', True, False, {}, False)
        #self.do_execute('%matplotlib ipympl', True, False, {}, False)
        for i in startup_scripts:
           self.do_execute('%run -i {}'.format(i), True, False, {}, False)
        wrappers = os.path.dirname(os.path.realpath(__file__)) + '/tasks_wrapped.py'
        self.do_execute('%run -i {}'.format(wrappers), True, False, {}, False)
        import casashell.private.config as config
        self.logfile = open(config.logfile, 'r')

    def do_execute(self, code, silent, store_history=True, user_expressions=None,
                   allow_stdin=False):
        result = super(CasapyKernel, self).do_execute(code, silent, store_history, user_expressions, allow_stdin)
        # Traverse log, this is not ideal. It would be better to have our own logger application and
        # use that to obtain logging information.
        loglines = []
        try:
          logfile = self.logfile
        except AttributeError:
          # Casa logger is not active yet
          return result
        line = logfile.readline()
        while line != "":
            sline = line.split()
            if len(sline) >= 4:
                task = sline[3].split(':')[0]
                if (task != '') and (task != 'casa'):
                    loglines.append(line)
            line = logfile.readline()
        # Display log messages
        if len(loglines) > 0:
            errorhappened = any(['Some arguments failed to verify' in logline
                                   for logline in loglines]) or \
                            any(['Please check that the file ' in logline
                                   for logline in loglines]) or \
                            any(['An error occurred' in logline
                                   for logline in loglines])
            out = ipywidgets.Output(layout={'max_height': "20em", 'overflow_y':'auto'})
            with out:
                for line in loglines:
                    print(line, end='')
            w = LogWidget(out, errorhappened)
            w.observe(loghandler, 'value')
            IPython.display.display(w)
            IPython.display.display(out)
        return result
