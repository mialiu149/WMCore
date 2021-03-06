#!/usr/bin/env python
import os
import unittest
import shutil
import time

from WMCore.Wrappers import JsonWrapper
from WMCore.Services.RequestDB.RequestDBReader import RequestDBReader
from WMCore.Services.RequestDB.RequestDBWriter import RequestDBWriter
from WMQuality.TestInitCouchApp import TestInitCouchApp
from WMCore_t.Services_t.WMStats_t.WMStatsDocGenerator import generate_reqmgr_schema
from WMCore.WMSpec.WMWorkload import newWorkload
from WMCore.Services.WMStats.DataStruct.RequestInfoCollection import RequestInfoCollection
class RequestDBTest(unittest.TestCase):
    """
    """
    def setUp(self):
        """
        _setUp_
        """
        self.schema = []
        self.couchApps = ["ReqMgr"]
        self.testInit = TestInitCouchApp('RequestDBServiceTest')
        self.testInit.setLogging()
        self.testInit.setDatabaseConnection()
        self.testInit.setSchema(customModules = self.schema,
                                useDefault = False)
        dbName = 'requsetdb_t'
        self.testInit.setupCouch(dbName, *self.couchApps)
        reqDBURL = "%s/%s" % (self.testInit.couchUrl, dbName)
        self.requestWriter = RequestDBWriter(reqDBURL)
        self.requestReader = RequestDBReader(reqDBURL)
        self.requestWriter.defaultStale = {}
        self.requestReader.defaultStale = {}
        return

    def tearDown(self):
        """
        _tearDown_

        Drop all the WMBS tables.
        """
        self.testInit.tearDownCouch()

    def testRequestDBWriter(self):
        # test getWork
        schema = generate_reqmgr_schema(3)
        result =  self.requestWriter.insertGenericRequest(schema[0])

        self.assertEquals(len(result), 1, 'insert fail');
        
        self.assertEquals(self.requestWriter.updateRequestStatus(schema[0]['RequestName'], "failed"), 'OK', 'update fail')
        self.assertEquals(self.requestWriter.updateRequestStatus("not_exist_schema", "assigned"),
                          'Error: document not found')
        result = self.requestWriter.updateRequestProperty(schema[0]['RequestName'], 
                                                                   {'Teams': ['teamA']})
        self.assertEquals(self.requestWriter.updateRequestProperty(schema[0]['RequestName'], 
                                                                   {'Teams': ['teamA']}), 'OK', 'update fail')
        self.assertEquals(self.requestWriter.updateRequestProperty("not_exist_schema", {'Teams': 'teamA'}),
                          'Error: document not found')
        
        result = self.requestReader.getRequestByNames([schema[0]['RequestName']])
        self.assertEquals(len(result), 1, "should be 1")
        result = self.requestReader.getRequestByStatus(["failed"], False, 1)
        self.assertEquals(len(result), 1, "should be 1")
        
        
        result =  self.requestWriter.insertGenericRequest(schema[1])
        time.sleep(2)
        result =  self.requestWriter.insertGenericRequest(schema[2])
        endTime = int(time.time()) - 1
        result = self.requestReader.getRequestByStatusAndStartTime("new", False, endTime)
        self.assertEquals(len(result), 1, "should be 1")
        endTime = int(time.time()) + 1
        result = self.requestReader.getRequestByStatusAndStartTime("new", False, endTime)
        self.assertEquals(len(result), 2, "should be 2")
      

if __name__ == '__main__':

    unittest.main()