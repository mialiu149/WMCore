#!/usr/bin/env python

import os
import sys

from WMCore.WMInit import WMInit
from WMCore.Configuration import loadConfigurationFile

from WMCore.WMBS.File import File
from WMCore.WMBS.Fileset import Fileset
from WMCore.WMBS.Subscription import Subscription
from WMCore.WMBS.Workflow import Workflow

from WMCore.DataStructs.Run import Run

from WMCore.WMSpec.StdSpecs.ReReco import rerecoWorkload
from DBSAPI.dbsApi import DbsApi

if not os.environ.has_key("WMAGENT_CONFIG"):
    print "Please set WMAGENT_CONFIG to point at your WMAgent configuration."
    sys.exit(0)

wmAgentConfig = loadConfigurationFile(os.environ["WMAGENT_CONFIG"])

if not hasattr(wmAgentConfig, "CoreDatabase"):
    print "Your config is missing the CoreDatabase section."

socketLoc = getattr(wmAgentConfig.CoreDatabase, "socket", None)
connectUrl = getattr(wmAgentConfig.CoreDatabase, "connectUrl", None)
(dialect, junk) = connectUrl.split(":", 1)

myWMInit = WMInit()
myWMInit.setDatabaseConnection(dbConfig = connectUrl, dialect = dialect,
                               socketLoc = socketLoc)


arguments = {
    "OutputTiers" : ["RECO", "ALCA", "AOD"],
    "AcquisitionEra" : "WMAgentCommissioining10",
    "GlobalTag" :"GR09_R_34X_V5::All",
    "LFNCategory" : "/store/backfill/2",
    "TemporaryLFNCategory": "/store/backfill/2/unmerged",
    "ProcessingVersion" : "v1",
    "Scenario" : "cosmics",
    "CMSSWVersion" : "CMSSW_3_4_2_patch1",
    "InputDatasets" : "/MinimumBias/BeamCommissioning09-v1/RAW",
    "Emulate" : False,
    }

workload = rerecoWorkload("Tier1ReReco", arguments)
workload.save("rereco.pkl")

def doIndent(level):
    myStr = ""
    while level > 0:
        myStr = myStr + " "
        level -= 1

    return myStr

def injectTaskIntoWMBS(specUrl, task, inputFileset, indent = 0):
    """
    _injectTaskIntoWMBS_

    """
    print "%sinjecting %s" % (doIndent(indent), task.getPathName())
    print "%s  input fileset: %s" % (doIndent(indent), inputFileset.name)

    myWorkflow = Workflow(spec = specUrl, owner = "sfoulkes@fnal.gov",
                          name = task.getPathName(), task = task.getPathName())
    myWorkflow.create()
    mySubscription = Subscription(fileset = inputFileset, workflow = myWorkflow,
                                  split_algo = task.jobSplittingAlgorithm(),
                                  type = task.taskType())
    mySubscription.create()

    outputModules =  task.getOutputModulesForStep(task.getTopStepName())
    for outputModuleName in outputModules.listSections_():
        print "%s  configuring output module: %s" % (doIndent(indent), outputModuleName)
        if task.taskType() == "Merge":
            outputFilesetName = "%s/merged-%s" % (task.getPathName(),
                                                  outputModuleName)
        else:
            outputFilesetName = "%s/unmerged-%s" % (task.getPathName(),
                                                    outputModuleName)

        print "%s    output fileset: %s" % (doIndent(indent), outputFilesetName)
        outputFileset = Fileset(name = outputFilesetName)
        outputFileset.create()

        myWorkflow.addOutput(outputModuleName, outputFileset)

        # See if any other steps run over this output.
        print "%s    searching for child tasks..." % (doIndent(indent))
        for childTask in task.childTaskIterator():
            if childTask.data.input.outputModule == outputModuleName:
                injectTaskIntoWMBS(specUrl, childTask, outputFileset, indent + 4)                

def injectFilesFromDBS(inputFileset, datasetPath):
    """
    _injectFilesFromDBS_

    """
    print "injecting files from %s into %s, please wait..." % (datasetPath, inputFileset.name)
    args={}
    args['url']='http://cmsdbsprod.cern.ch/cms_dbs_prod_global/servlet/DBSServlet'
    args['version']='DBS_2_0_9'
    args['mode']='GET'
    dbsApi = DbsApi(args)
    dbsResults = dbsApi.listFiles(path = datasetPath, retriveList = ["retrive_lumi", "retrive_run"])
    print "  found %d files, inserting into wmbs..." % (len(dbsResults))

    for dbsResult in dbsResults:
        myFile = File(lfn = dbsResult["LogicalFileName"], size = dbsResult["FileSize"],
                      events = dbsResult["NumberOfEvents"], checksums = {"cksum": dbsResult["Checksum"]},
                      locations = "cmssrm.fnal.gov")
        myRun = Run(runNumber = dbsResult["LumiList"][0]["RunNumber"])
        for lumi in dbsResult["LumiList"]:
            myRun.lumis.append(lumi["LumiSectionNumber"])
        myFile.addRun(myRun)
        myFile.create()

    return

for workloadTask in workload.taskIterator():
    inputFileset = Fileset(name = workloadTask.getPathName())
    inputFileset.create()

    inputDataset = workloadTask.inputDataset()
    inputDatasetPath = "/%s/%s/%s" % (inputDataset.primary,
                                      inputDataset.processed,
                                      inputDataset.tier)
    injectFilesFromDBS(inputFileset, inputDatasetPath)

    injectTaskIntoWMBS("/home/sfoulkes/etc/rereco.pkl", workloadTask,
                       inputFileset)





