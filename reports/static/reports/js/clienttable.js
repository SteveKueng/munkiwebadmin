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
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

// resize modal content to max windows height
function do_resize() {
    $('#detail_content').height($(window).height() - 340);
}

$(window).resize(do_resize);

$(document).on('click','.grid_list', function (e) {
    $(".grid_list").removeClass('active')
	    if($(this).hasClass('list')) {
	        $('#deviceList').removeClass('grid').addClass('list');
          $(this).addClass('active');
	    }
	    else if ($(this).hasClass('grid')) {
	        $('#deviceList').removeClass('list').addClass('grid');
          $(this).addClass('active');
	    }
});

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

// reset url on modal close
$(document).on('hide.bs.modal','#computerDetails', function () {
  // check for unsaved changes
  if ($('#save_and_cancel').length && !$('#save_and_cancel').hasClass('hidden')) {
      $('#computerDetails').data('bs.modal').isShown = false;
      $("#saveOrCancelConfirmationModal").modal("show");
      event.preventDefault();
      return;
  } else {
    $('#computerDetails').data('bs.modal').isShown = true;
    window.location.hash = '';
    current_pathname = "";
  }
});


$(document).ready(function() {
    hash = window.location.hash;
    if (hash.length > 1) {
        getComputerItem(hash.slice(1));
    }

    //$('#listSearchField').focus();
    // When a modal is shown, and it contains an <input>, make sure it's
    // selected when the modal is shown.
    $(document).on('shown.bs.modal', '.modal', function(event){
        $(event.currentTarget).find('input').select();
    });

    $(window).on('hashchange', function() {
        hash = window.location.hash;
        if (hash.length > 1) {
            if (hash.slice(1) != current_pathname) {
                getComputerItem(hash.slice(1));
                
            }
        }
    });

} );

var current_pathname = "";
function getComputerItem(pathname) {
    if ($('#save_and_cancel').length && !$('#save_and_cancel').hasClass('hidden')) {
        requested_pathname = pathname;
        $("#saveOrCancelConfirmationModal").modal("show");
        event.preventDefault();
        return;
    }
		$("#loadingModal").modal("show");
    var manifestItemURL = '/reports/' + pathname;
    $.ajax({
        method: 'GET',
        url: manifestItemURL,
        timeout: 10000,
        cache: false,
        success: function(data) {
            $('#computer_detail').html(data);
            getManifest(pathname);
          	//  hideSaveOrCancelBtns();
          	//  detectUnsavedChanges();
            current_pathname = pathname;
            requested_pathname = "";

            window.history.replaceState({'computer_detail': data}, manifestItemURL, '/reports/');
            window.location.hash = pathname;

            if (!$('#computerDetails').hasClass('in')){
                do_resize();              
                $("#computerDetails").modal("show");
            }
            $("#loadingModal").modal("hide");
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $('#computer_detail').html("")
            current_pathname = "";
            $("#errorModalTitleText").text("computer read error");
             try {
                 var json_data = $.parseJSON(jqXHR.responseText)
                 if (json_data['result'] == 'failed') {
                     $("#errorModalDetailText").text(json_data['detail']);
                     $("#errorModal").modal("show");
                     return;
                 }
             } catch(err) {
                 // do nothing
             }
             $("#errorModalDetailText").text(errorThrown);
             $("#errorModal").modal("show");
						 $("#loadingModal").modal("hide");
        },
        dataType: 'html'
    })
}

function cancelEdit() {
    //$('#cancelEditConfirmationModal').modal('hide');
    $("#computerDetails").modal("hide");
    //$('.modal-backdrop').remove();
    hideSaveOrCancelBtns();
    //getManifestItem(current_pathname);
}

var catalogData = ""
function getSoftwareList(catalogList) {
    $.ajax({
        type:"POST",
        async: false,
        url:"/reports/_catalogJson",
        data: {catalogList},
        dataType: 'json',
        success: function(data){
            catalogData = data;
        }
    }); 
}

function getManifest(manifest) {
    $.ajax({
        method: 'GET',
        url: "/reports/_getManifest/"+manifest,
        timeout: 10000,
        cache: false,
        success: function(data) {
            $.when(getSoftwareList(JSON.parse(data).catalogs)).done(
                createListElements(JSON.parse(data).included_manifests, "included_manifests"),
                createListElements(JSON.parse(data).catalogs, "catalogs"),
                createSoftwareElements(JSON.parse(data).managed_installs),
                createSoftwareElements(JSON.parse(data).managed_uninstalls),

            )
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $("#errorModalTitleText").text("manifest read error");
             try {
                 var json_data = $.parseJSON(jqXHR.responseText)
                 if (json_data['result'] == 'failed') {
                     $("#errorModalDetailText").text(json_data['detail']);
                     $("#errorModal").modal("show");
                     return;
                 }
             } catch(err) {
                 // do nothing
             }
             $("#errorModalDetailText").text(errorThrown);
             $("#errorModal").modal("show");
        },
        dataType: 'html'
    });
}

function createSoftwareElements(elements) {
    //alert(JSON.stringify(catalogData))
    $.each(elements, function( index, value ) {
        //alert( index + ": " + value );
        $( "#SoftwareList" ).append( "<a href='#' class='list-group-item' id="+value+">"+catalogData[value].display_name+" "+catalogData[value].version+"</a>" );
        $( "#"+value ).append('<div class="list-group" id="'+value+'_group"></div>');
        if (typeof catalogData[value].requires !== 'undefined') {
            $.each(catalogData[value].requires, function( index, value_requires ) {
                $( "#"+value+"_group" ).append( "<a href='#' class='list-group-item' id="+value_requires+'_requires'+">"+catalogData[value_requires].display_name+" "+catalogData[value_requires].version+" "+catalogData[value].display_name+" requires</a>" );
            });
        }
        if (typeof catalogData[value].updates !== 'undefined') {
            $.each(catalogData[value].updates, function( index, value_updates ) {
                $( "#"+value+"_group" ).append( "<a href='#' class='list-group-item' id="+value_updates+'_requires'+">"+catalogData[value_updates].display_name+" "+catalogData[value_updates].version+" update for "+catalogData[value].display_name+"</a>" );
            });
        }
        
    });
}

function createListElements(elements, listid) {
    //alert(JSON.stringify(catalogData))
    $.each(elements, function( index, value ) {
        //alert( index + ": " + value );
        $( "#"+listid ).append( "<li class='list-group-item'>"+value+"</li>" );
    });
}
