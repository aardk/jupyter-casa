import os
import sys
import time
import signal
#import filecmp
#import traceback # To pretty-print tracebacks
#from subprocess import Popen, PIPE, STDOUT
from ipykernel.ipkernel import IPythonKernel

##
## toplevel frame marker
##
_casa_top_frame_ = True

##
## ensure that we're the process group leader
## of all processes that we fork...
##
try:
    os.setpgid(0,0)
except OSError, e:
    print "setgpid( ) failed: " + e.strerror
    print "                   processes may be left dangling..."

##
## watchdog... which is *not* in the casapy process group
##
if os.fork( ) == 0 :
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    ## close standard input to avoid terminal interrupts
    sys.stdin.close( )
    sys.stdout.close( )
    sys.stderr.close( )
    os.close(0)
    os.close(1)
    os.close(2)
    # get parent process to monitor
    ppid = os.getppid( )
    # create our own process group
    try:
        os.setpgid(0,0)
    except:
        pass
    while True :
        try:
            os.kill(ppid,0)
        except:
            break
        time.sleep(3)
    sleeptime = 120
    os.killpg(ppid, signal.SIGTERM)
    time.sleep(0.1)
    # wait for group to die
    for i in range(sleeptime):
        try:
            os.killpg(ppid, 0)
        except:
            # group has died, done
            sys.exit(1)
        time.sleep(1)
    # force kill it
    os.killpg(ppid, signal.SIGKILL)
    sys.exit(1)

##
## no one likes a bloated watchdog...
## ...do this after setting up the watchdog
##
try:
    import casac 
except ImportError, e:
    print "failed to load casa:\n", e
    sys.exit(1)

try:
    import matplotlib
except ImportError, e:
    print "failed to load matplotlib:\n", e
    print "sys.path =", "\n\t".join(sys.path)
    


homedir = os.getenv('HOME')
if homedir == None :
   print "Environment variable HOME is not set, please set it"
   sys.exit(1)

import casadef
import __casac__
cu = __casac__.utils.utils()

casa = { 'build': {
             'time': casadef.build_time,
             'version': cu.version_info( ),
             'number': casadef.subversion_revision
         },
         'source': {
             'url': casadef.subversion_url,
             'revision': casadef.subversion_revision
         },
         'helpers': {
             'crashPoster' : 'CrashReportPoster',
             'logger': 'casalogger',
             'viewer': 'casaviewer',
             'info': None,
             'dbus': None,
             'ipcontroller': None,
             'ipengine': None
         },
        'dirs': {
             'rc': homedir + '/.casa',
             'data': None,
             'recipes': None,
             'root': None,
             'python': None,
             'pipeline': None,
             'xml': None
         },
         'flags': { },
         'files': {
             'logfile': os.getcwd( ) + '/casa-'+time.strftime("%Y%m%d-%H%M%S", time.gmtime())+'.log'
         },
         'state' : {
             'init_version': 0,
             'startup': True,
             'unwritable': set( )
         }
       }


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
## set up casa root
## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
if os.environ.has_key('CASAPATH') :
    __casapath__ = os.environ['CASAPATH'].split(' ')[0]
    __casaarch__ = os.environ['CASAPATH'].split(' ')[1]
    if not os.path.exists(__casapath__ + "/data") :
        print "DEBUG: CASAPATH = %s" % (__casapath__)
        raise RuntimeError, "Unable to find the data repository directory in your CASAPATH. Please fix."
    else :
        casa['dirs']['root'] = __casapath__
        casa['dirs']['data'] = __casapath__ + "/data"
        if os.path.exists(__casapath__ + "/" + __casaarch__ + "/lib/python2.7/assignmentFilter.py"):
            casa['dirs']['python'] = __casapath__ + "/" + __casaarch__ + "/lib/python2.7"
        elif os.path.exists(__casapath__ + "/lib/python2.7/assignmentFilter.py"):
            casa['dirs']['python'] = __casapath__ + "/lib/python2.7"
        elif os.path.exists(__casapath__ + "/Resources/python/assignmentFilter.py"):
            casa['dirs']['python'] = __casapath__ + "/Resources/python"

        if casa['dirs']['python'] is not None:
            casa['dirs']['recipes'] = casa['dirs']['python'] + "/recipes"

        if os.path.exists(__casapath__ + "/" + __casaarch__ + "/xml"):
            casa['dirs']['xml'] = __casapath__ + "/" + __casaarch__ + "/xml"
        elif os.path.exists(__casapath__ + "/xml"):
            casa['dirs']['xml'] = __casapath__ + "/xml"
        else:
            raise RuntimeError, "Unable to find the XML constraints directory in your CASAPATH"
else :
    __casapath__ = casac.__file__
    while __casapath__ and __casapath__ != "/" :
        if os.path.exists( __casapath__ + "/data") :
            break
        __casapath__ = os.path.dirname(__casapath__)
    if not os.path.exists(__casapath__ + "/data") :
        raise RuntimeError, "casa path could not be determined"
    else :
        casa['dirs']['root'] = __casapath__
        casa['dirs']['data'] = __casapath__ + "/data"
        if os.path.exists(__casapath__ + "/" + __casaarch__ + "/lib/python2.7/assignmentFilter.py"):
            casa['dirs']['python'] = __casapath__ + "/" + __casaarch__ + "/lib/python2.7"
        elif os.path.exists(__casapath__ + "/lib/python2.7/assignmentFilter.py"):
            casa['dirs']['python'] = __casapath__ + "/lib/python2.7"
        elif os.path.exists(__casapath__ + "/Resources/python/assignmentFilter.py"):
            casa['dirs']['python'] = __casapath__ + "/Resources/python"

        if casa['dirs']['python'] is not None:
            casa['dirs']['recipes'] = casa['dirs']['python'] + "/recipes"

        if os.path.exists(__casapath__ + "/" + __casaarch__ + "/xml"):
            casa['dirs']['xml'] = __casapath__ + "/" + __casaarch__ + "/xml"
        elif os.path.exists(__casapath__ + "/xml"):
            casa['dirs']['xml'] = __casapath__ + "/xml"
        else:
            raise RuntimeError, "Unable to find the XML constraints directory in your CASAPATH"


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
## setup pipeline path (if it exists)
## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
if os.path.exists(casa['dirs']['root']+"/pipeline"):
    casa['dirs']['pipeline'] = casa['dirs']['root']+"/pipeline"


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
## setup helper paths...
## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
##
## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
## try to set casapyinfo path...
## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
if os.path.exists( __casapath__ + "/bin/casapyinfo") :
    casa['helpers']['info'] = __casapath__ + "/bin/casa-config"

## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
##     first try to find executables using casapyinfo...
##            (since system area versions may be incompatible)...
##     next try likely system areas...
## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
##
##   note:  hosts which have dbus-daemon-1 but not dbus-daemon seem to have a broken dbus-daemon-1...
##
for info in [ (['dbus-daemon'],'dbus'),
              (['CrashReportPoster'],'crashPoster'),
              (['ipcontroller','ipcontroller-2.6'], 'ipcontroller'),
              (['ipengine','ipengine-2.6'], 'ipengine') ]:
    exelist = info[0]
    entry = info[1]
    for exe in exelist:
        if casa['helpers']['info']:
            casa['helpers'][entry] = (lambda fd: fd.readline().strip('\n'))(os.popen(casa['helpers']['info'] + " --exec 'which " + exe + "'"))
        if casa['helpers'][entry] and os.path.exists(casa['helpers'][entry]):
            break
        else:
            casa['helpers'][entry] = None

        ### first look in known locations relative to top (of binary distros) or known casa developer areas
        for srchdir in [ __casapath__ + '/MacOS', __casapath__ + '/lib/casa/bin', '/usr/lib64/casa/01/bin', '/opt/casa/01/bin' ] :
            dd = srchdir + os.sep + exe
            if os.path.exists(dd) and os.access(dd,os.X_OK) :
                casa['helpers'][entry] = dd
                break
        if casa['helpers'][entry] is not None:
            break

    ## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
    ##     next search through $PATH for executables
    ## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
    if casa['helpers'][entry] is None:
        for exe in exelist:
            for srchdir in os.getenv('PATH').split(':') :
                dd = srchdir + os.sep + exe
                if os.path.exists(dd) and os.access(dd,os.X_OK) :
                    casa['helpers'][entry] = dd
                    break
            if casa['helpers'][entry] is not None:
                break

print "CASA Version " + casa['build']['version'] + "-REL (r" + casa['source']['revision'] + ")\n  Compiled on: " + casa['build']['time']

a = [] + sys.argv             ## get a copy from goofy python
a.reverse( )
##
## A session configuration 'casa.conf' now included in casa tree...
##
dbus_conf = __casapath__ + "/etc/dbus/casa.conf"
if not os.path.exists(dbus_conf):
    dbus_conf = __casapath__ + "/Resources/dbus/casa.conf"

__ipython_colors = 'LightBG'
while len(a) > 0:
    c = a.pop()
    if c == '--colors':
        ##
        ## strip out 2 element ipython flags (which we recognize) here...
        ##
        if len(a) == 0 :
            print "A option must be specified with " + c + "..."
            sys.exit(1)
        else:
            c = a.pop( )
            if c != 'NoColor' and c != 'Linux' and c != 'LightBG':
                print "unrecognized option for '--color': " + c
                sys.exit(1)
            else:
                __ipython_colors = c

    elif c.startswith('--colors='):
        ##
        ## strip out single element ipython flags (which we recognize) here...
        ##
        c = c.split('=')[1]
        if c != 'NoColor' and c != 'Linux' and c != 'LightBG':
            print "unrecognized option for '--color': " + c
            sys.exit(1)
        else:
            __ipython_colors = c
        
    elif c == '--logfile' or c == '-c' or c == '--rcdir':
        ##
        ## we join multi-arg parameters here
        ##
        if len(a) == 0 :
            print "A file must be specified with " + c + "..."
            sys.exit(1)
        else :
            casa['flags'][c] = a.pop( )
            if c == '--rcdir':
                casa['dirs']['rc'] = casa['flags'][c]

    elif c.find('=') > 0 :
        casa['flags'][c[0:c.find('=')]] = c[c.find('=')+1:]

    else :
        casa['flags'][c] = ''

if casa['flags'].has_key('--logfile') :
    casa['files']['logfile'] = casa['flags']['--logfile']	## user specifies a log file
if casa['flags'].has_key('--nologfile') :
    casa['files'].pop('logfile')				## user indicates no log file

if casa['flags'].has_key('--help') :
	print "Options are: "
	print "   --rcdir directory"
	print "   --logfile logfilename"
	print "   --maclogger"
	print "   --log2term"
	print "   --nologger"
	print "   --nologfile"
	print "   --nogui"
        print "   --colors=[NoColor|Linux|LightBG]"
        print "   --pipeline"
	print "   -c filename-or-expression"
	print "   --help, print this text and exit"
	print
	sys.exit(0) 

if os.uname()[0]=='Darwin' :
    casa_path = os.environ['CASAPATH'].split()

    casa['helpers']['viewer'] = casa_path[0]+'/'+casa_path[1]+'/apps/casaviewer.app/Contents/MacOS/casaviewer'
    # In the distro of the app then the apps dir is not there and you find things in MacOS
    if not os.path.exists(casa['helpers']['viewer']) :
        casa['helpers']['viewer'] = casa_path[0]+'/MacOS/casaviewer'

    if casa['flags'].has_key('--maclogger') :
        casa['helpers']['logger'] = 'console'
    else:
        casa['helpers']['logger'] = casa_path[0]+'/'+casa_path[1]+'/apps/casalogger.app/Contents/MacOS/casalogger'

        # In the distro of the app then the apps dir is not there and you find things in MacOS
        if not os.path.exists(casa['helpers']['logger']) :
            casa['helpers']['logger'] = casa_path[0]+'/Resources/Logger.app/Contents/MacOS/casalogger'


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
## ensure default initialization occurs before this point...
##
##      prelude.py  =>  setup/modification of casa settings
##      init.py     =>  user setup (with task access)
##
## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
if os.path.exists( casa['dirs']['rc'] + '/prelude.py' ) :
    try:
        execfile ( casa['dirs']['rc'] + '/prelude.py' )
    except:
        print str(sys.exc_info()[0]) + ": " + str(sys.exc_info()[1])
        print 'Could not execute initialization file: ' + casa['dirs']['rc'] + '/prelude.py'
        sys.exit(1)

## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
## on linux set up a dbus-daemon for casa because each
## x-server (e.g. Xvfb) gets its own dbus session...
## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
if casa['helpers']['dbus'] is not None :

    argv_0_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    dbus_path = os.path.dirname(os.path.abspath(casa['helpers']['dbus']))

    (r,w) = os.pipe( )

    if os.fork( ) == 0 :
        os.close(r)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
        ## close standard input to avoid terminal interrupts
        sys.stdin.close( )
        os.close(0)
        args = [ 'casa-dbus-daemon' ]
        args = args + ['--print-address', str(w)]
        if dbus_conf is not None and os.path.exists(dbus_conf) :
            args = args + ['--config-file',dbus_conf]
        else:
            args = args + ['--session']
        os.execvp(casa['helpers']['dbus'],args)
        sys.exit
        
    os.close(w)
    dbus_address = os.read(r,200)
    dbus_address = dbus_address.strip( )
    os.close(r)
    if len(dbus_address) > 0 :
        os.putenv('DBUS_SESSION_BUS_ADDRESS',dbus_address)
        os.environ['DBUS_SESSION_BUS_ADDRESS'] = dbus_address


ipythonenv  = casa['dirs']['rc'] + '/ipython'
ipythonpath = casa['dirs']['rc'] + '/ipython'
try :
   os.makedirs(ipythonpath, 0755)
except :
   pass
###check IPYTHONDIR is defined by user and make it if not there
if(not os.environ.has_key('IPYTHONDIR')):
    os.environ['IPYTHONDIR']=ipythonpath
if(not os.path.exists(os.environ['IPYTHONDIR'])):
    os.makedirs(os.environ['IPYTHONDIR'], 0755)

os.environ['__CASARCDIR__']=casa['dirs']['rc']

#import string

#
# Special case if the backend is set to MacOSX reset it to TkAgg as our TablePlot
# stuff is specific for TkAgg
#
if matplotlib.get_backend() == "MacOSX" :
   matplotlib.use('TkAgg')

#
# Check if the display environment is set if not
# switch the backend to Agg only if it's TkAgg
#
if not os.environ.has_key('DISPLAY') and matplotlib.get_backend() == "TkAgg" :
   matplotlib.use('Agg')
#
# If the user has requested pipeline through a command line option set
# to use AGG
if casa['flags'].has_key('--pipeline'):
    matplotlib.use('Agg')

#
# We put in all the task declarations here...
#
from taskinit import *

logpid=[]

def casalogger(logfile=''):
    """
    Spawn a new casalogger using logfile as the filename.
    You should only call this if the casalogger dies or you close it
    and restart it again.

    Note: if you changed the name of the log file using casalog.setlogfile
    you will need to respawn casalogger with the new log filename. Eventually,
    we will figure out how to signal the casalogger with the new name but not
    for a while.
    """

    if logfile == '':
        if casa.has_key('files') and casa['files'].has_key('logfile') :
            logfile = casa['files']['logfile']
        else:
            casa['files']['logfile'] = os.getcwd( ) + '/casa.log'
            logfile = 'casa.log'

    pid=9999
    if (os.uname()[0]=='Darwin'):
        if casa['helpers']['logger'] == 'console':
           os.system("open -a console " + logfile)
        else:
           # XCode7 writes debug messages to stderr, which then end up in the
           # Casa console. Hence the stderr is directed to devnull
           #pid=os.spawnvp(os.P_NOWAIT,casa['helpers']['logger'],[casa['helpers']['logger'], logfile])
           DEVNULL = open(os.devnull, 'w')
           pid = Popen([casa['helpers']['logger'],logfile], stderr=DEVNULL).pid
           #pid = Popen([casa['helpers']['logger'],logfile], stdin=PIPE, stdout=FNULL, stderr=STDOUT).pid

    elif (os.uname()[0]=='Linux'):
        pid=os.spawnlp(os.P_NOWAIT,casa['helpers']['logger'],casa['helpers']['logger'],logfile)
    else:
        print 'Unrecognized OS: No logger available'

    if (pid!=9999): logpid.append(pid)



showconsole = False

thelogfile = ''

showconsole = casa['flags'].has_key('--log2term')
print 'show_console =', showconsole
if casa['files'].has_key('logfile') :
    thelogfile = casa['files']['logfile']
if casa['flags'].has_key('--nologfile') :
    thelogfile = 'null'

deploylogger = True
if casa['flags'].has_key('--nolog') :
    print "--nolog is deprecated, please use --nologger"
    deploylogger = False

if not os.access('.', os.W_OK) :
    print 
    print "********************************************************************************"
    print "Warning: no write permission in current directory, no log files will be written."
    print "********************************************************************************"
    deploylogger = False
    thelogfile = 'null'
    
if casa['flags'].has_key('--nologger') :
    deploylogger = False

if casa['flags'].has_key('--nogui') :
    deploylogger = False

#print 'thelogfile:', thelogfile
if thelogfile == 'null':
    pass
else:
    if thelogfile.strip() != '' :
        if deploylogger:
            casalogger(thelogfile)
    else:
        thelogfile = 'casapy-'+time.strftime("%Y%m%d-%H%M%S", time.gmtime())+'.log'
        try:
            open(thelogfile, 'a').close()
        except:
            pass
        if deploylogger:
            casalogger(thelogfile)


###################
#setup file catalog
###################

vwrpid=9999
####################
# Task Interface


from parameter_check import *
####################
def go(taskname=None):
    """ Execute taskname: """
    myf = sys._getframe(len(inspect.stack())-1).f_globals
    if taskname==None: taskname=myf['taskname']
    oldtaskname=taskname
    if(myf.has_key('taskname')):
        oldtaskname=myf['taskname']
    #myf['taskname']=taskname
    if type(taskname)!=str:
        taskname=taskname.__name__
        myf['taskname']=taskname
    try:
        parameter_checktype(['taskname'],[taskname],str)
    except TypeError, e:
        print "go -- TypeError: ",e
        return
    fulltaskname=taskname+'()'
    print 'Executing: ',fulltaskname
    exec(fulltaskname)
    myf['taskname']=oldtaskname

def selectfield(vis,minstring):
    """Derive the fieldid from  minimum matched string(s): """

    tb.open(vis+'/FIELD')
    fields=list(tb.getcol('NAME'))#get fieldname list
    tb.close()          #close table
    indexlist=list()    #initialize list
    stringlist=list()

    fldlist=minstring.split()#split string into elements
    print 'fldlist is ',fldlist
    for fld in fldlist:     #loop over fields
        _iter=fields.__iter__() #create iterator for fieldnames
        while 1:
            try:
                x=_iter.next() # has first value of field name
            except StopIteration:
                break
            #
            if (x.find(fld)!=-1): 
                indexlist.append(fields.index(x))
                stringlist.append(x)

    print 'Selected fields are: ',stringlist
    return indexlist

def selectantenna(vis,minstring):
    """Derive the antennaid from matched string(s): """

    tb.open(vis+'/ANTENNA')
    ants=list(tb.getcol('NAME'))#get fieldname list
    tb.close()          #close table
    indexlist=list()    #initialize list
    stringlist=list()

    antlist=minstring.split()#split string into elements
    for ant in antlist:     #loop over fields
        try:
            ind=ants.index(ant)
            indexlist.append(ind)
            stringlist.append(ant)
        except ValueError:
            pass

    print 'Selected reference antenna: ',stringlist
    print 'indexlist: ',indexlist
    return indexlist[0]

def readboxfile(boxfile):
    """ Read a file containing clean boxes (compliant with AIPS BOXFILE)

    Format is:
    #FIELDID BLC-X BLC-Y TRC-X TRC-Y
    0       110   110   150   150 
    or
    0       hh:mm:ss.s dd.mm.ss.s hh:mm:ss.s dd.mm.ss.s

    Note all lines beginning with '#' are ignored.

    """
    union=[]
    f=open(boxfile)
    while 1:
        try: 
            line=f.readline()
            if (line.find('#')!=0): 
                splitline=line.split('\n')
                splitline2=splitline[0].split()
                if (len(splitline2[1])<6): 
                    boxlist=[int(splitline2[1]),int(splitline2[2]),
                    int(splitline2[3]),int(splitline2[4])]
                else:
                    boxlist=[splitline2[1],splitline2[2],splitline2[3],
                    splitline2[4]]
    
                union.append(boxlist)
    
        except:
            break

    f.close()
    print 'union is: ',union
    return union


def inp(taskname=None, page=False):
    """
    Function to browse input parameters of a given task
    taskname: name of task of interest
    page: use paging if True, useful if list of parameters is longer than terminal height
    """
    try:
        ####paging contributed by user Ramiro Hernandez
        if(page):
            #########################
            class TemporaryRedirect(object):
                def __init__(self, stdout=None, stderr=None):
                    self._stdout = stdout or sys.stdout
                    self._stderr = stderr or sys.stderr
                def __enter__(self):
                    self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
                    self.old_stdout.flush(); self.old_stderr.flush()
                    sys.stdout, sys.stderr = self._stdout, self._stderr
                def __exit__(self, exc_type, exc_value, traceback):
                    self._stdout.flush(); self._stderr.flush()
                    sys.stdout = self.old_stdout
                    sys.stderr = self.old_stderr
            #######################end class
            tempfile="__temp_input.casa"
            temporal = open(tempfile, 'w')    

            with TemporaryRedirect(stdout=temporal):
                inp(taskname, False)
            temporal.close()
            os.system('more '+tempfile)
            os.system('rm '+tempfile)
            return
        ####
        myf=sys._getframe(len(inspect.stack())-1).f_globals
        if((taskname==None) and (not myf.has_key('taskname'))):
            print 'No task name defined for inputs display'
            return
        if taskname==None: taskname=myf['taskname']
        myf['taskname']=taskname
        if type(taskname)!=str:
            taskname=taskname.__name__
            myf['taskname']=taskname

        try:
            parameter_checktype(['taskname'],taskname,str)
        except TypeError, e:
            print "inp -- TypeError: ", e
            return
        except ValueError, e:
            print "inp -- OptionError: ", e
            return

        ###Check if task exists by checking if task_defaults is defined
        if ( not myf.has_key(taskname) and
             str(type(myf[taskname])) != "<type 'instance'>" and
             not hasattr(myf[taskname],"defaults") ):
            raise TypeError, "task %s is not defined " %taskname
        if(myf.has_key('__last_taskname')):
            myf['__last_taskname']=taskname
        else:
            myf.update({'__last_taskname':taskname})

        print '# ',myf['taskname']+' :: '+(eval(myf['taskname']+'.description()'))
        update_params(myf['taskname'], myf)
    except TypeError, e:
        print "inp --error: ", e
    except Exception, e:
        print "---",e

def update_params(func, printtext=True, ipython_globals=None):
    from odict import odict

    if ipython_globals == None:
        myf=sys._getframe(len(inspect.stack())-1).f_globals
    else:
        myf=ipython_globals

    ### set task to the one being called
    myf['taskname']=func
    obj=myf[func]

    if ( str(type(obj)) == "<type 'instance'>" and
         hasattr(obj,"check_params") ):
        hascheck = True
    else:
        hascheck = False

    noerror=True
    ###check if task has defined a task_check_params function

    if (hascheck):
	has_othertasks = myf.has_key('task_location')
	if(has_othertasks) :
	   has_task = myf['task_location'].has_key(myf['taskname'])
	   if (has_task) :
		pathname=myf['task_location'][myf['taskname']]
	   else :
	        pathname = os.environ.get('CASAPATH').split()[0]+'/'+os.environ.get('CASAPATH').split()[1]+'/xml'
                if not os.path.exists(pathname) :
                    pathname = os.environ.get('CASAPATH').split()[0]+'/xml'
                    if not os.path.exists(pathname) :
                        pathname = os.environ.get('CASAPATH').split()[0]+'/Resources/xml'
                
	else :
	   pathname = os.environ.get('CASAPATH').split()[0]+'/'+os.environ.get('CASAPATH').split()[1]+'/xml'
           if not os.path.exists(pathname) :
               pathname = os.environ.get('CASAPATH').split()[0]+'/xml'
               if not os.path.exists(pathname) :
                   pathname = os.environ.get('CASAPATH').split()[0]+'/Resources/xml'
                   if not os.path.exists(pathname) :
                       sys.exit("ERROR: casapy.py update_params() can not locate xml file for task %s" % (taskname))
                       
        xmlfile=pathname+'/'+myf['taskname']+'.xml'
        if(os.path.exists(xmlfile)) :
            cu.setconstraints('file://'+xmlfile);
        else:
            #
            # SRankin: quick fix for CAS-5381 - needs review.
            # The task is not a CASA internal task.  Extract the path from task_location.
            # This may not be robust.  I have not tracked down all the code that could update task_location.
            task_path=task_location[taskname]
            xmlfile=task_path+'/'+myf['taskname']+'.xml'
            if(os.path.exists(xmlfile)) :
                cu.setconstraints('file://'+xmlfile);

    a=myf[myf['taskname']].defaults("paramkeys",myf)
    itsdef=myf[myf['taskname']].defaults
    itsparams=myf[myf['taskname']].parameters
    params=a
    #print 'itsparams:', itsparams
    for k in range(len(params)):
        paramval = obj.defaults(params[k], myf)

        notdict=True
        ###if a dictionary with key 0, 1 etc then need to peel-open
        ###parameters
        if(type(paramval)==dict):
            if(paramval.has_key(0)):
                notdict=False
        if(myf.has_key(params[k])):
            itsparams.update({params[k]:myf[params[k]]})
        else:
            itsparams.update({params[k]:obj.itsdefault(params[k])})
        if (notdict ):
            if(not myf.has_key(params[k])):
                myf.update({params[k]:paramval})
                itsparams.update({params[k]:paramval})
            if(printtext):
                #print 'params:', params[k], '; myf[params]:', myf[params[k]]
                if(hascheck):
                    noerror = obj.check_params(params[k],myf[params[k]],myf)
                # RI this doesn't work with numpy arrays anymore.  Noone seems
                # interested, so I'll be the red hen and try to fix it.
                
                #print 'params:', params[k], '; noerror:', noerror, '; myf[params]:', myf[params[k]]
                myfparamsk=myf[params[k]]
                if(type(myf[params[k]])==pl.ndarray):
                    myfparamsk=myfparamsk.tolist()
                #if(myf[params[k]]==paramval):
                if(myfparamsk==paramval):
                    print_params_col(params[k],myf[params[k]],obj.description(params[k]), 'ndpdef', 'black',noerror)
                else:
                    print_params_col(params[k],myf[params[k]],obj.description(params[k]), 'ndpnondef', 'black', noerror)
		itsparams[params[k]] = myf[params[k]]
        else:
            subdict=odict(paramval)
            ##printtext is False....called most probably to set
            ##undefined params..no harm in doing it anyways
            if(not printtext):
                ##locate which dictionary is user selected
                userdict={}
                subkeyupdated={}
                for somekey in paramval:
                    somedict=dict(paramval[somekey])
                    subkeyupdated.update(dict.fromkeys(somedict, False))
                    if(somedict.has_key('value') and myf.has_key(params[k])):
                        if(somedict['value']==myf[params[k]]):
                            userdict=somedict
                    elif(somedict.has_key('notvalue') and myf.has_key(params[k])):
                        if(somedict['notvalue']!=myf[params[k]]):
                            userdict=somedict
                ###The behaviour is to use the task.defaults
                ### for all non set parameters and parameters that
                ### have no meaning for this selection
                for j in range(len(subdict)):
                    subkey=subdict[j].keys()
                   
                    for kk in range(len(subkey)):
                        
                        if( (subkey[kk] != 'value') & (subkey[kk] != 'notvalue') ):
                            #if user selecteddict
                            #does not have the key
                            ##put default
                            if(userdict.has_key(subkey[kk])):
                                if(myf.has_key(subkey[kk])):
                                    itsparams.update({subkey[kk]:myf[subkey[kk]]})
                                else:
                                    itsparams.update({subkey[kk]:userdict[subkey[kk]]})
                                subkeyupdated[subkey[kk]]=True
                            elif((not subkeyupdated[subkey[kk]])):
                                itsparams.update({subkey[kk]:itsdef(params[k], None, itsparams[params[k]], subkey[kk])})
                                subkeyupdated[subkey[kk]]=True
            ### need to do default when user has not set val
            if(not myf.has_key(params[k])):
                if(paramval[0].has_key('notvalue')):
                    itsparams.update({params[k]:paramval[0]['notvalue']})
                    myf.update({params[k]:paramval[0]['notvalue']})
                else:
                    itsparams.update({params[k]:paramval[0]['value']})
                    myf.update({params[k]:paramval[0]['value']})
            userval=myf[params[k]]
            choice=0
            notchoice=-1
            valuekey='value'
            for j in range(len(subdict)):
                if(subdict[j].has_key('notvalue')):
                    valuekey='notvalue'
                    if(subdict[j]['notvalue'] != userval):
                        notchoice=j;
                        break
                else:
                    if(subdict[j]['value']==userval):
                        choice=j
                        notchoice=j
                        break
            subkey=subdict[choice].keys()
            if(hascheck):
                noerror=obj.check_params(params[k],userval,myf)
            if(printtext):
                if(myf[params[k]]==paramval[0][valuekey]):
                    print_params_col(params[k],myf[params[k]],obj.description(params[k]),'dpdef','black', noerror)
                else:
                    print_params_col(params[k],myf[params[k]],obj.description(params[k]),'dpnondef','black', noerror)
		itsparams[params[k]] = myf[params[k]]
            for j in range(len(subkey)):
                if((subkey[j] != valuekey) & (notchoice > -1)):
                    ###put default if not there
                    if(not myf.has_key(subkey[j])):
                        myf.update({subkey[j]:subdict[choice][subkey[j]]})
                    paramval=subdict[choice][subkey[j]]
                    if (j==(len(subkey)-1)):
                        # last subparameter - need to add an extra line to allow cut/pasting
                        comment='last'
                    else:
                        comment='blue'
                    if(hascheck):
                        noerror = obj.check_params(subkey[j],myf[subkey[j]],myf)
                    if(printtext):
                        if(myf[subkey[j]]==paramval):
                            print_params_col(subkey[j],myf[subkey[j]],obj.description(subkey[j],userval),'spdef',comment, noerror)
                        else:
                            print_params_col(subkey[j],myf[subkey[j]],obj.description(subkey[j],userval),'spnondef',comment, noerror)
		        itsparams[params[k]] = myf[params[k]]                    
    #
    # Verify the complete record, with errors being reported to the user
    #
    #cu.verify(itsparams, cu.torecord('file://'+xmlfile)[myf['taskname']]);

####function to print inputs with coloring
####colorparam 'blue'=> non-default, colorcomment 'green'=> can have sub params
#### 'blue' => is a sub-parameter 
# blue = \x1B[94m
# bold = \x1B[1m
# red  = \x1B[91m
# cyan = \x1B[96m
# green= \x1B[92m
# normal   = \x1B[0m
# underline= \x1B[04m
# reverse = \x1B[7m
# highlight with black = \x1B[40s

def print_params_col(param=None, value=None, comment='', colorparam=None,
                     colorcomment=None, noerrorval=True):
    try:
        from TerminalController import TerminalController
        term = TerminalController()
        cols = term.COLS
        del term
    except:
        cols = 80
    #
    #print 'colorparam is: ', colorparam
    #
    if type(value) == str:
        printval = "'" + value + "'"
    else:
        printval = value

    if colorparam == 'ndpnondef':
        firstcol = '\x1B[0m'
        valcol   = '\x1B[94m'
    elif colorparam == 'dpdef':
        firstcol = '\x1B[1m' + '\x1B[47m'
        valcol   = '\x1B[1m' + '\x1B[0m'
    elif colorparam == 'dpnondef':
        firstcol = '\x1B[1m' + '\x1B[47m'
        valcol   = '\x1B[1m' + '\x1B[94m'
    elif colorparam == 'spdef':
        firstcol = '\x1B[32m'
        valcol   = '\x1B[0m'
    elif colorparam == 'spnondef':
        firstcol = '\x1B[32m'
        valcol   = '\x1B[94m'
    else:
        firstcol = '\x1B[0m'
        valcol   = '\x1B[0m'

    if not noerrorval:
        valcol = '\x1B[1m' + '\x1B[91m'

    if colorcomment == 'green':
        secondcol = '\x1B[102m'
    elif colorcomment == 'blue':
        #secondcol='\x1B[104m'
        secondcol = '\x1B[0m'
    else:
        secondcol = '\x1B[0m'

    # RR: I think colorcomment should really be called submenu.
    #     Since these are left justified, I've absorbed the right space into
    #     the %s's, in order to handle as long a parameter name as possible.
    #     (The uvfilterb* params were busting out of %-10s.)
    if colorcomment in ('last', 'blue'):
        parampart = firstcol + '     %-14s ='
    else:
        parampart = firstcol + '%-19s ='
    parampart %= param

    valpart = valcol + ' %10s \x1B[0m' % printval + secondcol
    # Well behaved (short) parameters and values tally up to 33 characters
    # so far.  Pad them up to 40, assuming the param is short enough.
    pad = 7
    paramlen = len(str(param))
    if colorcomment in ('last', 'blue') and paramlen > 14:
        pad -= paramlen - 14
    elif paramlen > 19:
        pad -= paramlen - 19
    valuelen = len(str(printval))
    if valuelen > 10:
        pad -= valuelen - 10
    if pad > 0:
        valpart += ' ' * pad

    try:
        from textwrap import fill
        if pad < 0:
            firstskip = 40 - pad
            firstfiller = ' ' * firstskip + '#  '
            afterfiller = ' ' * 40 + '#   '
        else:
            firstskip = 40
            firstfiller = ' ' * 40 + '#  '
            afterfiller = firstfiller + ' '
        commentpart = fill(comment, cols, initial_indent=firstfiller,
                           subsequent_indent=afterfiller)[firstskip:]
    except:
        if comment:
            commentpart = '#  ' + comment
        else:
            commentpart = ''
    commentpart += '\x1B[0m'          # RR: I think this might be redundant.
    if colorcomment == 'last':        #     (Is colorcomment ever green?)
        commentpart += "\n"

    print parampart + valpart + commentpart

def __set_default_parameters(b):
    myf=sys._getframe(len(inspect.stack())-1).f_globals
    a=b
    elkey=a.keys()
    for k in range(len(a)):
        if (type(a[elkey[k]]) != dict):
            myf[elkey[k]]=a[elkey[k]]
        elif (type(a[elkey[k]]) == dict and len(a[elkey[k]])==0):
            myf[elkey[k]]=a[elkey[k]]
        else:
            subdict=a[elkey[k]]
            ##clear out variables of other options if they exist
            for j in range(1,len(subdict)):
                subkey=subdict[j].keys()
                for kk in range(len(subkey)):
                    if((subkey[kk] != 'value') & (subkey[kk] != 'notvalue') ):
                        if(myf.has_key(subkey[kk])):
                            del myf[subkey[kk]]
            ###
            if(subdict[0].has_key('notvalue')):
                myf[elkey[k]]=subdict[0]['notvalue']
            else:
                myf[elkey[k]]=subdict[0]['value']
            subkey=subdict[0].keys()
            for j in range(0, len(subkey)):
                if((subkey[j] != 'value') & (subkey[j] != 'notvalue')):
                    myf[subkey[j]]=subdict[0][subkey[j]]

def backupoldfile(thefile=''):
    import copy
    import shutil
    if(thefile=='' or (not os.path.exists(thefile))):
        return 
    outpathdir = os.path.realpath(os.path.dirname(thefile))
    outpathfile = outpathdir + os.path.sep + os.path.basename(thefile)
    k=0
    backupfile=outpathfile+'.'+str(k)
    prevfile='--------'
    while (os.path.exists(backupfile)):
        k=k+1
        prevfile=copy.copy(backupfile)
        if(os.path.exists(prevfile)  and filecmp.cmp(outpathfile, prevfile)):
        ##avoid making multiple copies of the same file
            return
        backupfile=outpathfile+'.'+str(k)
    shutil.copy2(outpathfile, backupfile)

def tput(taskname=None, outfile=''):
	myf = sys._getframe(len(inspect.stack())-1).f_globals
	if taskname == None: taskname = myf['taskname']
	if type(taskname) != str:
		taskname=taskname.__name__
	myf['taskname'] = taskname
	outfile = myf['taskname']+'.last'
	saveinputs(taskname, outfile)

def saveinputs(taskname=None, outfile='', myparams=None, ipython_globals=None, scriptstr=['']):
    #parameter_printvalues(arg_names,arg_values,arg_types)
    """ Save current input values to file on disk for a specified task:

    taskname -- Name of task
        default: <unset>; example: taskname='bandpass'
        <Options: type tasklist() for the complete list>
    outfile -- Output file for the task inputs
        default: taskname.saved; example: outfile=taskname.orion

    """

    try:
        if ipython_globals == None:
	    myf = sys._getframe(len(inspect.stack())-1).f_globals
        else:
            myf=ipython_globals

        if taskname==None: taskname=myf['taskname']
        myf['taskname']=taskname
        if type(taskname)!=str:
            taskname=taskname.__name__
            myf['taskname']=taskname

        parameter_checktype(['taskname','outfile'],[taskname,outfile],[str,str])

        ###Check if task exists by checking if task_defaults is defined
        obj = False
        if ( not myf.has_key(taskname) and
             str(type(myf[taskname])) != "<type 'instance'>" and
             not hasattr(myf[taskname],"defaults") ):
            raise TypeError, "task %s is not defined " %taskname
        else:
            obj = myf[taskname]

        if taskname==None: taskname=myf['taskname']
        myf['taskname']=taskname
        if outfile=='': outfile=taskname+'.saved'
        if(myf.has_key('__multibackup') and myf['__multibackup']):
            backupoldfile(outfile)
        
        ##make sure unfolded parameters get their default values
        myf['update_params'](func=myf['taskname'], printtext=False, ipython_globals=myf)
        ###
        do_save_inputs = False
        outpathdir = os.path.realpath(os.path.dirname(outfile))
        outpathfile = outpathdir + os.path.sep + os.path.basename(outfile)
        if outpathfile not in casa['state']['unwritable'] and outpathdir not in casa['state']['unwritable']:
            try:
                taskparameterfile=open(outfile,'w')
                print >>taskparameterfile, '%-15s    = "%s"'%('taskname', taskname)
                do_save_inputs = True
            except:
                print "********************************************************************************"
                print "Warning: no write permission for %s, cannot save task" % outfile
                if os.path.isfile(outfile):
                    print "         inputs in %s..." % outpathfile
                    casa['state']['unwritable'].add(outpathfile)
                elif not os.path.isdir(outfile):
                    print "         inputs in dir %s..." % outpathdir
                    casa['state']['unwritable'].add(outpathdir)
                else:
                    print "         inputs because given file (%s) is a dir..." % outpathfile
                print "********************************************************************************"
        f=zip(myf[taskname].__call__.func_code.co_varnames[1:],myf[taskname].__call__.func_defaults)
        scriptstring='#'+str(taskname)+'('
	if myparams == None :
		myparams = {}
        l=0
        for j in range(len(f)):
            k=f[j][0]
	    if not myparams.has_key(k) and k != 'self' :
		    myparams[k] = myf[taskname].parameters[k]
            if(k != 'self' and type(myparams[k])==str):
                if ( myparams[k].count( '"' ) < 1 ):
                    # if the string doesn't contain double quotes then
                    # use double quotes around it in the parameter file.
                    if do_save_inputs:
                        print >>taskparameterfile, '%-15s    =  "%s"'%(k, myparams[k])
                    scriptstring=scriptstring+k+'="'+myparams[k]+'",'
                else:
                    # use single quotes.
                    if do_save_inputs:
                        print >>taskparameterfile, "%-15s    =  '%s'"%(k, myparams[k])
                    scriptstring=scriptstring+k+"='"+myparams[k]+"',"
            else :
                if ( j != 0 or k != "self" or
                     str(type(myf[taskname])) != "<type 'instance'>" ) :
                    if do_save_inputs:
                        print >>taskparameterfile, '%-15s    =  %s'%(k, myparams[k])
                    scriptstring=scriptstring+k+'='+str(myparams[k])+','

            ###Now delete varianle from global user space because
            ###the following applies: "It would be nice if one
            ### could tell the system to NOT recall
            ### previous non-default settings sometimes."
            if(not myf['casaglobals'] and myf.has_key(k)):
                del myf[k]
            l=l+1
            if l%5==0:
                scriptstring=scriptstring+'\n        '
        scriptstring=scriptstring.rstrip()
        scriptstring=scriptstring.rstrip('\n')
        scriptstring=scriptstring.rstrip(',')
        scriptstring=scriptstring+')'        
        scriptstr.append(scriptstring)
        scriptstring=scriptstring.replace('        ', '')
        scriptstring=scriptstring.replace('\n', '')
        if do_save_inputs:
            print >>taskparameterfile,scriptstring
            taskparameterfile.close()
    except TypeError, e:
        print "saveinputs --error: ", e
def default(taskname=None):
    """ reset given task to its default values :

    taskname -- Name of task


    """

    try:
	myf = sys._getframe(len(inspect.stack())-1).f_globals
        if taskname==None: taskname=myf['taskname']
        myf['taskname']=taskname
        if type(taskname)!=str:
            taskname=taskname.__name__
            myf['taskname']=taskname

        ###Check if task exists by checking if task_defaults is defined
        if ( not myf.has_key(taskname) and
             str(type(myf[taskname])) != "<type 'instance'>" and
             not hasattr(myf[taskname],"defaults") ):
            raise TypeError, "task %s is not defined " %taskname
        eval(myf['taskname']+'.defaults()')

        casalog.origin('default')
        taskstring=str(taskname).split()[0]
        casalog.post(' #######  Setting values to default for task: '+taskstring+'  #######')


    except TypeError, e:
        print "default --error: ", e

def taskparamgui(useGlobals=True):
    """
        Show a parameter-setting GUI for all available tasks.
    """
    import paramgui

    if useGlobals:
        paramgui.setGlobals(sys._getframe(len(inspect.stack())-1).f_globals)
    else:
        paramgui.setGlobals({})

    paramgui.runAll(_ip)
    paramgui.setGlobals({})

####################

def exit():
    __IPYTHON__.exit_now=True
    #print 'Use CNTRL-D to exit'
    #return


####################
def pybot_install( ):
    import tempfile
    import subprocess
    import shutil
    archdir = casa['dirs']['arch']
    pybot_url = "https://svn.cv.nrao.edu/svn/casa/development_tools/testing/pybot"
    tmp = tempfile.mkdtemp( )

    checkout = subprocess.Popen( "svn co %s ." % pybot_url, \
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=tmp )
    (output, err) = checkout.communicate()
    if len(err) > 0:
        print "OUTPUT: ", output
        print "ERROR:  ", err

    install = subprocess.Popen( "python setup.py install --install-lib=%s/python2.7 --install-scripts=%s/bin" % (archdir,archdir), \
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=tmp )
    (output, err) = install.communicate()
    if len(err) > 0:
        print "OUTPUT: ", output
        print "ERROR:  ", err

    shutil.rmtree(tmp)

def pybot_setup( ):
    import subprocess
    regression_url = "https://svn.cv.nrao.edu/svn/casa/development_tools/testing/pybot-regression"
    checkout = subprocess.Popen( "svn co %s casa" % regression_url, \
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True )
    (output, err) = checkout.communicate()
    if len(err) > 0:
        print "OUTPUT: ", output
        print "ERROR:  ", err
####################

    
import pylab as pl

#
# 
import platform
##
## CAS-951: matplotlib unresponsive on some 64bit systems
##

if (platform.architecture()[0]=='64bit'):
    if os.environ.has_key('DISPLAY') and os.environ['DISPLAY']!="" and not casa['flags'].has_key('--nogui'):
        pl.ioff( )
        pl.clf( )
        pl.ion( )
##
##

# Provide flexibility for boolean representation in the CASA shell
true  = True
T     = True
false = False
F     = False

# Case where casapy is run non-interactively
try:
   import IPython
except ImportError, e:
   print 'Failed to load IPython: ', e
   exit(1)


# setup available tasks
#
from math import *
from tasks_wrapped import *
from parameter_dictionary import *
from task_help import *

#
# import testing environment
#
import publish_summary
import runUnitTest
import runRegressionTest
#
home=os.environ['HOME']

#
# If the pipeline is there and the user requested it, load the pipeline tasks
#
if casa['flags'].has_key('--pipeline'):
    if casa['dirs']['pipeline'] is not None:
        sys.path.insert(0,casa['dirs']['pipeline'])
        import pipeline
        pipeline.initcli()
    else:
        print "Unable to locate pipeline installation, exiting"
        sys.exit(1)

## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
##
##      prelude.py  =>  setup/modification of casa settings (above)
##      init.py     =>  user setup (with task access)
##
## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
if os.path.exists( casa['dirs']['rc'] + '/init.py' ) :
    try:
        execfile ( casa['dirs']['rc'] + '/init.py' )
    except:
        print str(sys.exc_info()[0]) + ": " + str(sys.exc_info()[1])
        print 'Could not execute initialization file: ' + casa['dirs']['rc'] + '/init.py'
        sys.exit(1)

startup()

# assignment protection
#
#pathname=os.environ.get('CASAPATH').split()[0]
#uname=os.uname()
#unameminusa=str.lower(uname[0])
fullpath = casa['dirs']['python'] + '/assignmentFilter.py'
casalog.origin('casa')

#
# Use something else than python's builtin help() for
# documenting casapy tasks
#
import pydoc

class casaDocHelper(pydoc.Helper):
    def help(self, request):
        if hasattr(request, 'i_am_a_casapy_task'):
            pydoc.pager('Help on ' + pydoc.text.bold(request.__name__) + ' task:\n\n' + request.__doc__)
        else:
            return pydoc.Helper.help(self, request)

pydoc.help = casaDocHelper(sys.stdin, sys.stdout)

fullpath=casa['dirs']['python'] + '/assignmentFilter.py'

if os.environ.has_key('__CASAPY_PYTHONDIR'):
    fullpath=os.environ['__CASAPY_PYTHONDIR'] + '/assignmentFilter.py'

ipythonlog = 'ipython-'+time.strftime("%Y%m%d-%H%M%S", time.gmtime())+'.log'
#if os.path.exists('ipython.log') and not os.access('ipython.log', os.W_OK):
#    print
#    print
#    print
#    print "**********************************************************"
#    print "Error: ipython.log is not writable, unable to start casapy"
#    print "**********************************************************"
#    sys.exit(1) 

   
if casa['flags'].has_key('-c') :
    print 'will execute script',casa['flags']['-c']
    if os.path.exists( casa['dirs']['rc']+'/ipython/ipy_user_conf.py' ) :
        if os.path.exists( casa['flags']['-c'] ) :
            ###
            ###  assume casa['flags']['-c'] is a file to execute...
            ###
            try:
                ipshell = IPython.Shell.IPShell( argv=['-prompt_in1','CASA <\#>: ','-autocall','2','-colors',__ipython_colors, '-nomessages', '-nobanner','-logfile',ipythonlog,'-ipythondir',casa['dirs']['rc']+'/ipython','-c','execfile("'+casa['flags']['-c']+'")'], user_ns=globals() )
            except:
                print "ERROR: falied to create an instance of IPython.Shell.IPShell 1"
        else:
            ###
            ###  assume casa['flags']['-c'] is a python command...
            ###
            try:
                ipshell = IPython.Shell.IPShell( argv=['-prompt_in1','CASA <\#>: ','-autocall','2','-colors',__ipython_colors, '-nomessages', '-nobanner','-logfile',ipythonlog,'-ipythondir',casa['dirs']['rc']+'/ipython','-c',casa['flags']['-c']], user_ns=globals() )
            except: 
                print "ERROR: falied to create an instance of IPython.Shell.IPShell 2"
    else:
        if os.path.exists( casa['flags']['-c'] ) :
            ###
            ###  assume casa['flags']['-c'] is a file to execute...
            ###
            try:
                ipshell = IPython.Shell.IPShell( argv=['-prompt_in1','CASA <\#>: ','-autocall','2','-colors',__ipython_colors, '-nomessages', '-nobanner','-logfile',ipythonlog,'-upgrade','-ipythondir',casa['dirs']['rc']+'/ipython','-c','execfile("'+casa['flags']['-c']+'")'], user_ns=globals() )
            except: 
                print "ERROR: falied to create an instance of IPython.Shell.IPShell 3"
        else:
            ###
            ###  assume casa['flags']['-c'] is a python command...
            ###
            try:
                ipshell = IPython.Shell.IPShell( argv=['-prompt_in1','CASA <\#>: ','-autocall','2','-colors',__ipython_colors, '-nomessages', '-nobanner','-logfile',ipythonlog,'-upgrade','-ipythondir',casa['dirs']['rc']+'/ipython','-c',casa['flags']['-c']], user_ns=globals() )
            except: 
                print "ERROR: falied to create an instance of IPython.Shell.IPShell 4"
else:
    if os.path.exists( casa['dirs']['rc']+'/ipython/ipy_user_conf.py' ) :
        if(thelogfile != 'null') :
            try:
                ipshell = IPython.Shell.IPShell( argv=['-prompt_in1','CASA <\#>: ','-autocall','2','-colors',__ipython_colors, '-nomessages', '-nobanner','-logfile',ipythonlog,'-ipythondir',casa['dirs']['rc']+'/ipython'], user_ns=globals() )
            except: 
                print "ERROR: falied to create an instance of IPython.Shell.IPShell 5"
                ipshell = IPython.terminal.embed.InteractiveShellEmbed( argv=['-prompt_in1','CASA <\#>: ','-autocall','2','-colors',__ipython_colors, '-nomessages', '-nobanner','-logfile',ipythonlog,'-ipythondir',casa['dirs']['rc']+'/ipython'], user_ns=globals() )
        else :
            try:
                ipshell = IPython.Shell.IPShell( argv=['-prompt_in1','CASA <\#>: ','-autocall','2','-colors',__ipython_colors, '-nomessages', '-nobanner','-ipythondir',casa['dirs']['rc']+'/ipython'], user_ns=globals() )
            except: 
                print "ERROR: falied to create an instance of IPython.Shell.IPShell 6"
    else:
        if(thelogfile != 'null') :
            try:
                ipshell = IPython.Shell.IPShell( argv=['-prompt_in1','CASA <\#>: ','-autocall','2','-colors',__ipython_colors, '-nomessages', '-nobanner','-logfile',ipythonlog,'-upgrade','-ipythondir',casa['dirs']['rc']+'/ipython'], user_ns=globals() )
            except: 
                print "ERROR: falied to create an instance of IPython.Shell.IPShell 7"
        else :
            try:
                ipshell = IPython.Shell.IPShell( argv=['-prompt_in1','CASA <\#>: ','-autocall','2','-colors',__ipython_colors, '-nomessages', '-nobanner','-upgrade','-ipythondir',casa['dirs']['rc']+'/ipython'], user_ns=globals() )
            except: 
                print "ERROR: falied to create an instance of IPython.Shell.IPShell 8"
    #ipshell.IP.runlines('execfile("'+fullpath+'")')
    #print 'ipshell.runcode(\'execfile("'+fullpath+'")\')'
    #ipshell.ex('print(type(get_ipython()))')
    #ipshell.ex('execfile("'+fullpath+'")')
    #ipshell.ex('import assignmentFilter')
    #import __main__
    #import pdb
    #pdb.set_trace()
    #ipshell.safe_execfile(fullpath, {'global':__main__, 'local': __main__})

#ipshell = IPython.Shell.IPShell( argv=['-prompt_in1','CASA <\#>: ','-autocall','2','-colors',__ipython_colors,'-logfile',ipythonlog,'-ipythondir',casa['dirs']['rc']+'/ipython'], user_ns=globals() )

casalog.setlogfile(thelogfile)

try:
    casalog.post('---')
except:
    print "Error: the logfile is not writable"
    sys.exit(1)


casalog.showconsole(showconsole)
casalog.version()

## warn when available memory is < 512M (clean throws and exception)
if cu.hostinfo( )['memory']['available'] < 524288:
    casalog.post( 'available memory less than 512MB (with casarc settings)\n...some things will not run correctly', 'SEVERE' )
    
casa['state']['startup'] = False

#print '----thelogfile:', thelogfile
#print 'casa.log exists:', os.path.exists('casa.log')

if (thelogfile == 'null' or thelogfile != 'casa.log') and os.path.exists('casa.log'):
    try:
        os.remove('casa.log')
    except OSError:
        pass

# initialize/finalize Sakura library
if hasattr(casac,'sakura'):
    casalog.post('Managing Sakura lifecycle', priority='DEBUG')
    casac.sakura().initialize_sakura()
    import atexit
    atexit.register(lambda: __import__('casac').casac.sakura().cleanup_sakura())
    
import shutil

###
### append user's originial path...
###
if os.environ.has_key('_PYTHONPATH'):
    sys.path.extend(os.getenv('_PYTHONPATH').split(':'))

###
### Initialize the crash dump feature
###
#
#import signal
#import tempfile
#
#try:
#    temporaryDirectory = tempfile.gettempdir()
#    posterApp = casa['helpers']['crashPoster']
#    if posterApp is None: posterApp = "" # handle case where it wasn't found
#    postingUrl = "https://casa.nrao.edu/cgi-bin/crash-report.pl"
#    message = casac.utils()._crash_reporter_initialize(temporaryDirectory, posterApp, postingUrl)
#    if len (message) > 0:
#        print ("***\n*** Crash reporter failed to initialize: " + message)
#except Exception as e:
#    print "***\n*** Crash reporter initialization failed.\n***"
#    print "*** exception={0}\n***".format (e)

#ipshell.mainloop( )
#ipshell() # (AK)
#if(os.uname()[0] == 'Darwin') and type(casa) == "<type 'dict'>" and casa['flags'].has_key('--maclogger') :
#    os.system("osascript -e 'tell application \"Console\" to quit'")
#for pid in logpid: 
#    #print 'pid: ',pid
#    os.kill(pid,9)
#
#for x in os.listdir('.'):
#    if x.lower().startswith('casapy.scratch-'):
#        if os.path.isdir(x):
#            #shutil.rmtree(x, ignore_errors=True)
#            os.system("rm -rf %s" % x)
#            #print "Removed: ", x, "\n"
#
### leave killing off children to the watchdog...
### so everyone has a chance to die naturally...
#print "leaving casa..."
#def excepthook(exctype, value, tb):
#    print "-----------------------------------------------------------------------------"
#    print "error during shutdown"
#    print "-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --"
#    print exctype
#    print value
#    print "-----------------------------------------------------------------------------"
#
#sys.excepthook = excepthook
##sys.exit(0)

class CasapyKernel(IPythonKernel):
    implementation = 'Casapy'
    implementation_version = '1.0'
    language = 'casa'
    language_version = '1.0'
    language_info = {'mimetype': 'text/plain', 'name': 'Casa'}
    banner = "Casa wrapper for jupyter"
    logfile = open(casa['files']['logfile'], 'r')

    def __init__(self, **kwargs):
        super(CasapyKernel, self).__init__(**kwargs)
        self.do_execute('%matplotlib inline', True, False, {}, False) 

    def do_execute(self, code, silent, store_history=True, user_expressions=None,
                   allow_stdin=False):
	result = IPythonKernel.do_execute(self, code, silent, store_history, user_expressions, allow_stdin)
        # Traverse log, this is not ideal. It would be better to have our own logger application and
        # use that to obtain logging information.
        loglines = []
        logfile = self.logfile
        line = logfile.readline()
        while line != "":
            task = line.split()[3].split(':')[0]
            if task != 'casa':
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
            else:
                errorcolor = ''
                errorin = ''
            html_code = '<button type="button" ' + errorcolor + 'class="btn btn-info" data-toggle="collapse" id="' + button_id + '" data-target="#log' + button_id + '" ' +\
                   'onclick="if ($(\'#\'+this.id).html()==\'Show log\') {$(\'#\'+this.id).html(\'Hide log\')} else {$(\'#\'+this.id).html(\'Show log\')}; return false"' + \
                   '>Show log</button> <div class="collapse' + errorin + '" id="log' + button_id + '">' + "<br>".join(loglines) + '</div>'
            IPython.display.display_html(html_code, raw=True)
        return result
