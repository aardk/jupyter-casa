try:
    from ipykernel.kernelapp import IPKernelApp
except ImportError:
    from IPython.kernel.zmq.kernelapp import IPKernelApp
from .start_casa import *
IPKernelApp.user_ns = globals()
IPKernelApp.launch_instance(kernel_class=CasapyKernel)
