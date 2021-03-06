"""
__JobUpdaterPoller__

Poller module for the JobUpdater, takes care of the
actual updating work.

Created on Apr 16, 2013

@author: dballest
"""

import logging
import threading
import traceback
from WMCore.BossAir.BossAirAPI import BossAirAPI
from WMCore.DAOFactory import DAOFactory
from WMCore.Services.ReqMgr.ReqMgr import ReqMgr
from WMCore.Services.WorkQueue.WorkQueue import WorkQueue
from WMCore.WorkerThreads.BaseWorkerThread import BaseWorkerThread
from WMCore.WMException import WMException
from WMCore.Database.CMSCouch import CouchConflictError
from WMCore.Database.CouchUtils import CouchConnectionError

class JobUpdaterException(WMException):
    """
    _JobUpdaterException_

    A job updater exception-handling class for the JobUpdaterPoller
    """
    pass

class JobUpdaterPoller(BaseWorkerThread):
    """
    _JobUpdaterPoller_

    Poller class for the JobUpdater
    """

    def __init__(self, config):
        """
        __init__
        """
        BaseWorkerThread.__init__(self)
        self.config = config

        self.bossAir = BossAirAPI(config = self.config)
        self.reqmgr2 = ReqMgr(self.config.JobUpdater.reqMgr2Url)
        self.workqueue = WorkQueue(self.config.WorkQueueManager.couchurl,
                                   self.config.WorkQueueManager.dbname)

        myThread = threading.currentThread()

        self.daoFactory = DAOFactory(package = "WMCore.WMBS",
                                     logger = myThread.logger,
                                     dbinterface = myThread.dbi)

        self.listWorkflowsDAO = self.daoFactory(classname = "Workflow.ListForJobUpdater")
        self.updateWorkflowPrioDAO = self.daoFactory(classname = "Workflow.UpdatePriority")
        self.executingJobsDAO = self.daoFactory(classname = "Jobs.GetNumberOfJobsForWorkflowTaskStatus")


    def setup(self, parameters = None):
        """
        _setup_
        """
        pass

    def terminate(self, parameters = None):
        """
        _terminate_

        Terminate gracefully.
        """
        pass

    def algorithm(self, parameters = None):
        """
        _algorithm_
        """
        try:
            logging.info("Synchronizing priorities with ReqMgr...")
            self.synchronizeJobPriority()
            logging.info("Priorities were synchronized, wait until the next cycle")
        except CouchConnectionError, ex:
            msg = "Caught CouchConnectionError exception in JobUpdater\n"
            msg += "transactions postponed until the next polling cycle\n"
            msg += str(ex)
            logging.exception(msg)
        except CouchConflictError, ex:
            msg = "Caught CouchConflictError exception in JobUpdater\n"
            msg += "transactions postponed until the next polling cycle\n"
            msg += str(ex)
            logging.exception(msg)
        except Exception, ex:
            msg = "Caught unexpected exception in JobUpdater\n"
            msg += str(ex)
            msg += str(traceback.format_exc())
            msg += "\n\n"
            logging.error(msg)
            raise JobUpdaterException(msg)
        
    def synchronizeJobPriority(self):
        """
        _synchronizeJobPriority_

        Check WMBS and WorkQueue for active workflows and compare with the
        ReqMgr for priority changes. If a priority change occurs
        then update the job priority in the batch system and
        the elements in the local queue that have not been injected yet.
        """
        # Update the priority of workflows that are not in WMBS and just in local queue
        priorityCache = {}
        workflowsToUpdate = {}
        workflowsToCheck = [x for x in self.workqueue.getAvailableWorkflows()]
        for workflow, priority in workflowsToCheck:
            if workflow not in priorityCache:
                try:
                    priorityCache[workflow] = self.reqmgr2.getRequestByNames(workflow)[workflow]['RequestPriority']
                except Exception, ex:
                    logging.error("Couldn't retrieve the priority of request %s" % workflow)
                    logging.error("Error: %s" % ex)
                    continue
            if priority != priorityCache[workflow]:
                workflowsToUpdate[workflow] = priorityCache[workflow]
        logging.info("Found %d workflows to update in workqueue" % len(workflowsToUpdate))
        for workflow in workflowsToUpdate:
            self.workqueue.updatePriority(workflow, workflowsToUpdate[workflow])

        # Check the workflows in WMBS
        priorityCache = {}
        workflowsToUpdateWMBS = {}
        workflowsToCheck = self.listWorkflowsDAO.execute()
        for workflowEntry in workflowsToCheck:
            workflow = workflowEntry['name']
            if workflow not in priorityCache:
                try:
                    priorityCache[workflow] = self.reqmgr2.getRequestByNames(workflow)[workflow]['RequestPriority']
                except Exception, ex:
                    logging.error("Couldn't retrieve the priority of request %s" % workflow)
                    logging.error("Error: %s" % ex)
                    continue
            requestPriority = priorityCache[workflow]
            if requestPriority != workflowEntry['workflow_priority']:
                # Update the workqueue priority for the Available elements
                self.workqueue.updatePriority(workflow, priorityCache[workflow])
                # Check if there are executing jobs for this particular task
                if self.executingJobsDAO.execute(workflow, workflowEntry['task']) > 0:
                    self.bossAir.updateJobInformation(workflow, workflowEntry['task'],
                                                      requestPriority = priorityCache[workflow],
                                                      taskPriority = workflowEntry['task_priority'])
                workflowsToUpdateWMBS[workflow] = priorityCache[workflow]
        if workflowsToUpdateWMBS:
            logging.info("Updating %d workflows in WMBS." % len(workflowsToUpdateWMBS))
            self.updateWorkflowPrioDAO.execute(workflowsToUpdateWMBS)
