import sys
import os
import pylab as pl
import Tkinter as Tk
from matplotlib.backend_bases import cursors
import matplotlib
rcParams = matplotlib.rcParams
from matplotlib._pylab_helpers import Gcf

cursord = {
    cursors.MOVE: "fleur",    
    cursors.HAND: "hand2",
    cursors.POINTER: "arrow",
    cursors.SELECT_REGION: "tcross",
    }

class PlotFlag:   
    """
    (1) Start the internal python interpreter... 
    and make the 'pylab' module from the main python/casapy namespace 
    visible inside it. ( done inside TPPlotter )  Note that 'pylab' is the 
    only module of casapy that is visible from this internal interpreter.
    
    (2) figmanager = pl.get_current_fig_manager() 
    -> This gets a handle to the current window, canvas, toolbar.
    	
    (3) Create the python-C++ call-back module -> PyBind. 
        ( description in tables/implement/TablePlot/PlotterGlobals.cc )
	
    (3) TablePlotTkAgg.py  implements a python class called 'PlotFlag'
        which takes an instance of 'PyBind' and 'figmanager' and makes 
	the connection between the two.

	- Additional buttons are placed in the toolbar, and their callbacks
	  defined to call methods of PyBind.
	- The toolbar event-loop is captured - by explicitly disconnecting
	  previous bindings, and re-defining them for 'pan','zoom','mark-region'
	  modes. (need to do all three, to get them to interact properly with each other)
	- Some Canvas events are also redefined to allow mark-region boxes to
	  automatically resize and move around, when the window is resized or
	  when in pan or zoom modes. ( This is needed to allow flagging with
	  zooming ).
	 
    (4) Back to the internal python interpreter. The following steps are carried out.
        -> figmanager = pl.get_current_fig_manager()
	-> import PyBind
	-> from TablePlotTkagg import PlotFlag
	-> pf = PlotFlag( PyBind )
	-> pf.setup_custom_features( figmanager )

	----> All binding is complete at this point.
	----> All other logic is to ensure things like... make sure new buttons are
	      added only when needed... make sure they *are* added when needed... and
	      this has to keep up with the native TkAgg matplotlib backend's
	      whimsical decisions of when to create a new figure and when not to.
	
    """
    def __init__(self,PyBind):
        #print "Init PlotFlag"
	self.PyBind = PyBind;
	self.newtoolbar = False;
        self.quitted = False;

    def sub(self):
        #pass
        self.quitted = True;
        self.PyBind.quit(True);

    def setup_custom_features(self,cfigman):
        if (rcParams['backend'].lower() == 'agg'):
            return
	self.toolbar = cfigman.toolbar;
        self.canvas = self.toolbar.canvas;
	self.window = cfigman.window;
	self.figmanager = cfigman;
        self.figmanager.window.wm_title("CASA Plotter");
        self.figmanager.window.protocol("WM_DELETE_WINDOW", self.sub);
	
	if self.newtoolbar is True:
		# Add new buttons
		self.add_buttons();
		
		# Reconfigure buttons.
		self.configure_buttons();

		self.newtoolbar = False;

	# Toolbar parameters
	self.panel=0;
        self.rows=0;
        self.cols=0;
	
	# Canvas parameters
	self.regionlist=[];
	self.panelregionlist=[];
	self.axeslist=[];
        self.erase_rects();

	# Re-Make event bindings
        self.canvas.keyvald.update({65307 : 'escape'});
	self.canvas.mpl_disconnect(self.toolbar._idDrag)
	self.toolbar._idDrag=self.canvas.mpl_connect('motion_notify_event', self.mouse_move)
	self.canvas._tkcanvas.bind("<KeyRelease>", self.key_release);
	self.canvas._tkcanvas.bind("<Configure>", self.resize);
        self.canvas._tkcanvas.bind("<Destroy>", self.destroy);
        #self.window.bind("<Destroy>", self.destroy);


    def plotflag_cleanup(self):
	self.canvas._tkcanvas.bind("<Destroy>", None);

    def set_cursor(self, cursor):
        self.toolbar.set_cursor(cursor);
        #self.toolbar.window.configure(cursor=cursord[cursor]);

    def _NewButton(self, frame, text, file, command, side=Tk.LEFT):
	#file = os.path.join(rcParams['datapath'], 'images', file)
	#file = '/opt/casa/stable/darwin/python/2.5' + file;
	#im = Tk.PhotoImage(master=frame, file=file)
        if(os.uname()[0] == 'Darwin'):
                b = Tk.Button(master=frame, text=text, command=command)
        else:
                b = Tk.Button(master=frame, text=text, padx=2, pady=2, command=command)
	#master=frame, text=text, padx=2, pady=2, image=im, command=command)
	#b._ntimage = im
	b.pack(side=side)
        return b

    def add_buttons(self):
	#self.newframe = Tk.Frame()
	self.newframe = Tk.Frame(master=self.window)
	bside = Tk.LEFT;
        self.toolbar.bMarkRegion = self._NewButton( frame=self.newframe, 
                                            text="Mark Region", 
				            file="markregion.ppm",
					    #file="markregion2.ppm",
					    command=self.markregion,
					    side=bside)
	self.toolbar.bFlag = self._NewButton(frame=self.newframe,
			             text="Flag", 
				     file="flag4.ppm",
				     command=None,
				     side=bside)
	
	self.toolbar.bUnflag = self._NewButton(frame=self.newframe,
	                               text="Unflag", 
				       file="unflag4.ppm",
				       command=None,
				       side=bside)
	
	self.toolbar.bLocate = self._NewButton(frame=self.newframe,
	                               text="Locate", 
				       file="locate4.ppm",
				       command=None,
				       side=bside)
	
	self.toolbar.bIterNext = self._NewButton(frame=self.newframe,
	                               text=" Next ", 
				       file="locate4.ppm",
				       command=None,
				       side=bside)
	
        self.toolbar.bClear =None;
        #self.toolbar.bClear = self._NewButton(frame=self.newframe,
        #                               text=" Clear ", 
        #			       file="locate4.ppm",
        #			       command=None,
        #			       side=bside)
	
	self.toolbar.bQuit = self._NewButton(frame=self.newframe,
	                               text=" Quit ", 
				       file="locate4.ppm",
				       command=None,
				       side=bside)
	self.toolbar.bMarkRegion.config(background='lightblue');
	self.toolbar.bFlag.config(background='lightblue');
	self.toolbar.bUnflag.config(background='lightblue');
	self.toolbar.bLocate.config(background='lightblue');
	self.toolbar.bIterNext.config(background='lightblue',state='disabled');
        #self.toolbar.bClear.config(background='lightblue');
	self.toolbar.bQuit.config(background='lightblue');

	self.newframe.pack(side=Tk.BOTTOM,fill=Tk.BOTH);
        #self.newframe.pack_propagate();

    def configure_buttons(self):
	self.toolbar.bHome.config(command=self.home);
	self.toolbar.bForward.config(command=self.forward);
	self.toolbar.bBack.config(command=self.back);
	self.toolbar.bsubplot.config(command=self.configure_subplots);
	self.toolbar.bPan.config(command=self.pan);
	self.toolbar.bZoom.config(command=self.zoom);
	self.toolbar.bMarkRegion.config(command=self.markregion);
	self.toolbar.bFlag.config(command=self.flag);
	self.toolbar.bUnflag.config(command=self.unflag);
	self.toolbar.bLocate.config(command=self.locate);
	self.toolbar.bIterNext.config(command=self.iterplotnext);
        #self.toolbar.bClear.config(command=self.clearplot);
	self.toolbar.bQuit.config(command=self.quit);
	#self.toolbar.bIterstop.config(command=self.iterplotstop);
        ### comment the next line when Wes updates matplotlib.
        #self.toolbar.bsave.config(command=self.savefig);

    def flag(self, *args):
	self.operate(1);

    def unflag(self, *args):
	self.operate(0);

    def locate(self, *args):
	self.operate(2);

    def operate(self, flag=1):
	#print '** Record the following regions'
	#for pr in self.canvas.panelregionlist:
		#print 'Region on panel [%(r)d,%(c)d,%(p)d] : [%(t1).3f, %(t2).3f, %(t3).3f, %(t4).3f] '%{'r':pr[5],'c':pr[6], 'p':pr[4],'t1':pr[0],'t2':pr[2], 't3':pr[1], 't4':pr[3]};
	self.PyBind.markregion(self.panelregionlist);
        self.erase_rects();
	if( flag is 1 ):
		#print "**Flag !!";
		self.PyBind.flagdata();
	if( flag is 0 ):
		#print "**UnFlag !!";
		self.PyBind.unflagdata();
	if( flag is 2 ):
		#print "**Locate !!";
		self.PyBind.locatedata();

    def iterplotnext(self, *args):
	self.PyBind.iterplotnext();

    def iterplotstop(self, *args):
	self.PyBind.iterplotstop();

    def clearplot(self, *args):
	#print 'Gui::calling clearplot'
	self.PyBind.clearplot();
	#print 'Gui::finished clearplot'

    def savefig(self, *args):
        import time;
        fname = 'plot-casapy-'+time.strftime('%Y-%m-%dT%H:%M:%S')+'.png';
        print 'Saving figure as ', fname, ' in current working directory.'
        self.canvas.figure.savefig(fname);

    def enable_iter_button(self):
        #if (rcParams['backend'].lower() == 'agg'):
        #    return
	#if( self.toolbar.bIterNext is not None ):
	#	self.toolbar.bIterNext.config(state='normal');
        return

    def disable_iter_button(self):
        #if (rcParams['backend'].lower() == 'agg'):
        #    return
	#if( self.toolbar.bIterNext is not None ):
	#       self.toolbar.bIterNext.config(state='disabled');
        return

    def enable_markregion_button(self):
        #if (rcParams['backend'].lower() == 'agg'):
        #    return
	#if( self.toolbar.bMarkRegion is not None ):
	#       self.toolbar.bMarkRegion.config(state='normal');
        return

    def disable_markregion_button(self):
        #if (rcParams['backend'].lower() == 'agg'):
        #    return
	#if( self.toolbar.bMarkRegion is not None ):
	#       self.toolbar.bMarkRegion.config(state='disabled');
        return

    def enable_flag_button(self):
        #if (rcParams['backend'].lower() == 'agg'):
        #    return
	#if( self.toolbar.bFlag is not None ):
	#	self.toolbar.bFlag.config(state='normal');
        return

    def disable_flag_button(self):
        #if (rcParams['backend'].lower() == 'agg'):
        #    return
	#if( self.toolbar.bFlag is not None ):
	#	self.toolbar.bFlag.config(state='disabled');
        return

    def enable_unflag_button(self):
        #if (rcParams['backend'].lower() == 'agg'):
        #    return
	#if( self.toolbar.bUnflag is not None ):
	#	self.toolbar.bUnflag.config(state='normal');
        return

    def disable_unflag_button(self):
        #if (rcParams['backend'].lower() == 'agg'):
        #    return
	#if( self.toolbar.bUnflag is not None ):
	#	self.toolbar.bUnflag.config(state='disabled');
        return

    def enable_locate_button(self):
        #if (rcParams['backend'].lower() == 'agg'):
        #    return
	#if( self.toolbar.bLocate is not None ):
	#	self.toolbar.bLocate.config(state='normal');
        return

    def disable_locate_button(self):
        #if (rcParams['backend'].lower() == 'agg'):
        #    return
	#if( self.toolbar.bLocate is not None ):
	#	self.toolbar.bLocate.config(state='disabled');
        return

    def enable_clear_button(self):
        #if (rcParams['backend'].lower() == 'agg'):
        #    return
	#if( self.toolbar.bClear is not None ):
	#	self.toolbar.bClear.config(state='normal');
        return

    def disable_clear_button(self):
        #if (rcParams['backend'].lower() == 'agg'):
        #    return
	#if( self.toolbar.bClear is not None ):
	#	self.toolbar.bClear.config(state='disabled');
        return

    def enable_quit_button(self):
        #if (rcParams['backend'].lower() == 'agg'):
        #    return
	#if( self.toolbar.bQuit is not None ):
	#	self.toolbar.bQuit.config(state='normal');
        return

    def disable_quit_button(self):
        #if (rcParams['backend'].lower() == 'agg'):
        #    return
	#if( self.toolbar.bQuit is not None ):
	#	self.toolbar.bQuit.config(state='disabled');
        return

    def draw_rubberband(self, event, x0, y0, x1, y1):
        if (rcParams['backend'].lower() == 'agg'):
            return
        ### workaround for matplotlib API changes
        #height = self.canvas.figure.bbox.height()  #0.91.4
        #height = self.canvas.figure.bbox.height    #>=0.98
        height = self.get_bbox_size(self.canvas.figure.bbox,"height") #workaround
        y0 =  height-y0
        y1 =  height-y1
        try: self.toolbar.lastrect
        except AttributeError: pass
        else: self.canvas._tkcanvas.delete(self.toolbar.lastrect)
        self.toolbar.lastrect = self.canvas._tkcanvas.create_rectangle(x0, y0, x1, y1, width=2,outline='black')


    def draw_rect(self, x0, y0, x1, y1, x0data, y0data, x1data, y1data,a,panel,rows,cols):
       	self.panelregionlist.append([x0data,y0data,x1data,y1data,panel+1,rows,cols]);
	self.axeslist.append(a);
        ### workaround for matplotlib API changes
        #height = self.canvas.figure.bbox.height()  #0.91.4
        #height = self.canvas.figure.bbox.height    #>=0.98
        height = self.get_bbox_size(self.canvas.figure.bbox,"height") #workaround
        y0 =  height-y0
        y1 =  height-y1
        if(os.uname()[0] == 'Darwin'):
               rect = self.canvas._tkcanvas.create_rectangle(x0, y0, x1, y1, width=2,outline='black')
        else:
               rect = self.canvas._tkcanvas.create_rectangle(x0, y0, x1, y1, width=2,fill='black',stipple='gray50',outline='black')
        self.regionlist.append(rect);

    def erase_rects(self):
        #print "erase rects"
        if (rcParams['backend'].lower() == 'agg'):
            return
	for q in self.regionlist:
	  self.canvas._tkcanvas.delete(q);
	self.regionlist = [];
	self.panelregionlist = [];
	self.axeslist = [];


    def redraw_rects(self):
	for q in self.regionlist:
	  self.canvas._tkcanvas.delete(q);
	self.regionlist = [];
	
	for z in range(0,len(self.panelregionlist)):
	  q = self.panelregionlist[z];
	  a = self.axeslist[z];
          x0=q[0]; y0=q[1]; x1=q[2]; y1=q[3];
          # map to new zoom limits (current fig co-ords)
          ### workaround for matplotlib API changes
          #px0,py0 = a.transData.xy_tup( (x0, y0) )     #0.91
          #px0,py0 = a.transData.transform( (x0, y0) )  #>=0.98
          px0,py0 = self.get_xy(a.transData, (x0, y0) ) #workaround
          ### workaround for matplotlib API changes
          #px1,py1 = a.transData.xy_tup( (x1, y1) )     #0.91
          #px1,py1 = a.transData.transform( (x1, y1) )  #>=0.98
          px1,py1 = self.get_xy(a.transData, (x1, y1) )

          ### workaround for matplotlib API changes
          #height = self.canvas.figure.bbox.height()   #0.91
          #height = self.canvas.figure.bbox.height     #>=0.98
          height = self.get_bbox_size(self.canvas.figure.bbox,"height") #workaround
  	  py0 =  height-py0
  	  py1 =  height-py1
          if(os.uname()[0] == 'Darwin'):
               rect = self.canvas._tkcanvas.create_rectangle(px0, py0, px1, py1, width=2,outline='black')
          else:
               rect = self.canvas._tkcanvas.create_rectangle(px0, py0, px1, py1, width=2,fill='black',stipple='gray50',outline='black')
	  self.regionlist.append(rect);

    def resize(self, event):
	#print 'canvas resize'
	self.canvas.resize(event);
	self.redraw_rects();

    def destroy(self,*args):
        #print 'Gui::destroy.'
        self.erase_rects();
        self.newtoolbar = True;
        if self.quitted is False:
                self.quit(closewin=True);
                print " ";
                #print "................................................................";
                #print "............. Please IGNORE Tkinter error message. .............";
                #print "................................................................";

    def quit(self, closewin=True):
        #print 'quit with close-window : ', closewin;
        self.quitted = True;
        self.PyBind.quit(closewin);

    def key_release(self, event):
	#print 'key release'
	self.canvas.key_release(event);
        key = self.canvas._get_key(event);
	if(key=='escape'):
		numreg = len(self.regionlist);
		if(numreg>0):
			self.canvas._tkcanvas.delete(self.regionlist[numreg-1]);
			self.regionlist.pop();
			self.panelregionlist.pop();
			self.axeslist.pop();


    def home(self, *args):
        'restore the original view'
        if (rcParams['backend'].lower() == 'agg'):
            return
	self.toolbar.home();
	self.redraw_rects();

    def back(self, *args):
        'move back up the view lim stack'
        if (rcParams['backend'].lower() == 'agg'):
            return
	self.toolbar.back();
	self.redraw_rects();

    def forward(self, *args):
        'move forward in the view lim stack'
        if (rcParams['backend'].lower() == 'agg'):
            return
	self.toolbar.forward();
	self.redraw_rects();

    def configure_subplots(self):
	'configure subplots'
        if (rcParams['backend'].lower() == 'agg'):
            return
	self.toolbar.configure_subplots();
	self.redraw_rects();


    def markregion(self, *args):
        'activate mark-region mode'
        if (rcParams['backend'].lower() == 'agg'):
            return
        if self.toolbar._active == 'MARKREGION':
	    #self.toolbar._active = None
            self.erase_rects();
	    self.update_relief(newmode=None);
        else:
	    #self.toolbar._active = 'MARKREGION'
	    self.update_relief(newmode='MARKREGION');
	    

        if self.toolbar._idPress is not None:
            self.toolbar._idPress=self.canvas.mpl_disconnect(self.toolbar._idPress)
            self.toolbar.mode = ''

        if self.toolbar._idRelease is not None:
            self.toolbar._idRelease=self.canvas.mpl_disconnect(self.toolbar._idRelease)
            self.toolbar.mode = ''

        if  self.toolbar._active:
            self.toolbar._idPress = self.canvas.mpl_connect('button_press_event', self.press_markregion)
            self.toolbar._idRelease = self.canvas.mpl_connect('button_release_event', self.release_markregion)
            self.toolbar.mode = 'Mark Region mode'
            self.canvas.widgetlock(self.toolbar)
        else:
            self.canvas.widgetlock.release(self.toolbar)

        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self.toolbar._active)

        self.toolbar.set_message(self.toolbar.mode)

    def press_markregion(self, event):
        'the press mouse button in mark region mode callback'
        if (rcParams['backend'].lower() == 'agg'):
            return
        if event.button == 1:
            self.toolbar._button_pressed=1
        elif  event.button == 3:
            self.toolbar._button_pressed=3
        else:
            self.toolbar._button_pressed=None
	    return
	
	# Check that the click is inside the canvas.

        x, y = event.x, event.y

        # push the current view to define home if stack is empty
        if self.toolbar._views.empty(): self.toolbar.push_current()

        self.toolbar._xypress=[]
        for i, a in enumerate(self.canvas.figure.get_axes()):
            #if x is not None and y is not None and a.in_axes(x, y) and a.get_navigate():
            if x is not None and y is not None and event.inaxes==a and a.get_navigate():
                xmin, xmax = a.get_xlim()
                ymin, ymax = a.get_ylim()
                lim = xmin, xmax, ymin, ymax
                ### workaround for matplotlib API changes
                #self.toolbar._xypress.append(( x, y, a, i, lim, a.transData.deepcopy() ))  #0.91.4
                #self.toolbar._xypress.append(( x, y, a, i, lim, a.transData.frozen() ))    #>=0.98
                self.toolbar._xypress.append(( x, y, a, i, lim, self.copy_trans(a.transData)))  #workaround
		one, two, three = event.inaxes.get_geometry()
		self.panel = three-1
		self.rows = one
		self.cols = two

        self.toolbar.press(event)

    def release_markregion(self, event):
        'the release mouse button callback in mark region mode'
        if (rcParams['backend'].lower() == 'agg'):
            return
        if not self.toolbar._xypress: return

        for cur_xypress in self.toolbar._xypress:
            x, y = event.x, event.y
            lastx, lasty, a, ind, lim, trans = cur_xypress

            xmin, ymin, xmax, ymax = lim

            # mark rect
            ### workaround for matplotlib API changes
            #lastx, lasty = a.transData.inverse_xy_tup( (lastx, lasty) )        #0.91.4
            #lastx, lasty = a.transData.inverted().transform( (lastx, lasty) )  #>=0.98
            lastx, lasty = self.get_inverse_xy(a.transData, (lastx, lasty) )    #workaround
            ### workaround for matplotlib API changes
            #x, y = a.transData.inverse_xy_tup( (x, y) )        #0.91.4
            #x, y = a.transData.inverted().transform( (x, y) )  #>=0.98
            x, y = self.get_inverse_xy(a.transData, (x, y) )    #workaround
            Xmin,Xmax=a.get_xlim()
            Ymin,Ymax=a.get_ylim()

            if Xmin < Xmax:
                if x<lastx:  xmin, xmax = x, lastx
                else: xmin, xmax = lastx, x
                if xmin < Xmin: xmin=Xmin
                if xmax > Xmax: xmax=Xmax
            else:
                if x>lastx:  xmin, xmax = x, lastx
                else: xmin, xmax = lastx, x
                if xmin > Xmin: xmin=Xmin
                if xmax < Xmax: xmax=Xmax

            if Ymin < Ymax:
                if y<lasty:  ymin, ymax = y, lasty
                else: ymin, ymax = lasty, y
                if ymin < Ymin: ymin=Ymin
                if ymax > Ymax: ymax=Ymax
            else:
                if y>lasty:  ymin, ymax = y, lasty
                else: ymin, ymax = lasty, y
                if ymin > Ymin: ymin=Ymin
                if ymax < Ymax: ymax=Ymax

        ### workaround for matplotlib API changes
        #px1,py1 = a.transData.xy_tup( (xmin, ymin) )     #0.91.4
        #px1,py1 = a.transData.transform( (xmin, ymin) )  #>=0.98
        px1,py1 = self.get_xy(a.transData, (xmin, ymin) ) #workaround
        #px2,py2 = a.transData.xy_tup( (xmax, ymax) )     #0.91.4
        #px2,py2 = a.transData.transform( (xmax, ymax) )  #>=0.98
        px2,py2 = self.get_xy(a.transData, (xmax, ymax) ) #workaround
	    
	self.draw_rect(px1, py1, px2, py2, xmin, ymin, xmax, ymax, a, self.panel, self.rows, self.cols)
        #print 'Region on panel [%(r)d,%(c)d,%(p)d] : [%(t1).3f, %(t2).3f, %(t3).3f, %(t4).3f] '%{'r':self.rows,'c':self.cols, 'p':self.panel+1,'t1':xmin,'t2':xmax, 't3':ymin, 't4':ymax};
        
                
        #self.toolbar.draw()
        self.toolbar._xypress = None
        self.toolbar._button_pressed = None

        self.toolbar.push_current()
        self.toolbar.release(event)


    def zoom(self, *args):
        'activate zoom to rect mode'
        if (rcParams['backend'].lower() == 'agg'):
            return
        if self.toolbar._active == 'ZOOM':
	    #self.toolbar._active = None
	    self.update_relief(newmode=None);
        else:
	    #self.toolbar._active = 'ZOOM'
	    self.update_relief(newmode='ZOOM');

        if self.toolbar._idPress is not None:
            self.toolbar._idPress=self.canvas.mpl_disconnect(self.toolbar._idPress)
            self.toolbar.mode = ''

        if self.toolbar._idRelease is not None:
            self.toolbar._idRelease=self.canvas.mpl_disconnect(self.toolbar._idRelease)
            self.toolbar.mode = ''

        if  self.toolbar._active:
            self.toolbar._idPress = self.canvas.mpl_connect('button_press_event', self.press_zoom)
            self.toolbar._idRelease = self.canvas.mpl_connect('button_release_event', self.release_zoom)
            self.toolbar.mode = 'Zoom to rect mode'
            self.canvas.widgetlock(self.toolbar)
        else:
            self.canvas.widgetlock.release(self.toolbar)

        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self.toolbar._active)

        self.toolbar.set_message(self.toolbar.mode)


    def press_zoom(self, event):
        'the press mouse button in zoom to rect mode callback'
        if (rcParams['backend'].lower() == 'agg'):
            return
        if event.button == 1:
            self.toolbar._button_pressed=1
        elif  event.button == 3:
            self.toolbar._button_pressed=3
        else:
            self.toolbar._button_pressed=None
            return

        x, y = event.x, event.y

        # push the current view to define home if stack is empty
        if self.toolbar._views.empty(): self.toolbar.push_current()

        self.toolbar._xypress=[]
        for i, a in enumerate(self.canvas.figure.get_axes()):
            #if x is not None and y is not None and a.in_axes(x, y) and a.get_navigate():
            if x is not None and y is not None and event.inaxes==a and a.get_navigate():
                xmin, xmax = a.get_xlim()
                ymin, ymax = a.get_ylim()
                lim = xmin, xmax, ymin, ymax
                ### workaround for matplotlib API changes
                #self.toolbar._xypress.append(( x, y, a, i, lim, a.transData.deepcopy() ))   #0.91.4
                #self.toolbar._xypress.append(( x, y, a, i, lim, a.transData.frozen() ))     #>=0.98
                self.toolbar._xypress.append(( x, y, a, i, lim, self.copy_trans(a.transData)))  #workaround

        self.toolbar.press(event)


    def release_zoom(self, event):
        'the release mouse button callback in zoom to rect mode'
        if (rcParams['backend'].lower() == 'agg'):
            return
        if not self.toolbar._xypress: return

        for cur_xypress in self.toolbar._xypress:
            x, y = event.x, event.y
            lastx, lasty, a, ind, lim, trans = cur_xypress
            # ignore singular clicks - 5 pixels is a threshold
            if abs(x-lastx)<5 or abs(y-lasty)<5:
                self.toolbar._xypress = None
                self.toolbar.release(event)
                self.toolbar.draw()
                return

            xmin, ymin, xmax, ymax = lim

            # zoom to rect
            ### workaround for matplotlib API changes
            #lastx, lasty = a.transData.inverse_xy_tup( (lastx, lasty) )        #0.91.4
            #lastx, lasty = a.transData.inverted().transform( (lastx, lasty) )  #>=0.98
            lastx, lasty = self.get_inverse_xy(a.transData, (lastx, lasty) )    #workaround
            ### workaround for matplotlib API changes
            #x, y = a.transData.inverse_xy_tup( (x, y) )        #0.91.4
            #x, y = a.transData.inverted().transform( (x, y) )  #>=0.98
            x, y = self.get_inverse_xy(a.transData, (x, y) )    #workaround
            Xmin,Xmax=a.get_xlim()
            Ymin,Ymax=a.get_ylim()

            if Xmin < Xmax:
                if x<lastx:  xmin, xmax = x, lastx
                else: xmin, xmax = lastx, x
                if xmin < Xmin: xmin=Xmin
                if xmax > Xmax: xmax=Xmax
            else:
                if x>lastx:  xmin, xmax = x, lastx
                else: xmin, xmax = lastx, x
                if xmin > Xmin: xmin=Xmin
                if xmax < Xmax: xmax=Xmax

            if Ymin < Ymax:
                if y<lasty:  ymin, ymax = y, lasty
                else: ymin, ymax = lasty, y
                if ymin < Ymin: ymin=Ymin
                if ymax > Ymax: ymax=Ymax
            else:
                if y>lasty:  ymin, ymax = y, lasty
                else: ymin, ymax = lasty, y
                if ymin > Ymin: ymin=Ymin
                if ymax < Ymax: ymax=Ymax

            if self.toolbar._button_pressed == 1:
                a.set_xlim((xmin, xmax))
                a.set_ylim((ymin, ymax))
            elif self.toolbar._button_pressed == 3:
                if a.get_xscale()=='log':
                    alpha=log(Xmax/Xmin)/log(xmax/xmin)
                    x1=pow(Xmin/xmin,alpha)*Xmin
                    x2=pow(Xmax/xmin,alpha)*Xmin
                else:
                    alpha=(Xmax-Xmin)/(xmax-xmin)
                    x1=alpha*(Xmin-xmin)+Xmin
                    x2=alpha*(Xmax-xmin)+Xmin
                if a.get_yscale()=='log':
                    alpha=log(Ymax/Ymin)/log(ymax/ymin)
                    y1=pow(Ymin/ymin,alpha)*Ymin
                    y2=pow(Ymax/ymin,alpha)*Ymin
                else:
                    alpha=(Ymax-Ymin)/(ymax-ymin)
                    y1=alpha*(Ymin-ymin)+Ymin
                    y2=alpha*(Ymax-ymin)+Ymin
                a.set_xlim((x1, x2))
                a.set_ylim((y1, y2))

        self.toolbar.draw()
	self.redraw_rects();
        self.toolbar._xypress = None
        self.toolbar._button_pressed = None

        self.toolbar.push_current()
        self.toolbar.release(event)


    def pan(self,*args):
        'Activate the pan/zoom tool. pan with left button, zoom with right'
        # set the pointer icon and button press funcs to the
        # appropriate callbacks
        if (rcParams['backend'].lower() == 'agg'):
            return

        if self.toolbar._active == 'PAN':
	    #self.toolbar._active = None
	    self.update_relief(newmode=None);
        else:
	    #self.toolbar._active = 'PAN'
	    self.update_relief(newmode='PAN');

        if self.toolbar._idPress is not None:
            self.toolbar._idPress = self.canvas.mpl_disconnect(self.toolbar._idPress)
            self.toolbar.mode = ''

        if self.toolbar._idRelease is not None:
            self.toolbar._idRelease = self.canvas.mpl_disconnect(self.toolbar._idRelease)
            self.toolbar.mode = ''

        if self.toolbar._active:
            self.toolbar._idPress = self.canvas.mpl_connect(
                'button_press_event', self.press_pan)
            self.toolbar._idRelease = self.canvas.mpl_connect(
                'button_release_event', self.release_pan)
            self.toolbar.mode = 'pan/zoom mode'
            self.canvas.widgetlock(self.toolbar)
        else:
            self.canvas.widgetlock.release(self.toolbar)

        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self.toolbar._active)

        self.toolbar.set_message(self.toolbar.mode)


    def press_pan(self, event):
        'the press mouse button in pan/zoom mode callback'
        if (rcParams['backend'].lower() == 'agg'):
            return

        if event.button == 1:
            self.toolbar._button_pressed=1
        elif  event.button == 3:
            self.toolbar._button_pressed=3
        else:
            self.toolbar._button_pressed=None
            return

        x, y = event.x, event.y

        # push the current view to define home if stack is empty
        if self.toolbar._views.empty(): self.toolbar.push_current()

        self.toolbar._xypress=[]
        for i, a in enumerate(self.canvas.figure.get_axes()):
            #if x is not None and y is not None and a.in_axes(x, y) and a.get_navigate():
            if x is not None and y is not None and event.inaxes==a and a.get_navigate():
                xmin, xmax = a.get_xlim()
                ymin, ymax = a.get_ylim()
                lim = xmin, xmax, ymin, ymax
                ### workaround for matplotlib API changes
                #self.toolbar._xypress.append((x, y, a, i, lim,a.transData.deepcopy()))  #0.91.4
                #self.toolbar._xypress.append((x, y, a, i, lim,a.transData.frozen()))    #>=0.98
                self.toolbar._xypress.append((x, y, a, i, lim,self.copy_trans(a.transData))) #workaround
                self.canvas.mpl_disconnect(self.toolbar._idDrag)
                self.toolbar._idDrag=self.canvas.mpl_connect('motion_notify_event', self.drag_pan)

        self.toolbar.press(event)


    def release_pan(self, event):
        'the release mouse button callback in pan/zoom mode'
        if (rcParams['backend'].lower() == 'agg'):
            return
        self.canvas.mpl_disconnect(self.toolbar._idDrag)
        self.toolbar._idDrag=self.canvas.mpl_connect('motion_notify_event', self.mouse_move)
        if not self.toolbar._xypress: return
        self.toolbar._xypress = None
        self.toolbar._button_pressed=None
        self.toolbar.push_current()
        self.toolbar.release(event)
        self.toolbar.draw()
	self.redraw_rects();


    def drag_pan(self, event):
        'the drag callback in pan/zoom mode'
        if (rcParams['backend'].lower() == 'agg'):
            return

        def format_deltas(event,dx,dy):
            if event.key=='control':
                if(abs(dx)>abs(dy)):
                    dy = dx
                else:
                    dx = dy
            elif event.key=='x':
                dy = 0
            elif event.key=='y':
                dx = 0
            elif event.key=='shift':
                if 2*abs(dx) < abs(dy):
                    dx=0
                elif 2*abs(dy) < abs(dx):
                    dy=0
                elif(abs(dx)>abs(dy)):
                    dy=dy/abs(dy)*abs(dx)
                else:
                    dx=dx/abs(dx)*abs(dy)
            return (dx,dy)

        for cur_xypress in self.toolbar._xypress:
            lastx, lasty, a, ind, lim, trans = cur_xypress
            xmin, xmax, ymin, ymax = lim
            #safer to use the recorded button at the press than current button:
            #multiple button can get pressed during motion...
            if self.toolbar._button_pressed==1:
                ### workaround for matplotlib API changes
                #lastx, lasty = trans.inverse_xy_tup( (lastx, lasty) )          #0.91.4
                #lastx, lasty = trans.inverted().transform( (lastx, lasty) )    #>=0.98
                lastx, lasty = self.get_inverse_xy(trans, (lastx, lasty) )      #workaround
                ### workaround for matplotlib API changes
                #x, y = trans.inverse_xy_tup( (event.x, event.y) )        #0.91.4
                #x, y = trans.inverted().transform( (event.x, event.y) )  #>=0.98
                x, y = self.get_inverse_xy(trans, (event.x, event.y) )    #workaround
                if a.get_xscale()=='log':
                    dx=1-lastx/x
                else:
                    dx=x-lastx
                if a.get_yscale()=='log':
                    dy=1-lasty/y
                else:
                    dy=y-lasty

                dx,dy=format_deltas(event,dx,dy)

                if a.get_xscale()=='log':
                    xmin *= 1-dx
                    xmax *= 1-dx
                else:
                    xmin -= dx
                    xmax -= dx
                if a.get_yscale()=='log':
                    ymin *= 1-dy
                    ymax *= 1-dy
                else:
                    ymin -= dy
                    ymax -= dy
            elif self.toolbar._button_pressed==3:
                try:
                    ### workaround for matplotlib API changes
                    #dx=(lastx-event.x)/float(a.bbox.width())  #0.91.4
                    #dx=(lastx-event.x)/float(a.bbox.width)    #>=0.98
                    dx=(lastx-event.x)/float(self.get_bbox_size(a.bbox,"width")) #workaround
                    ### workaround for matplotlib API changes
                    #dy=(lasty-event.y)/float(a.bbox.height()) #0.91.4
                    #dy=(lasty-event.y)/float(a.bbox.height)   #>=0.98
                    dy=(lasty-event.y)/float(self.get_bbox_size(a.bbox,"height"))  #workaround
                    dx,dy=format_deltas(event,dx,dy)
                    if a.get_aspect() != 'auto':
                        dx = 0.5*(dx + dy)
                        dy = dx
                    alphax = pow(10.0,dx)
                    alphay = pow(10.0,dy)#use logscaling, avoid singularities and smother scaling...
                    ### workaround for matplotlib API changes
                    #lastx, lasty = trans.inverse_xy_tup( (lastx, lasty) )       #0.91.4
                    #lastx, lasty = trans.inverted().transform( (lastx, lasty) ) #>=0.98
                    lastx, lasty = self.get_inverse_xy(trans, (lastx, lasty) )   #workaround
                    if a.get_xscale()=='log':
                        xmin = lastx*(xmin/lastx)**alphax
                        xmax = lastx*(xmax/lastx)**alphax
                    else:
                        xmin = lastx+alphax*(xmin-lastx)
                        xmax = lastx+alphax*(xmax-lastx)
                    if a.get_yscale()=='log':
                        ymin = lasty*(ymin/lasty)**alphay
                        ymax = lasty*(ymax/lasty)**alphay
                    else:
                        ymin = lasty+alphay*(ymin-lasty)
                        ymax = lasty+alphay*(ymax-lasty)
                except OverflowError:
                    warnings.warn('Overflow while panning')
                    return
            a.set_xlim(xmin, xmax)
            a.set_ylim(ymin, ymax)
	    self.redraw_rects();

        self.toolbar.dynamic_update()


    def mouse_move(self, event):
        #print 'mouse_move', event.button
        if (rcParams['backend'].lower() == 'agg'):
            return

        if not event.inaxes or not self.toolbar._active:
            if self.toolbar._lastCursor != cursors.POINTER:
                self.set_cursor(cursors.POINTER)
                self.toolbar._lastCursor = cursors.POINTER
        else:
            if self.toolbar._active=='ZOOM':
                if self.toolbar._lastCursor != cursors.SELECT_REGION:
                    self.set_cursor(cursors.SELECT_REGION)
                    self.toolbar._lastCursor = cursors.SELECT_REGION
                if self.toolbar._xypress:
                    x, y = event.x, event.y
                    lastx, lasty, a, ind, lim, trans= self.toolbar._xypress[0]
                    self.draw_rubberband(event, x, y, lastx, lasty)
            elif self.toolbar._active=='MARKREGION':
                if self.toolbar._lastCursor != cursors.SELECT_REGION:
                    self.set_cursor(cursors.SELECT_REGION)
                    self.toolbar._lastCursor = cursors.SELECT_REGION
                if self.toolbar._xypress:
                    x, y = event.x, event.y
                    lastx, lasty, a, ind, lim, trans= self.toolbar._xypress[0]
                    self.draw_rubberband(event, x, y, lastx, lasty)
            elif (self.toolbar._active=='PAN' and
                  self.toolbar._lastCursor != cursors.MOVE):
                self.set_cursor(cursors.MOVE)

                self.toolbar._lastCursor = cursors.MOVE

        if event.inaxes and event.inaxes.get_navigate():


            try: s = event.inaxes.format_coord(event.xdata, event.ydata)
            except ValueError: pass
            except OverflowError: pass
            else:
                if len(self.toolbar.mode):
                    self.toolbar.set_message('%s : %s' % (self.toolbar.mode, s))
                else:
                    self.toolbar.set_message(s)
        else: self.toolbar.set_message(self.toolbar.mode)


    def update_relief(self,newmode):
        'activate new mode'
        if (rcParams['backend'].lower() == 'agg'):
            return
        if self.toolbar._active == 'ZOOM':
	    self.toolbar.bZoom.config(relief='raised');
        if self.toolbar._active == 'PAN':
	    self.toolbar.bPan.config(relief='raised');
        if self.toolbar._active == 'MARKREGION':
	    self.toolbar.bMarkRegion.config(relief='raised');
         
	self.toolbar._active = newmode;

        if self.toolbar._active == 'ZOOM':
	    self.toolbar.bZoom.config(relief='sunken');
        if self.toolbar._active == 'PAN':
	    self.toolbar.bPan.config(relief='sunken');
        if self.toolbar._active == 'MARKREGION':
	    self.toolbar.bMarkRegion.config(relief='sunken');


    #### Workarounds for Matplotlib version handling (ugly) ####
    def ismatlab_new(self):
        verstr=matplotlib.__version__.split(".")
        maj=int(verstr[0])
        sub=int(verstr[1])
        return (maj>0 or sub>=98)

    def get_inverse_xy(self,trans,(x,y)):
        if hasattr(trans,"inverse_xy_tup"): return trans.inverse_xy_tup((x, y))
        elif hasattr(trans,"inverted"): return trans.inverted().transform((x, y))
        else: return None

    def get_xy(self,trans,(x,y)):
        return self.switch_func(trans,["xy_tup","transform"],(x,y))

    def copy_trans(self,trans): 
        return self.switch_func(trans,["deepcopy","frozen"])
        
    def get_bbox_size(self,obj,func=""):
        return self.get_called_or_attr(obj,func)

    def switch_func(self,obj,funcs=[],*args,**kwargs):
        """
        Tries a list of functions and return a result from callable one.
        Deals with function name changes but parameters have to be unchanged.
        """
        for func in funcs:
            called_func=self.get_called_or_attr(obj,func,*args,**kwargs)
            if called_func != None: break
        return called_func

    def get_called_or_attr(self,obj,func="",*args,**kwargs):
        """
        Returns a result from function call if it's callable.
        If not callable, returns the attribute or False (non-existent). 
        """
        #if not hasattr(obj,func): return False
        #else: called=getattr(obj,func)
        try: called=getattr(obj,func)
        #except: return False
        except: return None
        if callable(called): return called(*args,**kwargs)
        else: return called
        
        
