window.confirm = function(message, cb) {
    $("#confirmationModal .modal-body").html(message);
    $("#confirmationModal").modal('show');
    $("#confirmYes").unbind('click').on("click", function () {
        cb(true);
    });
    cb(false);
};


// using jQuery
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    timeout:10000,
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});


// search field
$(document).on('keyup','#listSearchField', function () {
	filter = $(this).val();
	$("#deviceList li").each(function() {
    if ($(this).text().search(new RegExp(filter, "i")) > -1) {
      $(this).show();
    } else {
      $(this).hide();
    }
  });
});


$(document).ready(function() {
    getAppGroups();
});


function getAppGroups() {
    var machineURL = '/api/mdm/app_groups';
    $.ajax({
        method: 'GET',
        url: machineURL,
        success: function(data) {
            var html = '<div class="col-lg-12"><ul class="list-group"><li class="list-group-item">no data</li></ul></div>';
            if (data) {
                var html = '<div class="col-lg-12">';
                html += '<ul class="list-group">';
                $.each(data['data'], function(key, value) {
                    html += '<li class="list-group-item" style="text-transform: capitalize;"><img src="data:image/png;base64,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" width="15" style="margin-top:-3px;"> <b>'+value['attributes']['name']+'</b> <span class="badge">'+value['id']+'</span></li>';
                });
                html += '</ul>'
                html += '</div>'
            }
            $('#vpp').html(html);
        },
        error: function(jqXHR, textStatus, errorThrown) {
            var html = '<div class="col-lg-12"><ul><li class="list-group-item">no data</li></ul></div>';
            $('#vpp').html(html);
        }
    });
}


function pushApps(groupID) {
    var url = '/api/mdm/app_groups/'+groupID + "/push_apps" ;
    $("#process_progress").modal("show");
    $.ajax({
        method: 'POST',
        url: url,
        success: function(data) {
            $("#process_progress").modal("hide");
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $("#errorModalTitleText").text("MDM post error");
            try {
                var json_data = $.parseJSON(jqXHR.responseText)
                if (json_data['result'] == 'failed') {
                    $("#errorModalDetailText").text(json_data['detail']);
                    $("#process_progress").modal("hide");
                    $("#errorModal").modal("show");
                    return;
                }
            } catch(err) {
                // do nothing
            }
            $("#errorModalDetailText").text(errorThrown);
            $("#process_progress").modal("hide");
            $("#errorModal").modal("show");
        }
    });
}


function geticon(appid) {
    var url = 'https://itunes.apple.com/lookup?id='+appid+"&entity=software";
    $.ajax({
        method: 'GET',
        url: url,
        dataType: "json",
        success: function(data) {
            console.log(data["results"])
            $('#img_'+appid).attr("src", data["results"][0]["artworkUrl60"]);
        },
        error: function(jqXHR, textStatus, errorThrown) {
        }
    });
}