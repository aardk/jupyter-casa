import os
import time
import sys
import traceback
from ipykernel.ipkernel import IPythonKernel
from IPython.core.getipython import get_ipython
import IPython
if os.environ.has_key('LD_PRELOAD'):
    del os.environ['LD_PRELOAD']

import argparse
import casa_system_defaults
from casa_system_defaults import casa

__pylib = os.path.dirname(os.path.realpath(casa_system_defaults.__file__))
__init_scripts = [
    "init_begin_startup.py",
    "init_system.py",
    "init_logger.py",
    "init_user_pre.py",
    "init_dbus.py",
    "init_tools.py",
    "init_tasks.py",
    "init_funcs.py",
    "init_pipeline.py",
    "init_mpi.py",
    "init_docs.py",
    "init_user_post.py",
    "init_crashrpt.py",
    "init_end_startup.py",
    "init_welcome.py",
]

##
## this is filled via register_builtin (from casa_builtin.py)
##
casa_builtins = { }

##
## this is filled via add_shutdown_hook (from casa_shutdown.py)
##
casa_shutdown_handlers = [ ]

##
## final interactive exit status...
## runs using "-c ..." exit from init_welcome.py
##
startup_scripts = filter( os.path.isfile, map(lambda f: __pylib + '/' + f, __init_scripts ) )

from init_welcome_helpers import immediate_exit_with_handlers

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
        self.logfile = open(casa['files']['logfile'], 'r')
    
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
            button_id = str(time.time()).replace('.', '_') # Make sure all IDs are unique
            errorhappened = any(['Some arguments failed to verify' in logline
                                   for logline in loglines]) or \
                            any(['Please check that the file ' in logline
                                   for logline in loglines])
            if errorhappened:
                errorcolor = ' style="background-color:red"'
                errorin = ' in'
                buttontext = 'Hide log'
            else:
                errorcolor = ''
                errorin = ''
                buttontext = 'Show log'
            html_code = '<button type="button" ' + errorcolor + 'class="btn btn-info" data-toggle="collapse" id="' + button_id + '" data-target="#log' + button_id + '" ' +\
                   'onclick="if ($(\'#\'+this.id).html()==\'Show log\') {$(\'#\'+this.id).html(\'Hide log\')} else {$(\'#\'+this.id).html(\'Show log\')}; return false"' + \
                   '>' + buttontext + '</button> <div class="collapse' + errorin + '" id="log' + button_id + '">' + "<br>".join(loglines) + '</div>'
            IPython.display.display_html(html_code, raw=True)
        return result
