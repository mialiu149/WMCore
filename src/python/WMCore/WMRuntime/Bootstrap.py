#!/usr/bin/env python
"""
_TaskSpace_

Frontend module for setting up TaskSpace & StepSpace areas within a job.

"""
import inspect
import pickle

from WMCore.WMException import WMException
from WMCore.WMRuntime import TaskSpace
from WMCore.WMRuntime import StepSpace

from WMCore.DataStructs.JobPackage import JobPackage
from WMCore.WMSpec.WMWorkload import WMWorkloadHelper



class BootstrapException(WMException):
    #TODO: make awesome
    pass



def establishTaskSpace(**args):
    """
    _establishTaskSpace_

    Bootstrap method for the execution dir for a WMTask

    """
    return TaskSpace.TaskSpace(**args)

def establishStepSpace(**args):
    """
    _establishStepSpace_

    Bootstrap method for the execution dir of a WMStep within a WMTask

    """
    return StepSpace.StepSpace(**args)

def locateWMSandbox():
    """
    _locateWMSandbox_

    At runtime, the WMSandbox module should be defined and available
    on the PYTHONPATH.

    Look up the location of the module via import so that the
    pickled files in the sandbox can be loaded

    """
    try:
        import WMSandbox
    except ImportError, ex:
        msg = "Error importing WMSandbox module"
        msg += str(ex)
        raise BootstrapException(msg)

    wmsandboxLoc = inspect.getsourcefile(WMSandbox)
    wmsandboxLoc = wmsandboxLoc.replace("__init__.py", "")
    return wmsandboxLoc

def loadJobDefinition():
    """
    _loadJobDefinition_

    Load the job package and pull out the indexed job, return
    WMBS Job instance

    """
    sandboxLoc = locateWMSandbox()
    package = JobPackage()
    packageLoc = "%s/%s" % (sandboxLoc, "JobPackage.pcl")
    try:
        package.load(packageLoc)
    except Exception, ex:
        msg = "Failed to load JobPackage:%s\n" % packageLoc
        raise BootstrapException, msg

    try:
        import WMSandbox.JobIndex
    except ImportError, ex:
        msg = "Failed to import WMSandbox.JobIndex module\n"
        msg += str(ex)
        raise BootstrapException, msg

    index = WMSandbox.JobIndex.jobIndex

    try:
        job = package[index]
    except Exception, ex:
        msg = "Failed to extract Job"
        raise BootstrapException, msg

    return job

def loadWorkload():
    """
    _loadWorkload_

    Load the Workload from the WMSandbox Area

    """
    sandboxLoc = locateWMSandbox()
    workloadPcl = "%s/WMWorkload.pcl" % sandboxLoc
    handle = open(workloadPcl, 'r')
    wmWorkload = pickle.load(handle)
    handle.close()

    return WMWorkloadHelper(wmWorkload)




def loadTask(job):
    """
    _loadTask_

    load the Workload, and then lookup the task in the workload
    required by the job

    """
    workload = loadWorkload()
    try:
        task = workload.getTaskByPath(job['task'])
    except Exception, ex:
        msg = "Error looking up task %s\n" % job['task']
        msg += str(ex)
        raise BootstrapError, msg
    if task == None:
        msg = "Unable to look up task %s from Workload\n" % job['task']
        msg += "Task name not matched"
        raise BootstrapError, msg
    return task

