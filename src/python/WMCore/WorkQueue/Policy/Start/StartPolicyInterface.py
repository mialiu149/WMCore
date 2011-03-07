#!/usr/bin/env python
"""
WorkQueue SplitPolicyInterface

"""
__all__ = []

import types

from WMCore.WorkQueue.Policy.PolicyInterface import PolicyInterface
from WMCore.WorkQueue.DataStructs.WorkQueueElement import WorkQueueElement
#from WMCore.WorkQueue.DataStructs.CouchWorkQueueElement import CouchWorkQueueElement as WorkQueueElement
from WMCore.WMException import WMException
from WMCore.WorkQueue.WorkQueueExceptions import WorkQueueWMSpecError, WorkQueueNoWorkError
from DBSAPI.dbsApiException import DbsConfigurationError

class StartPolicyInterface(PolicyInterface):
    """Interface for start policies"""
    def __init__(self, **args):
        PolicyInterface.__init__(self, **args)
        self.workQueueElements = []
        self.wmspec = None
        self.team = None
        self.initialTask = None
        self.splitParams = None
        self.dbs_pool = {}
        self.data = {}
        self.lumi = None
        self.couchdb = None

    def split(self):
        """Apply policy to spec"""
        raise NotImplementedError

    def validate(self):
        """Check params and spec are appropriate for the policy"""
        raise NotImplementedError

    def validateCommon(self):
        """Common validation stuff"""
        if self.initialTask.siteWhitelist() and type(self.initialTask.siteWhitelist()) in types.StringTypes:
            error = WorkQueueWMSpecError(self.wmspec, 'Invalid site whitelist: Must be tuple/list but is %s' % type(self.initialTask.siteWhitelist()))
            raise error

        if self.initialTask.siteBlacklist() and type(self.initialTask.siteBlacklist()) in types.StringTypes:
            error = WorkQueueWMSpecError(self.wmspec, 'Invalid site blacklist: Must be tuple/list but is %s' % type(self.initialTask.siteBlacklist()))
            raise error

    def newQueueElement(self, **args):
        args.setdefault('Status', 'Available')
        args.setdefault('WMSpec', self.wmspec)
        args.setdefault('Task', self.initialTask)
        args.setdefault('RequestName', self.wmspec.name())
        args.setdefault('TaskName', self.initialTask.name())
        args.setdefault('Task', self.initialTask.name())
        args.setdefault('Dbs', self.initialTask.dbsUrl())
        args.setdefault('SiteWhitelist', self.initialTask.siteWhitelist())
        args.setdefault('SiteBlacklist', self.initialTask.siteBlacklist())
        args.setdefault('EndPolicy', self.wmspec.endPolicyParameters())
        self.workQueueElements.append(WorkQueueElement(**args))

    def __call__(self, wmspec, task, data = None, mask = None, team = None):
        self.wmspec = wmspec
        self.splitParams = self.wmspec.data.policies.start
        self.initialTask = task
        if data:
            self.data = data
        self.mask = mask
        self.validate()
        try:
            self.split()
        except DbsConfigurationError, ex:
            # A dbs configuration error implies the spec is invalid
            error = WorkQueueWMSpecError(self.wmspec, "DBS config error: %s" % str(ex))
            raise error
        
        if not self.workQueueElements:
            msg = """data: %s, mask: %s.""" % (str(task.inputDataset().pythonise_()), str(mask))
            error = WorkQueueNoWorkError(self.wmspec, msg)
            raise error
        return self.workQueueElements

    def dbs(self):
        """Get DBSReader"""
        from WMCore.WorkQueue.WorkQueueUtils import get_dbs
        dbs_url = self.initialTask.dbsUrl()
        return get_dbs(dbs_url)
