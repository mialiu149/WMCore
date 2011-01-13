#!/usr/bin/env python
"""
_CheckIn_

CheckIn process for making a request

"""




import logging
import WMCore.RequestManager.RequestDB.Interface.Request.MakeRequest as MakeRequest
import WMCore.RequestManager.RequestDB.Interface.Admin.RequestManagement as RequestAdmin


def raiseCheckInError(request, ex, msg):
    msg +='\n' + str(ex)
    msg += "\nUnable to check in new request"
    RequestAdmin.deleteRequest(request['RequestID'])
    raise RuntimeError, msg


def checkIn(request):
    """
    _CheckIn_

    Check in of a request manager

    Given a new request, check it in to the DB and add the
    appropriate IDs.
    """
    #  //
    # // First try and register the request in the DB
    #//
    try:
        reqId = MakeRequest.createRequest(
        request['Requestor'],
        request['Group'],
        request['RequestName'],
        request['RequestType'],
        request['RequestWorkflow'],
    )
    except Exception, ex:
        msg = "Error creating new request:\n"
        msg += str(ex)
        raise RuntimeError, msg
    request['RequestID'] = reqId
    logging.info("Request %s created with request id %s" % (
        request['RequestName'], request['RequestID'])
                 )

    #  //
    # // add metadata about the request
    #//
    try:
        if request['InputDatasetTypes'] != {}:
            for ds, dsType in request['InputDatasetTypes'].items():
                MakeRequest.associateInputDataset(
                    request['RequestName'], ds, dsType)
        elif isinstance(request['InputDatasets'], list):
            for ds in request['InputDatasets']:
                MakeRequest.associateInputDataset(request['RequestName'], ds)
        else:
            MakeRequest.associateInputDataset(request['RequestName'], request['InputDatasets'])
    except Exception, ex:
        raiseCheckInError(request, ex, "Unable to Associate input datasets to request")
    try:
        for ds in request['OutputDatasets']:
            MakeRequest.associateOutputDataset(request['RequestName'], ds)
    except Exception, ex:
        raiseCheckInError(request, ex, "Unable to Associate output datasets to request")

    try:
        for sw in request['SoftwareVersions']:
            MakeRequest.associateSoftware(
                request['RequestName'], sw)
    except Exception, ex:
        raiseCheckInError(request, ex, "Unable to associate software for this request")

    if request["RequestSizeEvents"] != None:
        MakeRequest.updateRequestSize(request['RequestName'],
                                      request["RequestSizeEvents"],
                                      request.get("RequestSizeFiles", 0)
                                      )


    return

