// resize modal content to max windows height
function do_resize() {
    if ($(window).width() < 768) {
        $('#detail_content').height($(window).height() - 270);
        $('#clientTab').tabdrop();
    } else {
        $('#detail_content').height($(window).height() - 220);
    }
}
$(window).resize(do_resize);

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

// grid/list view
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
});

function getDeviceIcon(serial, iconid) {
    var image_url = "https://km.support.apple.com.edgekey.net/kb/securedImage.jsp?configcode="+serial.slice( 8 )+"&size=120x120"
    var $image = $("#"+serial+iconid);
    var $downloadingImage = $("<img>");
    $downloadingImage.load(function(){
        $image.attr("src", $(this).attr("src"));	
    });
    $downloadingImage.attr("src", image_url);   
}

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

//create software list
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
            $(  "#SoftwareView").append('<div class="row"><div class="col-md-12"><div class="alert alert-danger" style="margin-top:20px;">manifest read error!</div></div></div>');
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
    $( "#"+listid ).append( "<li class='list-group-item' id='"+listid+"' style='padding-top: 1px !important; padding-bottom: 1px !important;'><input type='text' class='newElementInput' name='new'></li>" );
}

function loopElement(elements, listid, require_update) {
    //alert(JSON.stringify(catalogData))
    if ($("#"+listid ).length < 1){
        $( "#SoftwareList" ).append( '<div class="section_label"><h4>'+listid.replace("_", " ").replace(/\w\S*/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();})+'</h4></div><div class="list-group list-group-root well" id="'+listid+'"><p class="list-group-item" id="addItem" style="padding-top: 1px !important; padding-bottom: 2px !important;"><input type="text" class="newElementInput" name="newSoftware"></p></div>' );
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

        //item infos
        var display_name = element
        var version = ""
        var icon = element + ".png"

        if (typeof require_update === 'undefined') {
            require_update = ""
        } else {
            additionalClass = "manifestObjects"
        }
        if (typeof catalogData[element] === 'undefined') {
            additionalClass = "list-group-item-danger"
        } else {
            display_name = catalogData[element].display_name
            version = catalogData[element].version
            if (typeof catalogData[element].icon !== 'undefined') {
                var icon = catalogData[element].icon
                alert(icon)
            }
        }

        $( "#"+addTo ).append( "<a href='#' class='list-group-item "+additionalClass+"' id="+itemID+"><img src='"+static_url+"img/GenericPkg.png' width='15' style='margin-top:-3px;' id="+itemID+'_icon'+">  "+display_name+" "+version+" <small class='pull-right'>"+require_update+"</small><span class='label label-default pull-right status'>set</span></a>" );
        $( "#"+itemID ).after('<div class="list-group" style="padding-left:20px;" id="'+listGroupID+'"></div>');
        
        var serial = getSerial();
        getStatus(element, serial, itemID);

        //icon
        var image_url = media_url + icon
        $.get(image_url).done(function() { 
            document.getElementById(itemID+'_icon').src = image_url;
        }).fail(function() { 
            // Image doesn't exist
        })

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

function getStatus(item, serial, id) {
    $.ajax({
        type:"POST",
        async: false,
        url:"/reports/_status",
        data: {item : item, serial: serial},
        dataType: 'json',
        success: function(data){
            $('#'+id).find('.status').text(data);
        }
    }); 
}

function loadStatus() {
    $('.status').each(function(i, obj) {
        //get id
        var id = $(obj).parent().attr('id');

        // item
        var item = id.split('_')
        item.pop()
        item = item.join("_");
    
        //get serial
        var serial = getSerial();

        getStatus(item, serial, id)
    });
}

function getSerial() {
    var serial = window.location.hash
    serial.slice(1)
    return serial.substring(1)
}

//edit software
