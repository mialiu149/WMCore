function cleanConfirmation () {
    var doc = document.getElementById('confirmation');
    doc.innerHTML='';
    doc.className='';
}
function errorMessage(err) {
    // extract X-Error-Detail from server error
    var pat = 'X-Error-Detail:'
    var arr = err.split('\n')
    var msg = "<h3>Server error message</h3>";
    for(var i=0; i<arr.length; i++) {
        if(arr[i].startsWith(pat)) {
           msg += arr[i].replace(pat, '');
        }
    }
    // find out confirmation placeholder and fill it up with appropriate message
    var doc = document.getElementById('confirmation');
    var html = '<div>'+msg+'</div>';
    html += '<div>';
    html += '<button class="btn btn-smaller btn-blue right" onclick="javascript:cleanConfirmation()">Close</button>';
    html += '</div>';
    doc.innerHTML=html;
    doc.className='width-50 tools-alert tools-alert-red confirmation shadow';
}
function ajaxRequestPrototype(path, parameters) {
    // path is an URI binded to certain server method
    // parameters is dict of parameters passed to the server function
    new Ajax.Updater('response', path,
    { method: 'post' ,
      parameters : parameters,
      onCreate: function() {
          var doc = document.getElementById('confirmation');
          doc.innerHTML='Your request has been submitted';
          doc.className='tools-alert tools-alert-blue confirmation fadeout shadow';
      },
      onException: function() {
          var doc = document.getElementById('confirmation');
          doc.innerHTML='ERROR! Your request has been failed';
          doc.className='tools-alert tools-alert-red confirmation fadeout shadow';
          setTimeout(cleanConfirmation, 5000);
      },
      onComplete : function(response) {
          var doc = document.getElementById('confirmation');
          if  (response.status==200 || response.status==201) {
              doc.innerHTML='SUCCESS! Your request has been processed with status '+response.status;
              doc.className='tools-alert tools-alert-green confirmation fadeout shadow';
              setTimeout(cleanConfirmation, 5000);
          } else {
              doc.innerHTML='WARNING! Your request has been processed with status '+response.status;
              doc.className='tools-alert tools-alert-yellow confirmation fadeout shadow';
              var headers = response.getAllResponseHeaders();
              errorMessage(headers);
          }
      }
    });
}
function ajaxRequest(path, parameters, verb) {
    // path is an URI binded to certain server method
    // parameters is dict of parameters passed to the server function
    var request = $.ajax({
        url: path,
        data: parameters,
        type: verb || 'POST',
        // headers: {"X-HTTP-Method-Override": "PUT"}, // X-HTTP-Method-Override set to PUT.
        dataType: "json",
        cache: false,
        beforeSend: function() {
            var doc = document.getElementById('confirmation');
            doc.innerHTML='Your request has been submitted';
            doc.className='tools-alert tools-alert-blue confirmation fadeout shadow';
        }
    });
    request.done(function(data) {
        $('response').html(data);
    });
    request.fail(function(xhr, msg, err) {
        var doc = document.getElementById('confirmation');
        doc.innerHTML='ERROR! Your request has been failed with status code '+xhr.status+' and '+msg+' '+err;
        doc.className='tools-alert tools-alert-red confirmation fadeout shadow';
        var headers = xhr.getAllResponseHeaders();
        errorMessage(headers);
    });
    request.always(function (arg1, msg, arg2) {
        // from jQuery docs: http://api.jquery.com/jquery.ajax/
        // for successful events the input parameters are (data, msg, xhr)
        // for failed events the input parameters are (xhr, msg, err)
        var doc = document.getElementById('confirmation');
        if  (arg2.status==200 || arg2.status==201 || msg=='success') {
            doc.innerHTML='SUCCESS! Your request has been processed with code '+arg2.status;
            doc.className='tools-alert tools-alert-green confirmation fadeout shadow';
            setTimeout(cleanConfirmation, 5000);
        } else {
            doc.innerHTML='WARNING! Your request has been processed with status code '+arg1.status+' and '+msg+' '+arg2;
            doc.className='tools-alert tools-alert-yellow confirmation fadeout shadow';
            var headers = xhr.getAllResponseHeaders();
            errorMessage(headers);
        }
    });
}
