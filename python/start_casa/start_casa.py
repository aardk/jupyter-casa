import os
import time
import sys
import traceback
import secrets
from ipykernel.ipkernel import IPythonKernel
from IPython.core.getipython import get_ipython
from traitlets.config.loader import Config
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
__init_scripts = [ "init_begin_startup.py",
                 "init_system.py",
                 "load_tasks.py",
                 "load_tools.py",
                 "init_subparam.py",
                 "init_doc.py",
                 "init_welcome.py"
                ]

startup_scripts = list(filter( os.path.isfile, [__pylib + '/' + f for f in __init_scripts] ))


from argparse import Namespace
args = []
flags = Namespace(logfile = None,
                  log2term = False,
                  nologger = False,
                  nologfile = False,
                  nogui = False,
                  norc = True,
                  colors = "Neutral",
                  prompt = 'NoColor',
                  trace = False,
                  pipeline = False,
                  agg = False,
                  ipython_log = False,
                  datapath = None,
                  notelemetry = False,
                  nocrashreport = True,
                  user_site = True,
                  execute = [])
import casashell as _cs
_cs.argv = sys.argv
_cs.flags = flags
from casashell.private import config
casa_config_master = config

__init_config(casa_config_master,flags,args)

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
        self.init_logbuttons()

    def init_logbuttons(self):
        self.logbtn_template = """
<style>
    label.logbtn {{
        font-weight: bold;
        text-align: center;
        background-color: {bgcolor};
        width: 8em;
        border: 2px solid black;
        border-radius: 5px;
        display: block;
    }}
    input, label#hidelog{elid}, #log{elid} {{
        display: none;
    }}
    input#logbtn{elid}:checked ~ label#showlog{elid} {{
        display: none;
    }}
    input#logbtn{elid}:checked ~ label#hidelog{elid} {{
        display: block;
    }}
    input#logbtn{elid}:checked ~ #log{elid} {{
        display: block;
    }}
</style>
<input id="logbtn{elid}" type=checkbox>
    <label class="logbtn" id="showlog{elid}" for="logbtn{elid}">Show Log</label>
    <label class="logbtn" id="hidelog{elid}" for="logbtn{elid}">Hide Log</label>
<div id="log{elid}"> <br />
    {log}
    </div>
"""

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
            # Fixme errorhappened doesn't work for CASA 6.X
            errorhappened = any(['Some arguments failed to verify' in logline
                                   for logline in loglines]) or \
                            any(['Please check that the file ' in logline
                                   for logline in loglines]) or \
                            any(['An error occurred' in logline
                                   for logline in loglines])
            bgcolor = 'red' if errorhappened else 'green'
            elementid = secrets.token_urlsafe(16)
            html_code = self.logbtn_template.format(elid=elementid, bgcolor=bgcolor, log="<br>".join(loglines))
            IPython.display.display_html(html_code, raw=True)
        return result
