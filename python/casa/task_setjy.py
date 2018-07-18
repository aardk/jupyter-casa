from glob import glob
import os
import subprocess
import re
import sys
import shutil
from setjy_helper import * 
from taskinit import *
from parallel.parallel_task_helper import ParallelTaskHelper
import pdb

# Helper class for Multi-MS processing (by SC)
class SetjyHelper():
    def __init__(self, msfile=None):
        self.__msfile = msfile
        
    def resetModelCol(self):
        rstatus = True
        # Hide the log info
        casalog.post("Resetting the log filter to WARN", "DEBUG")
        casalog.post("Initialize the MODEL columns of sub-MSs to default 1", "DEBUG")
        casalog.filter('WARN')

        myms = mstool()
        try:
            try:
                myms.open(self.__msfile)
                submslist = myms.getreferencedtables()
                parentms = myms.name()
                myms.close()
            except:
                if (os.path.exists(self.__msfile+'/SUBMSS')):
                    casalog.post("MS may be corrupted. Try to initialize sub-MSs anyway...","DEBUG")
                    submslist = [os.path.abspath(self.__msfile+'/SUBMSS/'+fn) 
                                 for fn in os.listdir(self.__msfile+'/SUBMSS') if fn.endswith('.ms') ]
                else:
                    rstatus = False

            mycb = cbtool()
            if parentms!= submslist[0]:
                for subms in submslist:
                    mycb.open(subms, addcorr=False, addmodel=True)
                    mycb.close()            
        except:
            rstatus = False
                
        casalog.filter('INFO')

        return rstatus


def setjy(vis=None, field=None, spw=None,
          selectdata=None, timerange=None, scan=None, intent=None, observation=None,
          scalebychan=None, standard=None, model=None, modimage=None, 
          listmodels=None, fluxdensity=None, spix=None, reffreq=None, polindex=None,
          polangle=None, rotmeas=None, fluxdict=None, 
          useephemdir=None, interpolation=None, usescratch=None, ismms=None):
    """Fills the model column for flux density calibrators."""

    casalog.origin('setjy')
    casalog.post("standard="+standard,'DEBUG1')
    mylocals = locals()

    if not listmodels: # listmmodels=T does not require vis 
        sh = SetjyHelper(vis)
        rstat = sh.resetModelCol()


    # Take care of the trivial parallelization
    if ( not listmodels and ParallelTaskHelper.isParallelMS(vis) and usescratch):
        # jagonzal: We actually operate in parallel when usescratch=True because only
        # in this case there is a good trade-off between the parallelization overhead
        # and speed up due to the load involved with MODEL_DATA column creation
        # Create the default MODEL columns in all sub-MSs to avoid corruption of the MMS
        # when there are NULL MS selections
        #
        # TT: Use ismms is used to change behavior of some of the execption handling
        # for MMS case. It is a hidden task parameter only modified when input vis
        # is identified as MMS via SetjyHelper.resetModel().
      
        #sh = SetjyHelper(vis)
        #rstat = sh.resetModelCol()

        if rstat:
            ismms=rstat
            mylocals['ismms']=ismms
            #print "mylocals now=",mylocals
            helper = ParallelTaskHelper('setjy', mylocals)
            helper._consolidateOutput = False
            #helper._consolidateOutput = True
            try:
                retval = helper.go()

                # Remove the subMS names from the returned dictionary
                #print "remove subms names ...retval=",retval
                if (any(isinstance(v,dict) for v in retval.itervalues())):
                    for subMS in retval:
                        dict_i = retval[subMS]
                        if isinstance(dict_i,dict):
                            retval = dict_i
                            break
                else:
                    casalog.post("Error in parallel processing of MMS",'SEVERE')
                    retval = False
            except Exception, instance:
                retval = False
        else:
            casalog.post("Could not initialize MODEL columns in sub-MSs", 'SEVERE')
            retval = False
    else:
        retval = setjy_core(vis, field, spw, selectdata, timerange, 
                        scan, intent, observation, scalebychan, standard, model, 
                        modimage, listmodels, fluxdensity, spix, reffreq,
                        polindex, polangle, rotmeas, fluxdict, 
                        useephemdir, interpolation, usescratch, ismms)

    #pdb.set_trace()
    return retval


def setjy_core(vis=None, field=None, spw=None,
               selectdata=None, timerange=None, scan=None, intent=None, observation=None,
               scalebychan=None, standard=None, model=None, modimage=None, listmodels=None,
               fluxdensity=None, spix=None, reffreq=None,
               polindex=None, polangle=None, rotmeas=None, fluxdict=None,
               useephemdir=None, interpolation=None, usescratch=None, ismms=None):
    """Fills the model column for flux density calibrators."""

    #retval = True
    clnamelist=[]
    # remove componentlist generated
    deletecomp = True
    #deletecomp = False 
    try:
        # Here we only list the models available, but don't perform any operation
        if listmodels:
            retval=True
            casalog.post("Listing model candidates (listmodels == True).")
            if vis:
              casalog.post("%s is NOT being modified." % vis)

            if standard=='Butler-JPL-Horizons 2012':
                tpm_supported_objects = ['Ceres','Lutetia','Pallas','Vesta']
                #ssmoddirs = findCalModels(target='SolarSystemModels',
                #              roots=[casa['dirs']['data']],
                #              exts=['.im','.ms','tab', 'dat'])
                #ssmoddirs = findCalModels(target='SolarSystemModels',
                #                   roots=[casa['dirs']['data']],
                #                   exts=['.im','.ms','tab', 'dat'])
                #for d in ssmoddirs:
                #        lsmodims(d,modpat='*ALMA_TPMprediction*.txt', header='TPM models of asteroid available for %s' % standard) 
                ssmoddirs = findCalModels(target='SolarSystemModels',
                           roots=[casa['dirs']['data']],
                           exts=['.im','.ms','tab'])
                sstpmdirs = findCalModels(target='SolarSystemModels',
                           roots=[casa['dirs']['data']],
                           exts=['.im','.ms','tab'])
                if ssmoddirs==set([]):
                     casalog.post("No models were found. Missing SolarSystemModels in the CASA data directory","WARN")           
                for d in ssmoddirs:
                    lsmodims(d,modpat='*Tb*.dat', header='Tb models of solar system objects available for %s' % standard) 
                for d in sstpmdirs:
                    lsmodims(d,modpat='*fd_time.dat', header='Time variable models of asteroids available for %s [only applicable for the observation date 2015.01.01 0UT and beyond]' % standard) 
            elif standard=='Butler-JPL-Horizons 2010':
                availmodellist=['Venus', 'Mars', 'Jupiter', 'Uranus', 'Neptune', 'Pluto',
                                'Io', 'Europa', 'Ganymede', 'Callisto', 'Titan','Triton',
                                'Ceres', 'Pallas', 'Vesta', 'Juno', 'Victoria', 'Davida']
                print "Solar system objects recognized by %s:" % standard
                print availmodellist 
            else:
                lsmodims('.', modpat='*.im* *.mod*')
                calmoddirs = findCalModels()
                ssmoddirs=None
                for d in calmoddirs:
                    lsmodims(d)
        
        # Actual operation, when either the MODEL_DATA column or visibility model header are set
        else:
            if not os.path.isdir(vis):
              #casalog.post(vis + " must be a valid MS unless listmodels is True.",
              #             "SEVERE")
                raise Exception, "%s is not a valid MS" % vis 
                #return False

            myms = mstool()
            myim = imtool()
            if ismms==None: ismms=False
            if type(vis) == str and os.path.isdir(vis):
                n_selected_rows = nselrows(vis, field, spw, observation, timerange, scan, intent, usescratch, ismms)
                # jagonzal: When  usescratch=True, creating the MODEL column only on a sub-set of
                # Sub-MSs causes problems because ms::open requires all the tables in ConCatTable 
                # to have the same description (MODEL data column must exist in all Sub-MSs)
                #
                # This is a bit of an over-doing but it is necessary for the sake of transparency
                #
                # Besides, this is also the same behavior as when running setjy vs a normal MS
                #
                # Finally, This does not affect the normal MS case because nselrows throws an
                # exception when the user enters an invalid data selection, but it works for the 
                # MMS case because every sub-Ms contains a copy of the entire MMS sub-tables
                ##if ((not n_selected_rows) and ((not usescratch) or (standard=="Butler-JPL-Horizons 2012"))) :
                #mylocals = locals()
                #if ((not n_selected_rows) and ((usescratch) or (standard=="Butler-JPL-Horizons 2012"))) :
                if ((not n_selected_rows) and ((ismms) or (standard=="Butler-JPL-Horizons 2012"))) :
                    # jagonzal: Turn this SEVERE into WARNING, as explained above
                    casalog.post("No rows were selected.", "WARNING")
                    #return True
                    return False
                else:
                    if (not n_selected_rows):
                        raise Exception, "No rows were selected. Please check your data selection"
                    myim.open(vis, usescratch=usescratch)

            else:
                raise Exception, 'Visibility data set not found - please verify the name'

            if modimage==None:  # defined as 'hidden' with default '' in the xml
      	                        # but the default value does not seem to set so deal
			        # with it here...
                modimage=''
            if model:
                modimage=model
            elif not model and modimage:
                casalog.post("The modimage parameter is deprecated please use model instead", "WARNING")
            # If modimage is not an absolute path, see if we can find exactly 1 match in the likely places.
            if modimage and modimage[0] != '/':
                cwd = os.path.abspath('.')
                calmoddirs = [cwd]
                calmoddirs += findCalModels(roots=[cwd,
                                           casa['dirs']['data']])
                candidates = []
                for calmoddir in calmoddirs:
                    cand = calmoddir + '/' + modimage
                    if os.path.isdir(cand):
                        candidates.append(cand)
                if not candidates:
                    casalog.post("%s was not found for modimage in %s." %(modimage,
                                 ', '.join(calmoddirs)), 'SEVERE')
                    return False
                elif len(candidates) > 1:
                    casalog.post("More than 1 candidate for modimage was found:",
                         'SEVERE')
                    for c in candidates:
                        casalog.post("\t" + c, 'SEVERE')
                    casalog.post("Please pick 1 and use the absolute path (starting with /).",
                           'SEVERE')
                    return False
                else:
                    modimage = candidates[0]
                    casalog.post("Using %s for modimage." % modimage, 'INFO')

            # Write the parameters to HISTORY before the tool writes anything.
            try:
                param_names = setjy.func_code.co_varnames[:setjy.func_code.co_argcount]
                param_vals = [eval(p) for p in param_names]   
                #retval &= write_history(myms, vis, 'setjy', param_names,
                retval = write_history(myms, vis, 'setjy', param_names,
                                    param_vals, casalog)
            except Exception, instance:
                casalog.post("*** Error \'%s\' updating HISTORY" % (instance),
                         'WARN')

            # Split the process for solar system objects
            # To maintain the behavior of SetJy such that if a flux density is specified
            # we use it rather than the model, we need to check the state of the 
            # input fluxdensity  JSK 10/25/2012
            # TT comment 07/01/2013: some what redundant as fluxdensity is moved to 
            # a subparameter but leave fluxdensity=-1 for backward compatibility
            userFluxDensity = fluxdensity is not None
            if userFluxDensity and isinstance(fluxdensity, list):
                userFluxDensity = fluxdensity[0] > 0.0
            elif userFluxDensity:
                userFluxDensity = fluxdensity > 0.0

            #in mpirun somehow subparameter defaulting does not work properly, 
            #it seems to pick up default defined in "constraint" clause in the task xml instead
            #of the one defined in "param", so userFluxDensity is not reliable to use in here
            # (and somewhat redundant in this case).
            #if standard=="Butler-JPL-Horizons 2012" and not userFluxDensity:
            if standard=="Butler-JPL-Horizons 2012":
                casalog.post("Using Butler-JPL-Horizons 2012")
                ssmoddirs = findCalModels(target='SolarSystemModels',
                          roots=[casa['dirs']['data']],
                          exts=['.im','.ms','tab'])
                if ssmoddirs==set([]):
                     raise Exception, "Missing Tb or fd  models in the data directory"

                setjyutil=ss_setjy_helper(myim,vis,casalog)
                retval=setjyutil.setSolarObjectJy(field=field,spw=spw,scalebychan=scalebychan,
                             timerange=timerange,observation=str(observation), scan=scan, 
                             intent=intent, useephemdir=useephemdir,usescratch=usescratch)
                clnamelist=setjyutil.getclnamelist()
            
            else:
                # Need to branch out the process for fluxscale since the input dictionary may 
                # contains multiple fields. Since fluxdensity parameter is just a vector contains 
                # IQUV flux densities and so need to run im.setjy per field 

                if standard=="fluxscale": 
                    instandard="Perley-Butler 2010"
                    # function to return selected field, spw, etc
                    fieldidused=parse_fluxdict(fluxdict, vis, field, spw, observation, timerange,
                                           scan, intent, usescratch)

                    if len(fieldidused):
                    
                        retval={}
                        for selfld in fieldidused:
                            #selspix=fluxdict[selfld]["spidx"][1]  # setjy only support alpha for now
                            selspix=fluxdict[selfld]["spidx"][1:]  # omit c0 (=log(So))
                            # set all (even if fluxdensity = -1
                            if spw=='':
                                selspw = [] 
                                invalidspw = []
                                for ispw in fluxdict["spwID"].tolist():
                                    # skip spw if fluxd=-1
                                    if fluxdict[selfld][str(ispw)]["fluxd"][0]>-1:
                                        selspw.append(ispw)
                                    else:
                                        invalidspw.append(ispw)
                                if len(invalidspw):
                                    casalog.post("Fluxdict does not contains valid fluxdensity for spw="+
                                                 str(invalidspw)+ 
                                                 ". Model will not set for those spws.", "WARN") 
                            else: # use spw selection
                                selspw = ms.msseltoindex(vis,spw=spw)["spw"].tolist()
                    
                            if fluxdict[selfld]["fitFluxd"]:
                                selfluxd = fluxdict[selfld]["fitFluxd"]
                                selreffreq = fluxdict[selfld]["fitRefFreq"] 
                            else:
                                # use first selected spw's flux density 
                                selfluxd = fluxdict[selfld][str(selspw[0])]['fluxd']
                                # assuming the fluxscale reporting the center freq of a given spw
                                selreffreq=fluxdict["freq"][selspw[0]] 
                            casalog.post("Use fluxdensity=%s, reffreq=%s, spix=%s" %
                                     (selfluxd,selreffreq,selspix)) 
                            curretval=myim.setjy(field=selfld,spw=selspw,modimage=modimage,
                                                 # enable spix in list
                                                 fluxdensity=selfluxd, spix=selspix, reffreq=selreffreq, 
                                                 #fluxdensity=selfluxd, spix=[selspix], reffreq=selreffreq, 
                                                 standard=instandard, scalebychan=scalebychan,
                                                 polindex=polindex, polangle=polangle, rotmeas=rotmeas,
                                                 time=timerange, observation=str(observation), scan=scan, 
                                                 intent=intent, interpolation=interpolation)
                            retval.update(curretval)
                    else:
                        raise Exception, "No field is selected. Check fluxdict and field selection."
                else: 
                    influxdensity=fluxdensity
                    if standard=="manual":
                        instandard="Perley-Butler 2010" # default standard when fluxdensity=-1 or 1
                    else:
                        instandard=standard
                        # From the task, fluxdensity=-1 always for standard!="manual" (but possible to 
                        # for im.setjy to run with both the stanadard and fluxdensity specified.
                        # Until CAS-6463 is fixed, need to catch and override inconsistent parameters. 
                        if userFluxDensity and instandard!='manual':
                            influxdensity=-1
                            #raise Exception, "Use standard=\"manual\" to set the specified fluxdensity."
                            casalog.post("*** fluxdensity > 0 but standard != 'manual' (possibly interaction with globals), override to set fluxdensity=-1.", 'WARN')
                             

                    if spix==[]: # handle the default 
                        spix=0.0
                    # need to modify imager to accept double array for spix
                    retval=myim.setjy(field=field, spw=spw, modimage=modimage, fluxdensity=influxdensity, 
                                      spix=spix, reffreq=reffreq, standard=instandard, scalebychan=scalebychan, 
                                      polindex=polindex, polangle=polangle, rotmeas=rotmeas,
                                      time=timerange, observation=str(observation), scan=scan, intent=intent, 
                                      interpolation=interpolation)

            myim.close()

    # This block should catch errors mainly from the actual operation mode 
    except Exception, instance:
        casalog.post('%s' % instance,'SEVERE')
        #retval=False
	raise instance
        #if not ismms: 
        #    raise Exception, instance
        #else:
        #    pass

    finally:
        if standard=='Butler-JPL-Horizons 2012':
            for cln in clnamelist:
                if deletecomp and os.path.exists(cln) and os.path.isdir(cln):
                    shutil.rmtree(cln,True) 
            if os.path.exists(os.path.basename(vis)+"_tmp_setjyCLfile"):
                shutil.rmtree(os.path.basename(vis)+"_tmp_setjyCLfile")

    return retval


def better_glob(pats):
    """
    Unlike ls, glob.glob('pat1 pat2') does not return  
    the union of matches to pat1 and pat2.  This does.
    """
    retset = set([])
    patlist = pats.split()
    for p in patlist:
        retset.update(glob(p))
    return retset
  

def lsmodims(path, modpat='*', header='Candidate modimages'):
    """
    Does an ls -d of files or directories in path matching modpat.
  
    Header describes what is being listed.
    """
    if os.path.isdir(path):
        if better_glob(path + '/' + modpat):
            print "\n%s (%s) in %s:" % (header, modpat, path)
            #sys.stdout.flush()
            #os.system('cd ' + path + ';ls -d ' + modpat)
            cmd = 'cd ' + path + ';ls -d ' + modpat
            print subprocess.check_output(cmd, shell=True)
        else:
            print "\nNo %s matching '%s' found in %s" % (header.lower(),
                                                   modpat, path)


def findCalModels(target='CalModels',
                  roots=['.', casa['dirs']['data']],
                  #permexcludes = ['.svn', 'regression', 'ephemerides',
                  permexcludes = ['regression', 'ephemerides',
                                  'geodetic', 'gui'],
                  exts=['.ms', '.im', '.tab']):
    """
    Returns a set of directories ending in target that are in the trees of roots.

    Because casa['dirs']['data'] can contain a lot, and CASA tables are
    directories, branches matching permexcludes or exts are excluded for speed.
    """
    retset = set([])
    # exclulde all hidden(.xxx) directories
    regex = re.compile('^\.\S+')
    # extra skip for OSX 
    if sys.platform == "darwin": 
        permexcludes.append('Frameworks')
        permexcludes.append('Library')
        permexcludes.append('lib')
    for root in roots:
      # Do a walk to find target directories in root.
      # 7/5/2011: glob('/export/data_1/casa/gnuactive/data/*/CalModels/*') doesn't work.
      for path, dirs, fnames in os.walk(root, followlinks=True):
          realpath = os.path.realpath(path)
          if not realpath in retset:
              excludes = permexcludes[:]
              for ext in exts:
                  excludes += [d for d in dirs if ext in d]
                  excludes += [m.group(0) for d in dirs for m in [regex.search(d)] if m]
              for d in excludes:
                  if d in dirs:
                      dirs.remove(d)
              if path.split('/')[-1] == target:
              # make path realpath to resolve the issue with duplicated path resulted from symlinks
                  retset.add(realpath)
    return retset             


def nselrows(vis, field='', spw='', obs='', timerange='', scan='', intent='', usescratch=None, ismms=False):

    # modified to use ms.msselect. If no row is selected ms.msselect will
    # raise an exception  - TT 2013.12.13
    retval = 0
    myms = mstool()
    #msselargs = {'vis': vis}
    msselargs = {}
    if field:
        msselargs['field'] = field
    if spw:
        msselargs['spw'] = spw
    if intent:
       msselargs['scanintent'] = intent

  # only applicable for usescratch=T
    if usescratch:
        if obs:
            if not type(obs)==string:
               sobs = str(obs)
            msselargs['observation'] = sobs
        if timerange:
            msselargs['time'] = timerange
        if scan:
            msselargs['scan'] = scan
    else:
        warnstr='Data selection by '
        datasels=[]
        if timerange: datasels.append('timerange')
        if scan: datasels.append('scan') 
        if obs: datasels.append('observation') 
        if len(datasels):
            warnstr+=str(datasels)+' will be ignored for usescartch=False'
            casalog.post(warnstr,'WARN')
 
    # === skip this use ms.msselect instead ====
    # ms.msseltoindex only goes by the subtables - it does NOT check
    # whether the main table has any rows matching the selection.
#    try:
#        selindices = myms.msseltoindex(**msselargs)
#        print "msselargs=",msselargs," selindices=",selindices
#    except Exception, instance:
#        casalog.post('nselrowscore exception: %s' % instance,'SEVERE')
#        raise instance
#    query = []
#    if field:
#        query.append("FIELD_ID in " + str(selindices['field'].tolist()))
#    if spw:
#        query.append("DATA_DESC_ID in " + str(selindices['spw'].tolist()))
#    if obs and usescratch:
#        query.append("OBSERVATION_ID in " + str(selindices['obsids'].tolist()))

    # I don't know why ms.msseltoindex takes a time argument 
    # - It doesn't seem to appear in the output.
    
#    if scan and usescratch:
#        query.append("SCAN_NUMBER in " + str(selindices['scan'].tolist()))

    #if timerange and usescratch:
    #    query.append("TIME in [select TIME where 

    # for intent (OBS_MODE in STATE subtable), need a subquery part...
#    if intent:
#        query.append("STATE_ID in [select from ::STATE where OBS_MODE==pattern(\""+\
#                  intent+"\") giving [ROWID()]]")
#    print "query=",query
#    mytb = tbtool()
#    mytb.open(vis)
    myms = mstool()
    casalog.post(str(msselargs))
    myms.open(vis)

    if (len(msselargs)==0):
        retval = myms.nrow()
        myms.close()
    else:
        try:
#            st = mytb.query(' and '.join(query),style='python')  # Does style matter here?
#            retval = st.nrows()
#            st.close() # needed to clear tablecache? 
#            mytb.close()
            myms.msselect(msselargs)
            retval = myms.nrow(True)
            myms.close()
        except Exception, instance:
            #if ismms:
            #     casalog.post('nselrows: %s' % instance,'WARN')
            #else:
                 # this is probably redundant as the exception will be handle in setjy()
                 #casalog.post('nselrowscore exception: %s' % instance,'SEVERE')
            #     pass
            
            myms.close()
            #if not ismms: 
            #    raise Exception, instance
            raise Exception, instance
            #else:
            #    casalog.post('Proceed as it appears to be dealing with a MMS...','DEBUG')

    return retval

def parse_fluxdict(fluxdict, vis, field='', spw='', observation='', timerange='', scan='', intent='', usescratch=None):
    """
    Parser function for fluxdict (dictionary output from fluxscale) to set
    fluxdensity, spix, and reffreq parameters (as in 'manual' mode)
    """
    # set spix and reffreq if there  

    #(myms,mymsmd) = gentools(['ms','msmd'])
    myms, = gentools(['ms'])

    # dictionary for storing modified (taking AND between the data selection
    # and fluxdict content)
    modmsselargs={}
                    
    msselargs={}
    msselargs['field']=field 
    msselargs['spw']=spw 
    msselargs['scanintent']=intent
    # only applicable for usescratch=T
    if usescratch:
        if observation:
            msselargs['observation'] = observation
        if timerange:
           msselargs['time'] = timerange
        if scan:
           msselargs['scan'] = scan

    try:
        myms.open(vis)
        myms.msselect(msselargs)
        #selindices = myms.msselectedindices()
        msselfldids=myms.range(["FIELD_ID"])['field_id']
    except Exception, instance:
        casalog.post('parse_fluxdict exception: %s' % instance,'SEVERE')
        raise instance
    finally:
        myms.close()

    # check if fluxdict is valid
    if fluxdict=={}:
        raise Exception, "fluxdict is empty"
    else:
        msg=""
        if not fluxdict.has_key("freq"):
             msg+="freq "
        if not fluxdict.has_key("spwID"):
             msg+="spwID "
        if len(msg):
             raise Exception, "Input fluxdict is missing keywords:"+msg

    # select fields only common to the dictionary and field selection
    fieldids=[]
    for ky in fluxdict.keys():
        try:
            int(ky) 
            fieldids.append(ky) # list in string field ids
        except:
            pass
    if not len(fieldids):
        casalog.post('No field ids was found in the dictionary given for fluxdict. Please check the input.', 'SEVERE')
       

    #if len(selindices['field']):
    if len(msselfldids):    
        # also check there is common field id, note field ids in selindices are in numpy.array
        #selfieldids = [fd for fd in fieldids if int(fd) in selindices['field'].tolist()]
        selfieldids = [fd for fd in fieldids if int(fd) in msselfldids]
        if not len(selfieldids):
            raise Exception, "No field was found in fluxdict for the given data selection"
    else:
        selfieldids = fieldids   

    return selfieldids 
