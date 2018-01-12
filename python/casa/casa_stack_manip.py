import sys
import string
import inspect

def stack_find(symbol, level='stack') :
    label="_casa_top_frame_"
    a=inspect.stack()
    stacklevel=0
    if level == "stack":
        for k in range(len(a)):
            if a[k][1].startswith("<ipython-input-") or \
               string.find(a[k][1], 'ipython console') > 0 or \
               string.find(a[k][1],"/casapy.py") > 0 or \
               string.find(a[k][1],"/casa.py") > 0 or \
               string.find(a[k][1],"mpi4casapy.py") > 0:
                stacklevel=k
		# aardk: if stack frame doesn't contain label, continue searching
		if sys._getframe(stacklevel).f_globals.has_key(label):
                    break

        myf=sys._getframe(stacklevel).f_globals

        if myf.has_key(symbol) and myf.has_key(label) :
            return myf[symbol]

        else:
            return None

    elif level == "root":
        for k in range(len(a)):
            if string.find(a[k][1],"start_casa.py") > 0:
                stacklevel=k
                # jagonzal: Take the first level that matches the requirement
                break

        myf=sys._getframe(stacklevel).f_globals

        if myf.has_key(symbol) :
            return myf[symbol]

        else:
            return None

    else:
        raise RuntimeError("unknown stack level %s" % level)


def stack_frame_find(level='stack') :
    label="_casa_top_frame_"
    a=inspect.stack()
    stacklevel=0
    if level == "stack":
        for k in range(len(a)):
            if a[k][1].startswith("<ipython-input-") or \
               string.find(a[k][1], 'ipython console') > 0 or \
               string.find(a[k][1],"/casapy.py") > 0 or \
               string.find(a[k][1],"/casa.py") > 0 or \
               string.find(a[k][1],'/MPICommandServer.py') > 0 or \
               string.find(a[k][1],"mpi4casapy.py") > 0:
                stacklevel=k
		# aardk: if stack frame doesn't contain label, continue searching
		if sys._getframe(stacklevel).f_globals.has_key(label):
                    break
    elif level == "root":
        for k in range(len(a)):
            if string.find(a[k][1],"start_casa.py") > 0:
                stacklevel=k
                # jagonzal: Take the first level that matches the requirement
                break
    else:
        raise RuntimeError("unknown stack level %s" % level)

    myf=sys._getframe(stacklevel).f_globals
    if myf.has_key(label) :
        return myf
    else:
        return None

def find_casa( ):
    return stack_find('casa')
