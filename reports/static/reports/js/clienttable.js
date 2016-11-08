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
    $('#detail_content').height($(window).height() - 220);
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
                loopElement(JSON.parse(data).managed_installs, "managed_installs"),
                loopElement(JSON.parse(data).managed_uninstalls, "managed_uninstalls"),
                loopElement(JSON.parse(data).optional_installs, "optional_installs"),
                loopManifests(JSON.parse(data).included_manifests),
            );
        },
        error: function(jqXHR, textStatus, errorThrown) {
            //display error when manifest is not readable
            $("#SoftwareView").empty();
            $("#SoftwareView").append('<div class="row"><div class="col-md-12"><div class="alert alert-danger" style="margin-top:20px;">manifest read error!</div></div></div>');
        },
        dataType: 'html'
    });
}

function getIncludedManifest(manifest) {
    $.ajax({
        method: 'GET',
        url: "/reports/_getManifest/"+manifest,
        timeout: 10000,
        cache: false,
        success: function(data) {
            loopElement(JSON.parse(data).managed_installs, "managed_installs", manifest),
            loopElement(JSON.parse(data).managed_uninstalls, "managed_uninstalls", manifest),
            loopElement(JSON.parse(data).optional_installs, "optional_installs", manifest),
            loopManifests(JSON.parse(data).included_manifests)
        },
        error: function() {
            $("#included_manifests_"+manifest).addClass("list-group-item-danger");
        },
        dataType: 'html'
    });
}

function createListElements(elements, listid) {
    //alert(JSON.stringify(catalogData))
    $.each(elements, function( index, value ) {
        //alert( index + ": " + value );
        $( "#"+listid ).append( "<li class='list-group-item' id='"+listid+"_"+value+"'>"+value+"</li>" );
    });
}

function loopElement(elements, listid, require_update) {
    //alert(JSON.stringify(catalogData))
    if ($("#"+listid ).length < 1){
        $( "#SoftwareList" ).append( '<div class="section_label"><h4>'+listid.replace("_", " ").replace(/\w\S*/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();})+'</h4></div><div class="list-group list-group-root well" id="'+listid+'"></div>' );
    }
    $.each(elements, function( index, value ) {
        //alert( index + ": " + value );
        createSoftwareElement(value, listid, require_update);
    });
}

var softwareElementCount = 0
function createSoftwareElement(element, addTo, require_update) {
        var itemID = element + "_" + softwareElementCount
        var listGroupID = element + "_" + softwareElementCount + "_" + addTo
        var additionalClass = ""
        if (typeof require_update === 'undefined') {
            require_update = ""
        }
        if (typeof catalogData[element] === 'undefined') {
            var display_name = element
            var version = ""
            additionalClass = "list-group-item-danger"
        } else {
            var display_name = catalogData[element].display_name
            var version = catalogData[element].version
        }

        $( "#"+addTo ).append( "<a href='#' class='list-group-item "+additionalClass+"' id="+itemID+">"+display_name+" "+version+" <small class='pull-right'>"+require_update+"</small></a>" );
        $( "#"+itemID ).append('<div class="list-group" id="'+listGroupID+'"></div>');

        if (typeof catalogData[element] !== 'undefined' && typeof catalogData[element].requires !== 'undefined') {
            $.each(catalogData[element].requires, function( index, element_requires ) {
                createSoftwareElement(element_requires, listGroupID, catalogData[element].display_name+" requires");
            });
        }

       if (typeof catalogData[element] !== 'undefined' && typeof catalogData[element].updates !== 'undefined') {
           $.each(catalogData[element].updates, function( index, element_updates ) {
               createSoftwareElement(element_updates, listGroupID, "update for "+catalogData[element].display_name);
           });
        }
      softwareElementCount++;
}

function loopManifests(manifests) {
    $.each(manifests, function( index, manifest ) {
        //alert(manifest);
        getIncludedManifest(manifest);
    });
}